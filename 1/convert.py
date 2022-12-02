"""Convert the text-based input format to numeric memories.

The output format consists of a `calories` memory that holds all the
calorie values strung together. A second `markers` memory of the same
length holds a 1-bit value that indicates whether a given index is the
beginning of a new elf. Finally, a one-entry `count` memory holds the
number of calorie numbers.
"""
import sys
import json


def convert(infile):
    calories = []
    markers = []

    is_first = True
    for line in infile:
        line = line.strip()
        if line:
            calories.append(int(line))
            markers.append(int(is_first))
            is_first = False
        else:
            is_first = True

    assert len(calories) == len(markers)

    return {
        "calories": {
            "data": calories,
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": 32,
            }
        },
        "markers": {
            "data": markers,
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": 1,
            }
        },
        "count": {
            "data": [len(calories)],
            "format": {
                "numeric_type": "bitnum",
                "is_signed": False,
                "width": 32,
            },
        },
    }


if __name__ == "__main__":
    json.dump(convert(sys.stdin), sys.stdout,
              indent=2, sort_keys=True)
