from calyx.builder import Builder, while_, if_, const, invoke
from calyx import py_ast as ast

MAX_CONTENTS = 16384
MAX_RUCKSACKS = 512
ITEM_WIDTH = 6
LENGTH_WIDTH = 8
SCORE_WIDTH = 32

RUCKSACK_IDX_WIDTH = (MAX_RUCKSACKS - 1).bit_length()
CONTENTS_IDX_WIDTH = (MAX_CONTENTS - 1).bit_length()


def build_mem(comp, name, width, size, is_external=True, is_ref=False):
    idx_width = (size - 1).bit_length() if size > 1 else 1
    comp.prog.import_("primitives/memories.futil")
    inst = ast.CompInst("seq_mem_d1", [width, size, idx_width])
    return comp.cell(name, inst, is_external=is_external, is_ref=is_ref)


def build(rucksacks_per_team=1):
    """Build the `main` component for AOC day 3.

    `rucksacks_per_team` dictates the number of different rucksacks
    (compartment pairs) we are looking for conflicts among. If this is
    1, then we look at *compartments* within a single rucksack: i.e., we
    chop each rucksack contents in half and treat them as separate.
    """
    prog = Builder()
    main = prog.component("main")

    # Inputs & outputs.
    contents = build_mem(main, "contents", ITEM_WIDTH, MAX_CONTENTS)
    lengths = build_mem(main, "lengths", LENGTH_WIDTH, MAX_RUCKSACKS)
    rucksacks = build_mem(main, "rucksacks", RUCKSACK_IDX_WIDTH, 1)
    answer = build_mem(main, "answer", SCORE_WIDTH, 1)

    # (Constant) register for rucksack loop limit.
    rucksacks_reg = main.reg("rucksacks_reg", RUCKSACK_IDX_WIDTH)
    with main.group("init_rucksack") as init_rucksack:
        rucksacks.read_en = 1
        rucksacks.addr0 = 0
        rucksacks_reg.write_en = rucksacks.read_done
        rucksacks_reg.in_ = rucksacks.out
        init_rucksack.done = rucksacks_reg.done

    # Increment for rucksack loop.
    rucksack_idx = main.reg("rucksack_idx", RUCKSACK_IDX_WIDTH)
    rucksack_add = main.add("rucksack_add", RUCKSACK_IDX_WIDTH)
    with main.group("incr_rucksack") as incr_rucksack:
        rucksack_add.left = rucksack_idx.out
        rucksack_add.right = 1
        rucksack_idx.write_en = 1
        rucksack_idx.in_ = rucksack_add.out
        incr_rucksack.done = rucksack_idx.done

    # Exit check for rucksack loop.
    rucksack_lt = main.cell(
        "rucksack_lt",
        ast.Stdlib().op("lt", RUCKSACK_IDX_WIDTH, signed=False),
    )
    with main.comb_group("check_rucksack") as check_rucksack:
        rucksack_lt.left = rucksack_idx.out
        rucksack_lt.right = rucksacks_reg.out

    # Register for the contents loop limit. In compartment mode, divide
    # the rucksack length by 2 to get the *compartment* length.
    items = main.reg("items", LENGTH_WIDTH)
    with main.group("init_items") as init_items:
        lengths.read_en = 1
        lengths.addr0 = rucksack_idx.out

        # Halve the rucksack length to get the compartment length.
        if rucksacks_per_team == 1:
            rsh = main.cell(
                "rsh",
                ast.Stdlib().op("rsh", LENGTH_WIDTH, signed=False),
            )
            rsh.left = lengths.out
            rsh.right = const(LENGTH_WIDTH, 1)  # Shift down 1 bit.
            val = rsh.out
        else:
            val = lengths.out

        items.write_en = lengths.read_done
        items.in_ = val
        init_items.done = items.done

    # Reset the contents loop counter.
    item_idx = main.reg("item_idx", LENGTH_WIDTH)
    with main.group("reset_item") as reset_item:
        item_idx.write_en = 1
        item_idx.in_ = 0
        reset_item.done = item_idx.done

    # Increment for the item loop.
    item_add = main.add("item_add", LENGTH_WIDTH)
    with main.group("incr_item") as incr_item:
        item_add.left = item_idx.out
        item_add.right = 1
        item_idx.write_en = 1
        item_idx.in_ = item_add.out
        incr_item.done = item_idx.done

    # Exit check for *first* item loop.
    item_lt = main.cell(
        "item_lt",
        ast.Stdlib().op("lt", LENGTH_WIDTH, signed=False),
    )
    with main.comb_group("check_item") as check_item:
        item_lt.left = item_idx.out
        item_lt.right = items.out

    # Increment for the *global* item index.
    global_item_idx = main.reg("global_item_idx", CONTENTS_IDX_WIDTH)
    global_item_add = main.add("global_item_add", CONTENTS_IDX_WIDTH)
    with main.group("incr_global_item") as incr_global_item:
        global_item_add.left = global_item_idx.out
        global_item_add.right = 1
        global_item_idx.write_en = 1
        global_item_idx.in_ = global_item_add.out
        incr_global_item.done = global_item_idx.done

    # Save the *next* global start index at the beginning of the
    # outer loop: `next_idx = idx + 2 * items`
    next_idx = main.reg("next_idx", CONTENTS_IDX_WIDTH)
    pad = main.cell("pad_idx", ast.CompInst("std_pad", [LENGTH_WIDTH,
                                                        CONTENTS_IDX_WIDTH]))
    double = main.add("double", CONTENTS_IDX_WIDTH)
    jump_add = main.add("jump_add", CONTENTS_IDX_WIDTH)
    with main.group("save_next") as save_next:
        jump_add.left = global_item_idx.out
        pad.in_ = items.out
        double.left = pad.out
        double.right = pad.out
        jump_add.right = double.out
        next_idx.write_en = 1
        next_idx.in_ = jump_add.out
        save_next.done = next_idx.done

    # "Jump" to the start of the next rucksack in the contents memory.
    with main.group("jump_global_item") as jump_global_item:
        global_item_idx.write_en = 1
        global_item_idx.in_ = next_idx.out
        jump_global_item.done = global_item_idx.done

    # Load the actual item value from rucksack contents.
    item = main.reg("item", ITEM_WIDTH)
    with main.group("load_item") as load_item:
        contents.read_en = 1
        contents.addr0 = global_item_idx.out
        item.write_en = contents.read_done
        item.in_ = contents.out
        load_item.done = item.done

    # Filter subcomponents. We need one fewer filters than we have
    # chunks of components to process: the last one will merely check
    # the existing filters.
    filter_def = build_filter(prog, ITEM_WIDTH)
    num_filters = 1 if rucksacks_per_team == 1 else rucksacks_per_team - 1
    filters = [
        main.cell(f"filter{i}", filter_def)
        for i in range(num_filters)
    ]

    # Exit check for the "checker" loop, when we need an early exit
    # after the first collision is found.
    break_cond = main.cell("break_cond",
                           ast.Stdlib().op("wire", 1, signed=False))
    with main.comb_group("check_item_break") as check_item_break:
        item_lt.left = item_idx.out
        item_lt.right = items.out
        break_cond.in_ = (item_lt.out & ~filters[0].present) @ 1
        break_cond.in_ = ~(item_lt.out & ~filters[0].present) @ 0

    # Accumulator for duplicate item priorities.
    accum = main.reg("accum", SCORE_WIDTH)
    accum_add = main.add("accum_add", SCORE_WIDTH)
    pad = main.cell("pad", ast.CompInst("std_pad", [ITEM_WIDTH, SCORE_WIDTH]))
    with main.group("accum_priority") as accum_priority:
        accum_add.left = accum.out
        pad.in_ = item.out
        accum_add.right = pad.out
        accum.write_en = 1
        accum.in_ = accum_add.out
        accum_priority.done = accum.done

    # Publish result back to interface memory.
    with main.group("finish") as finish:
        answer.write_en = 1
        answer.addr0 = 0
        answer.in_ = accum.out
        finish.done = answer.write_done

    # Control fragment: a loop to *populate* a filter (i.e., mark
    # contents but don't check them).
    def populate_loop(filt):
        reset_item,
        return while_(item_lt.out, check_item, [
            load_item,
            invoke(filt, in_value=item.out, in_set=const(1, 1),
                   in_clear=const(1, 0)),
            {incr_item, incr_global_item},
        ])

    # Control fragment: a loop to *check* the filter, aborting early if
    # we find a collision.
    check_loop = [
        reset_item,
        while_(break_cond.out, check_item_break, [
            load_item,
            invoke(filters[0], in_value=item.out, in_set=const(1, 0),
                   in_clear=const(1, 0)),
            if_(filters[0].present, None, [
                accum_priority,
            ]),
            {incr_item, incr_global_item},
        ]),
    ]

    # Larger control fragment: "unrolled loop" to process all the
    # contiguous rucksacks in a "team" (not the term used in the
    # description, but "group" was already taken :).
    team_control = []
    for i in range(rucksacks_per_team):
        # Set up the contents register (the loop limit for processing
        # each set of contents), and record the place we'll jump for the
        # next rucksack.
        team_control += [
            init_items,
            save_next,
        ]

        if rucksacks_per_team == 1:
            # With only a single rucksack, check both compartments. Our
            # loop limit has already been adjusted to only look at one
            # compartment instead of the whole rucksack.
            team_control += [
                populate_loop(filters[0]),
                check_loop,
            ]
        elif i == rucksacks_per_team - 1:
            # *Check* the filter in the last rucksack.
            team_control.append(check_loop)
        else:
            # *Populate* the filter for every other rucksack.
            team_control.append(populate_loop(filters[i]))

        # Advance to the next rucksack.
        team_control += [
            {incr_rucksack, jump_global_item},
        ]

    # Control fragment: "unrolled loop" to reset all the filters.
    reset_filters = [
        invoke(filt, in_value=item.out, in_set=const(1, 1),
               in_clear=const(1, 1))
        for filt in filters
    ]

    # Overall control program.
    main.control += [
        init_rucksack,
        while_(rucksack_lt.out, check_rucksack,
               reset_filters + team_control),
        finish,
    ]

    return prog.program


