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

To solve part 2, we need to generalize a simple `max` operation to broader "top-k" functionality.
This was probably the most interesting part of the Calyx implementation: we use a parameterized generator that takes a `k` and produces a little component that wraps `k` registers.
You can think of many different ways to update the top `k` values, such as keeping a sorted list; we used a simple strategy that combinationally re-identifies the minimum value each time.
It's not clear if this is wise at all, but it is kind of fun.

To run the whole thing on the sample input, through Verilator:

    make part1-sample

To run on your special input, put it in a file called `full.txt` or something and then do:

    make part1-full

That's for the first star.
To earn the second star, use `part2-sample` or similar.

[day1]: https://adventofcode.com/2022/day/1
