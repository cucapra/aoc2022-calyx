from calyx.builder import Builder, while_, if_
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
    accum = main.reg("local_max", WIDTH)
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

    # Update the global maximum calorie count:
    # global_max = max(accum, global_max)
    global_max = main.reg("global_max", WIDTH)
    max_gt = main.cell("max_gt", ast.Stdlib().op("gt", WIDTH, signed=False))
    max_mux = main.cell("max_mux",
                        ast.Stdlib().op("mux", WIDTH, signed=False))
    with main.group("update_max") as update_max:
        max_gt.left = accum.out
        max_gt.right = global_max.out

        max_mux.cond = max_gt.out
        max_mux.tru = accum.out
        max_mux.fal = global_max.out

        global_max.in_ = max_mux.out
        global_max.write_en = 1
        update_max.done = global_max.done

    # Publish the answer back to an interface memory.
    with main.group("finish") as finish:
        answer.write_en = 1
        answer.addr0 = 0
        answer.in_ = global_max.out
        finish.done = answer.write_done

    # The control program.
    main.control += [
        {init_count, init_index},
        while_(lt.out, cmp, [
            new_elf_check,
            if_(new_elf_reg.out, None, [
                update_max,
                clear_accum,
            ]),
            accum_calories,
            incr,
        ]),
        finish,
    ]

    return prog.program


if __name__ == '__main__':
    build().emit()