def build_filter(prog, width):
    filter = prog.component("filter")

    filter.input("value", width)
    filter.input("set", 1)
    filter.input("clear", 1)
    filter.output("present", 1)

    markers = build_mem(filter, "markers", 1, 2 ** width, is_external=False)

    # Check whether the value has been seen before.
    present_reg = filter.reg("present_reg", 1)
    with filter.group("check_marker") as check_marker:
        markers.read_en = 1
        markers.addr0 = filter.this().value
        present_reg.write_en = markers.read_done
        present_reg.in_ = markers.out
        check_marker.done = present_reg.done

    # Mark the value as seen.
    with filter.group("set_marker") as set_marker:
        markers.write_en = 1
        markers.addr0 = filter.this().value
        markers.in_ = 1
        set_marker.done = markers.write_done

    # Connect output register to output.
    with filter.continuous:
        filter.this().present = present_reg.out

    # Clear loop: initialize.
    idx = filter.reg("idx", width)
    with filter.group("clear_init") as clear_init:
        idx.write_en = 1
        idx.in_ = 0
        clear_init.done = idx.done

    # Clear loop: body.
    with filter.group("clear_idx") as clear_idx:
        markers.write_en = 1
        markers.addr0 = idx.out
        markers.in_ = 0
        clear_idx.done = markers.write_done

    # Clear loop: increment.
    add = filter.add("add", width)
    with filter.group("incr") as incr:
        add.left = idx.out
        add.right = 1
        idx.write_en = 1
        idx.in_ = add.out
        incr.done = idx.done

    # Clear loop: bounds check. This turns out to be REALLY ANNOYING
    # because we want the bounds check to look like `idx < 64`, but we
    # *also* want `idx` to be a 6-bit value. So we have to rely on
    # overflow and check whether it's zero, and unroll the first
    # iteration?? Weird.
    neq = filter.cell("neq", ast.Stdlib().op("neq", width, signed=False))
    with filter.comb_group("check") as check:
        neq.left = idx.out
        neq.right = 0

    # Clear the output register.
    with filter.group("clear_present") as clear_present:
        present_reg.write_en = 1
        present_reg.in_ = 0
        clear_present.done = present_reg.done

    filter.control += \
        if_(filter.this().clear, None, [
                # Iteratively clear everything in the filter.
                clear_init,
                clear_idx,
                incr,
                while_(neq.out, check, [
                    clear_idx,
                    incr,
                ]),
                clear_present,
            ], if_(filter.this().set, None,
                   set_marker,
                   check_marker))

    return filter


if __name__ == '__main__':
    build().emit()
