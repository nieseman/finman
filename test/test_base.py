#!/usr/bin/env python3

import json
import os
import tempfile
import unittest

from finmanlib.datafile import *



class TestWithSampleJsonFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.create_jsonl_files()


    @classmethod
    def tearDownClass(cls):
        cls.remove_jsonl_files()


    @classmethod
    def create_jsonl_files(cls):
        """
        Create a temporary JSONL files from given data.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp_file:
            cls.jsonl_filename1 = tmp_file.name

            for part_of_jsonl_file in (CONTENTS_TESTFILE_1_PART_A,
                                       CONTENTS_TESTFILE_1_PART_B):
                for json_line in part_of_jsonl_file:
                    json.dump(json_line, tmp_file)
                    tmp_file.write("\n")
                tmp_file.write("\n")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp_file:
            cls.jsonl_filename2 = tmp_file.name

            for part_of_jsonl_file in (CONTENTS_TESTFILE_2_PART_A,):
                for json_line in part_of_jsonl_file:
                    json.dump(json_line, tmp_file)
                    tmp_file.write("\n")
                tmp_file.write("\n")


    @classmethod
    def remove_jsonl_files(cls):
        """
        Remove the temporary JSONL files.
        """
        os.remove(cls.jsonl_filename1)
        os.remove(cls.jsonl_filename2)



CONTENTS_TESTFILE_1_PART_A = [
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

CONTENTS_TESTFILE_1_PART_B = [
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

CONTENTS_TESTFILE_2_PART_A = [
    {
        "type": "SourceFileInfo",
        "conversion_date": None,
        "filename": "test2.csv",
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
        "date_start": "1973-01-01",
        "date_end": "1973-01-31",
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
            "date": "1973-01-11",
            "value": "+11.00",
            "details": "Transfer 2-11"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 5,
        "columns": {
            "date": "1973-01-12",
            "value": "+11.00",
            "details": "Transfer 2-12"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 6,
        "columns": {
            "date": "1973-01-13",
            "value": "+11.00",
            "details": "Transfer 2-13"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 7,
        "columns": {
            "date": "1973-01-14",
            "value": "+11.00",
            "details": "Transfer 2-14"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 8,
        "columns": {
            "date": "1973-01-15",
            "value": "+11.00",
            "details": "Transfer 2-15"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 9,
        "columns": {
            "date": "1973-01-16",
            "value": "+11.00",
            "details": "Transfer 2-16"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 10,
        "columns": {
            "date": "1973-01-17",
            "value": "+11.00",
            "details": "Transfer 2-17"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 11,
        "columns": {
            "date": "1973-01-18",
            "value": "+11.00",
            "details": "Transfer 2-18"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 12,
        "columns": {
            "date": "1973-01-19",
            "value": "+11.00",
            "details": "Transfer 2-19"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 13,
        "columns": {
            "date": "1973-01-20",
            "value": "+11.00",
            "details": "Transfer 2-20"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 14,
        "columns": {
            "date": "1973-01-21",
            "value": "+11.00",
            "details": "Transfer 2-21"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    },
    {
        "type": "Trn",
        "line_num_in_csv": 15,
        "columns": {
            "date": "1973-01-22",
            "value": "+11.00",
            "details": "Transfer 2-22"
        },
        "notes": {
            "cat": "",
            "cat_auto": None,
            "remark": ""
        }
    }
]
