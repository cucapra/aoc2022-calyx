"""Generate memories for the strategy guide and score tables.

We encode Rock (A & X), Paper (B & Y), and Scissors (C & Z) into 2-bit
numbers (0, 1, and 2). Then there are just two memories of equal length:
"them" moves and "us" moves.
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
    }


if __name__ == "__main__":
    json.dump(convert(sys.stdin), sys.stdout,
              indent=2, sort_keys=True)
