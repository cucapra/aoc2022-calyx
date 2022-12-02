.PHONY: all
all: sample

accel.futil: accelgen.py
	python3 $^ > $@

%.json: %.txt
	python3 convert.py < $^ > $@

.PHONY: run
%: accel.futil %.json
	fud e $< --to dat --through verilog -s verilog.data $*.json | \
		jq .memories.answer[0]
