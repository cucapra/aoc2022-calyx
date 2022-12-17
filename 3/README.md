Day 3: Rucksack Reorganization
==============================

Type one of these two to run on the sample input:

    make sample-part1
    make sample-part1-interp

(The latter uses Calyx's interpreter, Cider.
I think it's interesting how much slower it is than the former, which uses Verilator.)
Or use `part2` instead to solve the version of the puzzle that looks at "teams" of 3 elves.

The data format for this puzzle was interestingly sparse for a hardware implementation.
Instead of using a dense "marker" memory as I did for Day 1, this representation uses a memory full of rucksack sizes, which makes some things easier and some things harder.

The code generator is made somewhat fiddly and long by the need for a loop nest; there are three loops total here.
It makes me wonder if there wouldn't be some nice way to make it easier to construct standard `for` loops in Calyx's Python builder.

The most hardwarey aspect of this puzzle was the "filter", i.e., the component that checks if we've seen a given item before.
I used a value-indexed memory of 1-bit flags.
It's basically the hardwarey reflection of a set of small values (and there are only 46 values in this domain).
