"""Generate memories for the strategy guide and score tables.

We encode Rock (A & X), Paper (B & Y), and Scissors (C & Z) into 2-bit
numbers (0, 1, and 2). Then there are just two memories of equal length:
"them" moves and "us" moves.

We also include look-up tables for two scoring functions: one for the
shape (indexed by the raw, two-bit rock/paper/scissors value) and one
for the outcome (indexed by the 4-bit *concatenated pair* of "their"
move and "our" move). It's possible this could be a lot more efficient
if we instructed the generated Verilog that these are ROMs, to be baked
into the design, rather than actual writable RAMs---but that's for
another day.
"""
import sys
import json

MAX_SIZE = 4096
WIDTH = 32

ROCK = 0
PAPER = 1
SCISSORS = 2

THEM_NUMS = {
    "A": ROCK,
    "B": PAPER,
    "C": SCISSORS,
}
US_NUMS = {
    "X": ROCK,
    "Y": PAPER,
    "Z": SCISSORS,
}

WINS = {
    (ROCK, SCISSORS),
    (PAPER, ROCK),
    (SCISSORS, PAPER),
}
SHAPE_SCORE = [1, 2, 3]
LOSE_SCORE = 0
DRAW_SCORE = 3
WIN_SCORE = 6


def convert(infile):
    them_moves = []
    us_moves = []

    for line in infile:
        line = line.strip()
        if line:
            them, us = line.split()
            them_moves.append(THEM_NUMS[them])
            us_moves.append(US_NUMS[us])

    assert len(them_moves) == len(us_moves)
    assert len(them_moves) <= MAX_SIZE
    padding = [0] * (MAX_SIZE - len(them_moves))

    return {
        # Inputs.
        "them": {
            "data": them_moves + padding,
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": 2,
            }
        },
        "us": {
            "data": us_moves + padding,
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": 2,
            }
        },
        "count": {
            "data": [len(them_moves)],
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": MAX_SIZE.bit_length(),
            },
        },

        # Output.
        "answer": {
            "data": [0],
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": WIDTH,
            },
        },

        # Look-up table ROMs.
        "outcome_score": {
            "data": gen_outcome_table(),
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": WIDTH,
            },
        },
        "shape_score": {
            "data": SHAPE_SCORE,
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": WIDTH,
            },
        },
    }


def gen_outcome_table():
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


if __name__ == "__main__":
    json.dump(convert(sys.stdin), sys.stdout,
              indent=2, sort_keys=True)
