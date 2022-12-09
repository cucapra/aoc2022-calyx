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
    item = main.reg("item", LENGTH_WIDTH)
    with main.group("reset_item") as reset_item:
        item.write_en = 1
        item.in_ = 0
        reset_item.done = item.done

    # Increment for the item loop.
    item_add = main.add("item_add", LENGTH_WIDTH)
    with main.group("incr_item") as incr_item:
        item_add.left = item.out
        item_add.right = 1
        item.write_en = 1
        item.in_ = item_add.out
        incr_item.done = item.done

    # Exit check for item loop.
    item_lt = main.cell(
        "item_lt",
        ast.Stdlib().op("lt", LENGTH_WIDTH, signed=False),
    )
    with main.comb_group("check_item") as check_item:
        item_lt.left = item.out
        item_lt.right = items.out

    main.control += [
        init_rucksack,
        while_(rucksack_lt.out, check_rucksack, [
            {init_items, reset_item},
            while_(item_lt.out, check_item, [
                incr_item,
            ]),
            incr_rucksack,
        ]),
    ]

    return prog.program


if __name__ == '__main__':
    build().emit()
