accel.futil: accelgen.py
	python3 $^ > $@

%.json: %.txt
	python3 convert.py < $^ > $@

.PHONY: run
run: accel.futil sample.json
	fud e $< --to dat --through verilog -s verilog.data sample.json
