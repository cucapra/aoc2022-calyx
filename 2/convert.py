"""Convert the strategy guide to numeric memories.

We encode Rock (A & X), Paper (B & Y), and Scissors (C & Z) into 2-bit
numbers (0, 1, and 2). Then there are just two memories of equal length:
"them" moves and "us" moves.
"""
import sys
import json

MAX_SIZE = 4096
WIDTH = 32
THEM_NUMS = {
    "A": 0,
    "B": 1,
    "C": 2,
}
US_NUMS = {
    "X": 0,
    "Y": 1,
    "Z": 2,
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
