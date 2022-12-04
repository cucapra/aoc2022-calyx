.PHONY: all
all: sample

part1.futil: accelgen.py
	python3 $^ 1 > $@

part2.futil: accelgen.py
	python3 $^ 3 > $@

%.json: %.txt
	python3 convert.py < $^ > $@

part1-%: part1.futil %.json
	fud e $< --to dat --through verilog -s verilog.data $*.json | \
		jq .memories.answer[0]

part2-%: part2.futil %.json
	fud e $< --to dat --through verilog -s verilog.data $*.json | \
		jq .memories.answer[0]
