Day 3: Rucksack Reorganization
==============================

As usual, try this to solve both parts on the sample input:

    $ turnt -e part1-icarus -e part2-icarus sample.txt

Or provide your own input text file.
(Also try `part*-interp`; I think it's interesting how much slower our interpreter is than the RTL simulators on this code.)
`part1` solves the "compartments" version of the puzzle;
`part2` solves the version that looks at "teams" of 3 elves.

The data format for this puzzle was interestingly sparse for a hardware implementation.
Instead of using a dense "marker" memory as I did for Day 1, this representation uses a memory full of rucksack sizes, which makes some things easier and some things harder.

The code generator is made somewhat fiddly and long by the need for a loop nest; there are three loops total here (for part 1).
It makes me wonder if there wouldn't be some nice way to make it easier to construct standard `for` loops in Calyx's Python builder.

The most hardwarey aspect of this puzzle was the "filter", i.e., the component that checks if we've seen a given item before.
I used a value-indexed memory of 1-bit flags.
It's basically the hardwarey reflection of a set of small values (and there are only 46 values in this domain).

I went a little overboard generalizing this solution to cover both Part 1 and Part 2.
It is, of course, possible to generate an accelerator for Part 2 that works with elf teams of *any* size, not just 3.
We generate "unrolled" loops that cover each elf within a team---in other words, the looping happens in Python and we splat out nearly-identical control statements for every elf in the team.
This makes the implementation of the generator fairly elaborate, and I think it also may reveal points where the code could be simplified with additional work on the Calyx builder.

[cider]: https://docs.calyxir.org/interpreter.html
