.PHONY: all
all: part1.futil part2.futil sample.json

%.futil: accelgen.py
	python3 $^ $* > $@

%.json: %.txt
	python3 convert.py < $^ > $@
