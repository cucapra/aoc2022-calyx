from calyx.builder import Builder, while_, invoke, const
from calyx import py_ast as ast

WIDTH = 32
MAX_SIZE = 4096
IDX_WIDTH = MAX_SIZE.bit_length()

ROCK = 0
PAPER = 1
SCISSORS = 2

WINS = {
    (ROCK, SCISSORS),
    (PAPER, ROCK),
    (SCISSORS, PAPER),
}
SHAPE_SCORE = [1, 2, 3]
LOSE_SCORE = 0
DRAW_SCORE = 3
WIN_SCORE = 6


def build_mem(comp, name, width, size, is_external=True, is_ref=False):
    idx_width = size.bit_length()
    comp.prog.import_("primitives/memories.futil")
    inst = ast.CompInst("seq_mem_d1", [width, size, idx_width])
    return comp.cell(name, inst, is_external=is_external, is_ref=is_ref)


def build():
    """Build the `main` component for AOC day 2.
    """
    prog = Builder()
    main = prog.component("main")

    # Inputs & outputs.
    them_mem = build_mem(main, "them", 2, MAX_SIZE)
    us_mem = build_mem(main, "us", 2, MAX_SIZE)
    count = build_mem(main, "count", IDX_WIDTH, 1)
    answer = build_mem(main, "answer", WIDTH, 1)

    # Scoring subcomponent.
    scorer_def = build_scorer(prog)
    scorer = main.cell("scorer", scorer_def)

    # Load the pair of moves at `index`.
    idx = main.reg("idx", IDX_WIDTH)
    with main.group("get_a_move") as get_a_move:
        them_mem.read_en = 1
        them_mem.addr0 = idx.out
        us_mem.read_en = 1
        us_mem.addr0 = idx.out
        get_a_move.done = (them_mem.read_done & us_mem.read_done) @ 1

    # Store the score for this move.
    accum = main.reg("accum", WIDTH)
    with main.group("store_score") as store_score:
        accum.write_en = 1
        accum.in_ = scorer.score
        store_score.done = accum.done

    # Publish the answer back to an interface memory.
    with main.group("finish") as finish:
        answer.write_en = 1
        answer.addr0 = 0
        answer.in_ = accum.out
        finish.done = answer.write_done

    # Loop increment.
    incr_add = main.add("incr_add", IDX_WIDTH)
    with main.group("incr") as incr:
        incr_add.left = idx.out
        incr_add.right = 1
        idx.write_en = 1
        idx.in_ = incr_add.out
        incr.done = idx.done

    # Load the loop maximum for convenient access.
    count_reg = main.reg("count_reg", IDX_WIDTH)
    with main.group("init") as init:
        count.read_en = 1
        count.addr0 = 0
        count_reg.write_en = count.read_done
        count_reg.in_ = count.out
        init.done = count_reg.done

    # Loop control comparator.
    lt = main.cell("lt", ast.Stdlib().op("lt", IDX_WIDTH, signed=False))
    with main.comb_group("check") as check:
        lt.left = idx.out
        lt.right = count_reg.out

    # Control program.
    main.control += [
        init,
        while_(lt.out, check, [
            get_a_move,
            invoke(scorer, in_them=them_mem.out, in_us=us_mem.out),
            store_score,
            incr,
        ]),
        finish,
    ]

    return prog.program


def build_scorer(prog):
    scorer = prog.component("scorer")
    scorer.input("them", 2)
    scorer.input("us", 2)
    scorer.output("score", WIDTH)

    # Look up shape score.
    shape_score = scorer.reg("shape_score", WIDTH)
    with scorer.group("get_shape_score") as get_shape_score:
        shape_score_wire = build_lut(scorer, "shape_score",
                                     SHAPE_SCORE, scorer.this().us)
        shape_score.write_en = 1
        shape_score.in_ = shape_score_wire.out
        get_shape_score.done = shape_score.done

    # Same for outcome score.
    outcome_score = scorer.reg("outcome_score", WIDTH)
    cat = scorer.cell("cat",  ast.CompInst("std_cat", [2, 2, 4]))
    with scorer.group("get_outcome_score") as get_outcome_score:
        # Concatenate the two moves to get the LUT's index.
        cat.left = scorer.this().them
        cat.right = scorer.this().us

        # Look up the value.
        outcome_score_wire = build_lut(scorer, "outcome_score",
                                       gen_outcome_table(), cat.out)

        # Write to the register.
        outcome_score.write_en = 1
        outcome_score.in_ = outcome_score_wire.out
        get_outcome_score.done = outcome_score.done

    # Continuously produce the total score.
    add = scorer.add("add", WIDTH)
    with scorer.continuous:
        add.left = shape_score.out
        add.right = outcome_score.out
        scorer.this().score = add.out

    # Control program.
    scorer.control += {get_shape_score, get_outcome_score}

    return scorer


def gen_outcome_table():
    """Generate a look-up table for outcome scores.

    The table is indexed by the 4-bit *concatenated pair* of "their"
    move and "our" move.
    """
    table = [0] * (2 ** 4)
    for them in (ROCK, PAPER, SCISSORS):
        for us in (ROCK, PAPER, SCISSORS):
            idx = (them << 2) | us
            if us == them:
                score = DRAW_SCORE
            elif (us, them) in WINS:
                score = WIN_SCORE
            else:
                score = LOSE_SCORE
            table[idx] = score
    return table


def build_lut(comp, name, table, inport):
    """Generate assignments to implement a look-up table.

    Return a wire component that has been assigned to produce the LUT's
    output based on the value of `outport`.
    """
    outwire = comp.cell(
        f"{name}_lut",
        ast.Stdlib().op("wire", WIDTH, signed=False),
    )
    key_size = (len(table) - 1).bit_length()
    for (key, value) in enumerate(table):
        outwire.in_ = (inport == const(key_size, key)) @ value
    return outwire


if __name__ == '__main__':
    build().emit()
