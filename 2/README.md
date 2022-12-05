Day 2: Rock Paper Scissors
==========================

To solve the two parts on the sample input in `sample.txt`, type:

    make part1-sample
    make part2-sample

Then replace `sample` with the name of your full input text file to solve the real thing.

This puzzle involves several arbitrarily-chosen score values for two conditions (which shape you play, and whether you win, lose, or tie).
In hardware, the natural strategy for this sort of thing is a look-up table (LUT).
So that's what this solution is: a glorified wrapper around two very small LUTs.

In Calyx, the LUTs look like chains of mutually exclusive conditional assignments, like this:

    outcome_score_lut.in = cat.out == 4'd0 ? 32'd3;
    outcome_score_lut.in = cat.out == 4'd1 ? 32'd6;
    outcome_score_lut.in = cat.out == 4'd2 ? 32'd0;
    outcome_score_lut.in = cat.out == 4'd3 ? 32'd0;

...and so on.
This particular example uses a key that is the bitwise concatenation of two smaller values ("our" shape and "their" shape).

At first, I built the LUTs using actual memories instead of conditional logic.
This *really* seemed like overkill for their small size, however.

The design is ripe for simple DOALL parallelism (it's a simple `map` followed by an add-reduction), which would be a fun extension.
