Day 1: Calorie Counting
=======================

[This puzzle][day1] is not too tricky to do with a strictly-sequential implementation.

One important realization here is that picking the data format is essential; we need a preprocessor that translates the input text file into numerical data for the accelerator's memories.
The input format for this puzzle has "gaps" between each elf's food lists.
We encode the gaps with a very simple bitmask memory that's the same length as the (fully dense) calorie-value memory:
the bitmask is 1 where the calorie value is the first one for a given elf, and 0 otherwise (i.e., it's a continuation for the same elf).
This format should make it hypothetically fairly easy if we were to ever try to add some parallelism; we could just chunk up the address space and "round" to the nearest elf.

It was very helpful to use a Python generator instead of writing the Calyx IL directly.
Simple quality-of-life advantages include interleaving cells and the groups that use them.
It was also nice to be able to define Python constants for magic numbers (various sizes and widths).

To run the whole thing on the sample input, through Verilator:

    make sample

To run on your special input, put it in a file called `full.txt` or something and then do:

    make full

The current implementation earns one star.
For the second star, we'd need to implement some "top-k" comparison, which shouldn't be too hard.
It would be entertaining, if not all that wise, to try to do this with some parallelism.

[day1]: https://adventofcode.com/2022/day/1
