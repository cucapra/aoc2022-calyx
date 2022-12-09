import sys
from calyx.builder import Builder, while_, invoke, const
from calyx import py_ast as ast

MAX_CONTENTS = 16384
MAX_RUCKSACKS = 512
ITEM_WIDTH = 6
LENGTH_WIDTH = 8
SCORE_WIDTH = 32

RUCKSACK_IDX_WIDTH = MAX_RUCKSACKS.bit_length()


def build_mem(comp, name, width, size, is_external=True, is_ref=False):
    idx_width = size.bit_length()
    comp.prog.import_("primitives/memories.futil")
    inst = ast.CompInst("seq_mem_d1", [width, size, idx_width])
    return comp.cell(name, inst, is_external=is_external, is_ref=is_ref)


def build():
    """Build the `main` component for AOC day 3.
    """
    prog = Builder()
    main = prog.component("main")

    # Inputs & outputs.
    contents = build_mem(main, "contents", 2, MAX_CONTENTS)
    lengths = build_mem(main, "lengths", 2, MAX_RUCKSACKS)
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

    main.control += [
        init_rucksack,
        while_(rucksack_lt.out, check_rucksack, [
            incr_rucksack,
        ]),
    ]

    return prog.program


if __name__ == '__main__':
    build().emit()
