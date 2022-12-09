"""Generate memories for the rucksack contents.

The idea is to use the priority value of each item (which unambiguously
identifies the item in 6 bits). We record the *size* of one
*compartment* in each rucksack (so this is a sparse encoding, unlike Day
1).
"""
import sys
import json

MAX_CONTENTS = 16384
MAX_RUCKSACKS = 512
ITEM_WIDTH = 6
LENGTH_WIDTH = 8
SCORE_WIDTH = 32


def char2pri(c):
    return ord(c) - ord('a') + 1 if c > 'Z' else \
        ord(c) - ord('A') + 27


def convert(infile):
    contents = []
    lengths = []

    for line in infile:
        line = line.strip()
        vals = [char2pri(c) for c in line]
        contents += vals
        lengths.append(len(vals) // 2)

    assert len(contents) <= MAX_CONTENTS

    return {
        # Inputs.
        "contents": {
            "data": contents + [0] * (MAX_CONTENTS - len(contents)),
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": ITEM_WIDTH,
            }
        },
        "lengths": {
            "data": lengths + [0] * (MAX_RUCKSACKS - len(lengths)),
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": LENGTH_WIDTH,
            }
        },
        "rucksacks": {
            "data": [len(lengths)],
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": MAX_RUCKSACKS.bit_length(),
            },
        },

        # Output.
        "answer": {
            "data": [0],
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": SCORE_WIDTH,
            },
        },
    }


if __name__ == "__main__":
    json.dump(convert(sys.stdin), sys.stdout,
              indent=2, sort_keys=True)
