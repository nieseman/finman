# Makefile for FinMan tests

default:

example-csv:
	cd demo/csv && ../create_sample_csv

example-jsonl:
	CSV_FMT=demo/CsvFormat_Demo.json; \
	for CSV in demo/csv/*.csv; do \
	    BASE=$$(basename $${CSV}); \
	    BASE=$${BASE%%.csv}; \
	    JSONL=demo/jsonl/$${BASE}.jsonl; \
	    PYTHONPATH=./src:${PYTHONPATH} src/finman-conv $${CSV_FMT} $${CSV} > $${JSONL}; \
	done

example-finman:
	PYTHONPATH=./src:${PYTHONPATH} src/finman  \
	    --cat data/Categories_Deutsch.json \
		demo/jsonl/transactions_????-??-??.jsonl

test:
	@echo "\n\n____________________"
	PYTHONPATH=./src:${PYTHONPATH} python3 test/test_datafile.py
	@echo "\n\n____________________"
	PYTHONPATH=./src:${PYTHONPATH} python3 test/test_selection.py


.PHONY: default example-csv example-jsonl example-finman test
