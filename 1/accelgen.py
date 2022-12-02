from calyx.builder import Builder, const
from calyx import py_ast

WIDTH = 32
MAX_SIZE = 4096


def build_mem(comp, name, width, size):
    idx_width = size.bit_length()
    inst = py_ast.CompInst("seq_mem_d1", [width, size, idx_width])
    return comp.cell("calories", inst, is_external=True)


def build():
    prog = Builder()
    main = prog.component("main")

    # Interface memories.
    calories = build_mem(main, "calories", WIDTH, MAX_SIZE)
    markers = build_mem(main, "calories", 1, MAX_SIZE)
    count = build_mem(main, "calories", WIDTH, 1)

    return prog.program


if __name__ == '__main__':
    build().emit()
