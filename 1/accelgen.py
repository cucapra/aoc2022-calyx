from calyx.builder import Builder, while_, if_, invoke, const
from calyx import py_ast as ast

WIDTH = 32
MAX_SIZE = 4096
IDX_WIDTH = MAX_SIZE.bit_length()


def build_mem(comp, name, width, size):
    idx_width = size.bit_length()
    inst = ast.CompInst("seq_mem_d1", [width, size, idx_width])
    return comp.cell(name, inst, is_external=True)


def build():
    prog = Builder()
    main = prog.component("main")

    # Interface memories.
    calories = build_mem(main, "calories", WIDTH, MAX_SIZE)
    markers = build_mem(main, "markers", 1, MAX_SIZE)
    count = build_mem(main, "count", WIDTH, 1)
    answer = build_mem(main, "answer", WIDTH, 1)

    # Temporaries.
    index = main.reg("index", IDX_WIDTH)
    count_reg = main.reg("count_reg", IDX_WIDTH)

    # Initialize count register for convenient access.
    slice = main.cell("slice", ast.Stdlib().slice(WIDTH, IDX_WIDTH))
    with main.group("init_count") as init_count:
        count.addr0 = 0
        count.read_en = 1

        count_reg.write_en = count.read_done
        slice.in_ = count.out
        count_reg.in_ = slice.out
        init_count.done = count_reg.done

    # Initialize index counter to zero. (Maybe this is unnecessary.)
    with main.group("init_index") as init_index:
        index.in_ = 0
        index.write_en = 1
        init_index.done = index.done

    # Loop control comparison.
    lt = main.cell("lt", ast.Stdlib().op("lt", IDX_WIDTH, signed=False))
    with main.comb_group("cmp") as cmp:
        lt.left = index.out
        lt.right = count_reg.out

    # Loop control increment.
    incr_add = main.add("incr_add", IDX_WIDTH)
    with main.group("incr") as incr:
        incr_add.left = index.out
        incr_add.right = 1
        index.in_ = incr_add.out
        index.write_en = 1
        incr.done = index.done

    # Reset calorie accumulator.
    accum = main.reg("accum", WIDTH)
    with main.group("clear_accum") as clear_accum:
        accum.in_ = 0
        accum.write_en = 1
        clear_accum.done = accum.done

    # Accumulate calories.
    add = main.add("add", WIDTH)
    with main.group("accum_calories") as accum_calories:
        calories.read_en = 1
        calories.addr0 = index.out

        add.left = calories.out
        add.right = accum.out

        accum.in_ = add.out
        accum.write_en = calories.read_done
        accum_calories.done = accum.done

    # Check whether we're looking at a new elf. We have to register the
    # result of the (sequential) check so we can use it in an `if`.
    eq = main.cell("eq", ast.Stdlib().op("eq", 1, signed=False))
    new_elf_reg = main.reg("new_elf_reg", 1)
    with main.group("new_elf_check") as new_elf_check:
        markers.read_en = 1
        markers.addr0 = index.out
        eq.left = markers.out
        eq.right = 1
        new_elf_reg.write_en = markers.read_done
        new_elf_reg.in_ = eq.out
        new_elf_check.done = new_elf_reg.done

    # Machinery to track the top K elves.
    topk_def = build_topk(prog, 3)  # TODO Should be a parameter.
    topk = main.cell("topk", topk_def)

    # Publish the answer back to an interface memory.
    with main.group("finish") as finish:
        answer.write_en = 1
        answer.addr0 = 0
        answer.in_ = topk.total
        finish.done = answer.write_done

    # The control program.
    main.control += [
        {init_count, init_index},
        while_(lt.out, cmp, [
            new_elf_check,
            if_(new_elf_reg.out, None, [
                invoke(topk, in_value=accum.out),
                clear_accum,
            ]),
            accum_calories,
            incr,
        ]),
        invoke(topk, in_value=accum.out),  # Count last elf.
        finish,
    ]

    return prog.program


