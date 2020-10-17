# Makefile for FinMan tests

default:

example-csv:
	cd ../demo && ./create_sample_csv

example-jsonl:
	CSV_FMT=../demo/CsvFormat_Demo.json; \
	for CSV in ../demo/*.csv; do \
	    ./finman-conv $${CSV_FMT} $${CSV} > $${CSV%%.csv}.jsonl; \
	done

example-finman:
	./finman  --cat ../data/Categories_Deutsch.json  ../demo/transactions_????-??-??.jsonl

test:
	./test_finman


.PHONY: default example-csv example-json test
