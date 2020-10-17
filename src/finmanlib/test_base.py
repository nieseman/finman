#!/usr/bin/env python3

import json
import os
import tempfile
import unittest

from finmanlib.datafile import *



class TestBase(unittest.TestCase):
    """
    Test class FinmanData and the classes of all instances contained within
    (i.e. all classes in file datafile.py).
    """

    @classmethod
    def setUpClass(cls):
        """
        Create a temporary JSONL file, which is read by each test.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            cls.jsonl_filename = tmp_file.name

            for part_of_jsonl_file in (CONTENTS_TESTFILE_PART_A,
                                       CONTENTS_TESTFILE_PART_B):
                for json_line in part_of_jsonl_file:
                    json.dump(json_line, tmp_file)
                    tmp_file.write("\n")
                tmp_file.write("\n")


    @classmethod
    def tearDownClass(cls):
        """
        Remove the temporary JSONL file.
        """
        os.remove(cls.jsonl_filename)


    def setUp(self):
        """
        Preparation for each test: load JSONL file and remember some
        sub-elements.
        """
        self.finman_data = FinmanData(self.jsonl_filename)
        try:
            self.jsonl_file = self.finman_data.jsonl_files[0]
            self.trns_set_a = self.jsonl_file.trns_sets[0]
            self.trns_set_b = self.jsonl_file.trns_sets[1]
            self.trn_a1     = self.trns_set_a.trns[0]
            self.trn_a2     = self.trns_set_a.trns[1]
            self.trn_b1     = self.trns_set_b.trns[0]
        except KeyError:
            assert False, "Missing data in data structures!?"



CONTENTS_TESTFILE_PART_A = [
    {
        "type": "SourceFileInfo",
        "conversion_date": None,
        "filename": "test1a.csv",
        "filesize": None,
        "sha1": None,
        "fmt": None,
        "currency": None,
        "columns": {
            "Datum": "date",
            "Betrag": "value",
            "Beschreibung": "details"
        },
        "num_lines": None,
        "num_trns": None
    },
    {
        "type": "SourceFileHeader",
        "bank_account": None,
        "date_start": "1972-07-01",
        "date_end": "1972-07-31",
        "date_first": None,
        "date_last": None,
        "value_start": None,
        "value_end": None,
        "value_diff": None
    },
    {
        "type": "Trn",
        "line_num_in_csv": 4,
        "columns": {
            "date": "1972-07-10",
            "value": "+100.78",
            "details": "Transfer 1a-1"
        },
        "notes": {
            "cat": "transfers",
            "cat_auto": True,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 5,
        "columns": {
            "date": "1972-07-20",
            "value": "+200.78",
            "details": "Transfer 1a-2"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": "abc"
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 6,
        "columns": {
            "date": "1972-07-30",
            "value": "+300.78",
            "details": "Transfer 1a-3"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    }
]

CONTENTS_TESTFILE_PART_B = [
    {
        "type": "SourceFileInfo",
        "conversion_date": None,
        "filename": "test1b.csv",
        "filesize": None,
        "sha1": None,
        "fmt": None,
        "currency": None,
        "columns": {
            "Datum": "date",
            "Betrag": "value",
            "Beschreibung": "details",
            "Konto": "account"
        },
        "num_lines": None,
        "num_trns": None
    },
    {
        "type": "SourceFileHeader",
        "bank_account": None,
        "date_start": "1972-08-01",
        "date_end": "1972-08-31",
        "date_first": None,
        "date_last": None,
        "value_start": None,
        "value_end": None,
        "value_diff": None
    },
    {
        "type": "Trn",
        "line_num_in_csv": 4,
        "columns": {
            "date": "1972-08-05",
            "value": "+100.55",
            "details": "Transfer 1b-1",
            "account": "DE 99 1111 2222 3333 4444 55"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    }
]
