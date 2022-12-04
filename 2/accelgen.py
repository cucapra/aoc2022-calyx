import sys
from calyx.builder import Builder, while_, if_, invoke, const
from calyx import py_ast as ast

WIDTH = 32
MAX_SIZE = 4096
IDX_WIDTH = MAX_SIZE.bit_length()


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
    count = build_mem(main, "count", WIDTH, 1)
    answer = build_mem(main, "answer", WIDTH, 1)

    # Scoring look-up tables.
    outcome_score = build_mem(main, "outcome_score", WIDTH, 2 ** 4)
    shape_score = build_mem(main, "shape_score", WIDTH, 3)

    # Scoring subcomponent.
    scorer_def = build_scorer(prog)
    scorer = main.cell("topk", scorer_def)

    # Load a pair of moves.
    with main.group("get_a_move") as get_a_move:
        them_mem.read_en = 1
        them_mem.addr0 = 0
        us_mem.read_en = 1
        us_mem.addr0 = 0
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

    # Control program.
    main.control += [
        get_a_move,
        invoke(scorer, in_them=them_mem.out, in_us=us_mem.out),
        store_score,
        finish,
    ]

    return prog.program


def build_scorer(prog):
    scorer = prog.component("scorer")
    scorer.input("them", 2)
    scorer.input("us", 2)
    scorer.output("score", WIDTH)

    # Memory references to LUTs.
    outcome_score_lut = build_mem(scorer, "outcome_score_lut", WIDTH, 2 ** 4,
                                  is_external=False, is_ref=True)
    shape_score_lut = build_mem(scorer, "shape_score_lut", WIDTH, 3,
                                is_external=False, is_ref=True)

    # Look up shape score. Registering the output of a sequential memory
    # seems a little redundant, but it seems necessary to stabilize the
    # result for subsequent use? Not sure. TODO REMOVE
    shape_score = scorer.reg("shape_score", WIDTH)
    with scorer.group("get_shape_score") as get_shape_score:
        shape_score_lut.read_en = 1
        shape_score_lut.addr = scorer.this().us
        shape_score.write_en = shape_score_lut.done
        shape_score.in_ = shape_score_lut.out
        get_shape_score.done = shape_score.done

    # Same for outcome score.
    outcome_score = scorer.reg("outcome_score", WIDTH)
    cat = scorer.cell("cat",  ast.CompInst("std_cat", [2, 2, 4]))
    with scorer.group("get_outcome_score") as get_outcome_score:
        # Concatenate the two moves to get the LUT's index.
        cat.left = scorer.this().them
        cat.right = scorer.this().us

        # Look up the value.
        outcome_score_lut.read_en = 1
        outcome_score_lut.addr = cat.out
        outcome_score.write_en = outcome_score_lut.done
        outcome_score.in_ = outcome_score_lut.out
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


if __name__ == '__main__':
    build().emit()
