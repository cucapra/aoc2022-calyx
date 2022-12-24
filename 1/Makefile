.PHONY: all
all: part1.futil part2.futil sample.json

part1.futil: accelgen.py
	python3 $^ 1 > $@

part2.futil: accelgen.py
	python3 $^ 3 > $@

%.json: %.txt
	python3 convert.py < $^ > $@
