from calyx.builder import Builder, const, while_
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

    # Temporaries.
    local_max = main.reg("local_max", WIDTH)
    global_max = main.reg("global_max", WIDTH)
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

    main.control += [
        {init_count, init_index},
        while_(lt.out, cmp, [
            incr,
        ]),
    ]

    return prog.program


if __name__ == '__main__':
    build().emit()
