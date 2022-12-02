%.json: %.txt
	python3 convert.py < $^ > $@

accel.futil: accelgen.py
	python3 $^ > $@