def build_topk(prog: Builder, k: int):
    """Build a component that tracks the largest K values it sees.

    The strategy is that we keep the current "running" top K in K
    registers (unordered). If the new value is bigger than the smallest
    of these registers, we drop that smallest value and put the new
    value in its place. This strategy avoid the need to do sequential
    comparisons, or to keep a sorted list, but it does require some
    "reduction" logic to find the smallest value every time. This is
    probably acceptable for small K and admits reasonable parallelism;
    for larger K, you might want to store state about the order of the
    current top K.
    """
    topk = prog.component(f"top{k}")

    # You invoke the component with a new value to "push" into the set,
    # and you get the sum of the top K values you have ever pushed in
    # the past.
    topk.input("value", WIDTH)
    topk.output("total", WIDTH)

    # We keep track of the top K values in K registers.
    regs = [
        topk.reg(f"reg{i}", WIDTH)
        for i in range(k)
    ]

    # Continuously produce the sum of these registers. This could be a
    # reduction tree, but for now it's just a reduction "stick."
    with topk.continuous:
        last_add = None
        for i in range(1, k):
            add = topk.add(f"sum{i}", WIDTH)
            if last_add:
                add.left = last_add.out
            else:
                add.left = regs[0].out
            add.right = regs[i].out
            last_add = add
        topk.this().total = last_add.out

    # Similarly, continuously compute the min and argmin of all our
    # current values. There's a chance it would be better to wrap this
    # up in a `comb group`, but it's not clear exactly where we would
    # `with` it.
    idx_width = k.bit_length()
    with topk.group("argmin") as argmin:
        last_val = None
        last_idx = None
        for i in range(1, k):
            left_val = last_val.out if last_val else regs[0].out
            left_idx = last_idx.out if last_idx else 0

            # Compare with the next register.
            lt = topk.cell(f"lt{i}",
                           ast.Stdlib().op("lt", WIDTH, signed=False))
            lt.left = left_val
            lt.right = regs[i].out

            # Produce the resulting min and argmin.
            val = topk.cell(f"val{i}",
                            ast.Stdlib().op("wire", WIDTH, signed=False))
            idx = topk.cell(f"idx{i}",
                            ast.Stdlib().op("wire", idx_width, signed=False))
            val.in_ = lt.out @ left_val
            val.in_ = ~lt.out @ regs[i].out
            idx.in_ = lt.out @ left_idx
            idx.in_ = ~lt.out @ i

            # Record the current wires for the next comparison.
            last_val = val
            last_idx = idx

        # Write the results into registers.
        min_val_reg = topk.reg("min_val_reg", WIDTH)
        min_val_reg.write_en = 1
        min_val_reg.in_ = last_val.out
        min_idx_reg = topk.reg("min_idx_reg", idx_width)
        min_idx_reg.write_en = 1
        min_idx_reg.in_ = last_idx.out

        argmin.done = (min_val_reg.done & min_idx_reg.done) @ 1

    # Check whether the input value is bigger than the smallest stored
    # value.
    gt = topk.cell("gt", ast.Stdlib().op("gt", WIDTH, signed=False))
    with topk.comb_group("check") as check:
        gt.left = topk.this().value
        gt.right = min_val_reg.out

    # Replace the minimum value. Because we only have the index of the
    # register we need, we need a bunch of conditional logic to write
    # into the correct register.
    done_expr = None
    with topk.group("upd") as upd:
        for i in range(k):
            const_i = const(idx_width, i)
            regs[i].write_en = (min_idx_reg.out == const_i) @ 1
            regs[i].write_en = (min_idx_reg.out != const_i) @ 0
            regs[i].in_ = (min_idx_reg.out == const_i) @ topk.this().value
            done_part = (min_idx_reg.out == const_i) & regs[i].done
            if done_expr:
                done_expr |= done_part
            else:
                done_expr = done_part
        upd.done = done_expr @ 1

    # The control program.
    topk.control += [
        argmin,
        if_(gt.out, check, upd),
    ]

    return topk


if __name__ == '__main__':
    build().emit()
