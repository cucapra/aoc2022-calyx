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


def build():
    """Build the `main` component for AOC day 3.
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

    # Register for the contents loop limit.
    items = main.reg("items", LENGTH_WIDTH)
    with main.group("init_items") as init_items:
        lengths.read_en = 1
        lengths.addr0 = rucksack_idx.out
        items.write_en = lengths.read_done
        items.in_ = lengths.out
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

    # Exit check for item loop.
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

    # Load the actual item value from rucksack contents.
    item = main.reg("item", ITEM_WIDTH)
    with main.group("load_item") as load_item:
        contents.read_en = 1
        contents.addr0 = global_item_idx.out
        item.write_en = contents.read_done
        item.in_ = contents.out
        load_item.done = item.done

    # Filter subcomponent.
    filter_def = build_filter(prog, ITEM_WIDTH)
    filter = main.cell("filter", filter_def)

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

    main.control += [
        init_rucksack,
        while_(rucksack_lt.out, check_rucksack, [
            # First compartment.
            {init_items, reset_item},
            while_(item_lt.out, check_item, [
                load_item,
                invoke(filter, in_value=item.out, in_set=const(1, 1)),
                {incr_item, incr_global_item},
            ]),

            # Second compartment.
            reset_item,
            while_(item_lt.out, check_item, [
                load_item,
                invoke(filter, in_value=item.out, in_set=const(1, 0)),
                if_(filter.present, None, [
                    accum_priority,
                ]),
                {incr_item, incr_global_item},
            ]),

            incr_rucksack,
        ]),
        finish,
    ]

    return prog.program


def build_filter(prog, width):
    filter = prog.component("filter")

    filter.input("value", width)
    filter.input("set", 1)
    filter.output("present", 1)

    markers = build_mem(filter, "markers", 1, 2 ** width, is_external=False)

    # Check whether the value has been seen before.
    present_reg = filter.reg("present_reg", 1)
    with filter.group("check_marker") as check_marker:
        markers.read_en = 1
        markers.addr0 = filter.this().value
        present_reg.write_en = 1
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

    filter.control += if_(filter.this().set, None,
                          set_marker,
                          check_marker)

    return filter


if __name__ == '__main__':
    build().emit()
