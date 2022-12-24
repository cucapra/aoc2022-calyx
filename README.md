Accelerating the Advent of Code
===============================

This is an attempt to solve the [Advent of Code 2022][aoc] in [Calyx][], our intermediate language for generating hardware accelerators.
It is almost certainly doomed.

You can test all the solutions using [Turnt][].
This runs the sample inputs for everything:

    $ turnt -j */sample.txt

The Turnt setup does differential testing across two RTL simulators and Calyx's interpreter to make sure they all agree.
You can also just run the [Icarus Verilog][iverilog] simulations:

    $ turnt -j -e part1-icarus -e part2-icarus */sample.txt

When you have your own *full* input files, try something like this to print out the answer:

    $ turnt -e part1-icarus -p 1/full.txt

The `-p` flag tells Turnt to just print the result instead of checking it against the saved expected output.

[aoc]: https://adventofcode.com/2022/
[calyx]: https://calyxir.org
[turnt]: https://github.com/cucapra/turnt
[iverilog]: http://iverilog.icarus.com/
