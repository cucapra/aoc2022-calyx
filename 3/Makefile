.PHONY: all
all: sample

accel.futil: accelgen.py
	python3 $^ > $@

%.json: %.txt
	python3 convert.py < $^ > $@

%: accel.futil %.json
	fud e $< --to dat --through verilog -s verilog.data $*.json | \
		jq .memories.answer[0]

%-interp: accel.futil %.json
	fud e $< --to interpreter-out -s verilog.data $*.json | \
		jq .main.answer[0]

%-debug: accel.futil %.json
	fud e $< --to debugger -s verilog.data $*.json
