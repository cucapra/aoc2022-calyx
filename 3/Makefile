.PHONY: all
all: sample

part1.futil: accelgen.py
	python3 $^ 1 > $@

part2.futil: accelgen.py
	python3 $^ 3 > $@

%.json: %.txt
	python3 convert.py < $^ > $@

%-part1: part1.futil %.json
	fud e $< --to dat --through verilog -s verilog.data $*.json | \
		jq .memories.answer[0]

%-part1-interp: part1.futil %.json
	fud e $< --to interpreter-out -s verilog.data $*.json | \
		jq .main.answer[0]

%-part1-debug: part1.futil %.json
	fud e $< --to debugger -s verilog.data $*.json

%-part2: part2.futil %.json
	fud e $< --to dat --through verilog -s verilog.data $*.json | \
		jq .memories.answer[0]

%-part2-interp: part2.futil %.json
	fud e $< --to interpreter-out -s verilog.data $*.json | \
		jq .main.answer[0]

%-part2-debug: part2.futil %.json
	fud e $< --to debugger -s verilog.data $*.json
