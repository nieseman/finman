#!/usr/bin/env python3

"""
Tests of file datafile.py.
"""

import logging
import unittest

from test_base import TestWithSampleJsonFiles
from finmanlib.datafile import FinmanData



class TestFinmanData(TestWithSampleJsonFiles):
    """
    Test class FinmanData and the classes of all instances contained within
    (i.e. all classes in file datafile.py).
    """

    def setUp(self):
        """
        Preparation for each test: load JSONL file and remember some
        sub-elements.
        """
        self.finman_data = FinmanData((self.jsonl_filename1,
                                       self.jsonl_filename2))
        try:
            self.jsonl_file1 = self.finman_data.jsonl_files[0]
            self.jsonl_file2 = self.finman_data.jsonl_files[1]
            self.trns_set_1a = self.jsonl_file1.trns_sets[0]
            self.trns_set_1b = self.jsonl_file1.trns_sets[1]
            self.trn_1a1     = self.trns_set_1a.trns[0]
            self.trn_1a2     = self.trns_set_1a.trns[1]
        except KeyError:
            assert False, "Missing data in data structures!?"


    def testLoading(self):
        """
        Test the loading of JSONL data by checking some attributes.
        """
        # Some of the loading is implicitly tested in setUp(), testRepr().

        # FinmanData and JsonlFile objects.
        self.assertEqual(self.finman_data.filenames,        (self.jsonl_filename1,
                                                             self.jsonl_filename2))
        self.assertEqual(self.jsonl_file1.filename,          self.jsonl_filename1)
        self.assertEqual(self.jsonl_file2.filename,          self.jsonl_filename2)

        # TrnsSet objects.
        self.assertEqual(self.trns_set_1a.src.filename,      "test1a.csv")
        self.assertEqual(self.trns_set_1a.header.date_start, "1972-07-01")
        self.assertEqual(self.trns_set_1a.header.date_end,   "1972-07-31")
        self.assertEqual(self.trns_set_1a.src.columns,       {
            "Datum": "date",
            "Betrag": "value",
            "Beschreibung": "details"
        })
        self.assertEqual(self.trns_set_1b.src.filename,      "test1b.csv")
        self.assertEqual(self.trns_set_1b.header.date_start, "1972-08-01")
        self.assertEqual(self.trns_set_1b.header.date_end,   "1972-08-31")
        self.assertEqual(self.trns_set_1b.src.columns,       {
            "Datum": "date",
            "Betrag": "value",
            "Beschreibung": "details",
            "Konto": "account"
        })

        # Trn objects.
        self.assertEqual(self.trn_1a1._is_modified,    False)
        self.assertEqual(self.trn_1a1.line_num_in_csv, 4)
        self.assertEqual(self.trn_1a1.columns,         {
            "date": "1972-07-10",
            "value": "+100.78",
            "details": "Transfer 1a-1"
        })
        self.assertEqual(self.trn_1a1.notes,           {
            "cat": "transfers",
            "cat_auto": True,
            "remark": ""
        })
        self.assertEqual(self.trn_1a2._is_modified,    False)
        self.assertEqual(self.trn_1a2.line_num_in_csv, 5)
        self.assertEqual(self.trn_1a2.columns,         {
            "date": "1972-07-20",
            "value": "+200.78",
            "details": "Transfer 1a-2"
        })
        self.assertEqual(self.trn_1a2.notes,           {
            "cat": "",
            "cat_auto": None,
            "remark": "abc"
        })


    def testRepr(self):
        """
        Test the various __repr__() functions.

        This includes checking for proper file loading, helper functions
        str_modified()/plural(), the is_modified() state.
        """

        # 
        fmt_finman_data = f"<FinmanData: 2 JSONL files (%s): {self.jsonl_filename1}, " \
                                                           f"{self.jsonl_filename2}>"
        fmt_jsonl_file1 = f"<JsonlFile {self.jsonl_filename1} (%s): 2 transaction sets, 4 transactions>"
        fmt_jsonl_file2 = f"<JsonlFile {self.jsonl_filename2} (%s): 1 transaction set, 12 transactions>"
        fmt_trns_set_1a = f"<TrnsSet test1a.csv (%s): 3 transactions>"
        fmt_trns_set_1b = f"<TrnsSet test1b.csv (%s): 1 transaction>"
        fmt_trn_1a1     = f"<Trn #1-3 (%s)>"
        fmt_trn_1a2     = f"<Trn #1-4 (%s)>"

        # repr's before modification.
        self.assertEqual(repr(self.finman_data),  fmt_finman_data % "unmodified")
        self.assertEqual(repr(self.jsonl_file1),  fmt_jsonl_file1 % "unmodified")
        self.assertEqual(repr(self.jsonl_file2),  fmt_jsonl_file2 % "unmodified")
        self.assertEqual(repr(self.trns_set_1a),  fmt_trns_set_1a % "unmodified")
        self.assertEqual(repr(self.trns_set_1b),  fmt_trns_set_1b % "unmodified")
        self.assertEqual(repr(self.trn_1a1),      fmt_trn_1a1     % "unmodified")
        self.assertEqual(repr(self.trn_1a2),      fmt_trn_1a2     % "unmodified")

        # repr's after modification of transaction trn1.
        self.trn_1a1.set_remark('abc')
        self.assertEqual(repr(self.finman_data),  fmt_finman_data % "modified")
        self.assertEqual(repr(self.jsonl_file1),  fmt_jsonl_file1 % "modified")
        self.assertEqual(repr(self.jsonl_file2),  fmt_jsonl_file2 % "unmodified")
        self.assertEqual(repr(self.trns_set_1a),  fmt_trns_set_1a % "modified")
        self.assertEqual(repr(self.trns_set_1b),  fmt_trns_set_1b % "unmodified")
        self.assertEqual(repr(self.trn_1a1),      fmt_trn_1a1     % "modified")
        self.assertEqual(repr(self.trn_1a2),      fmt_trn_1a2     % "unmodified")

        # repr's after clearing of transaction trn1.
        self.trn_1a1.clear_modified()
        self.assertEqual(repr(self.finman_data),  fmt_finman_data % "unmodified")
        self.assertEqual(repr(self.jsonl_file1),  fmt_jsonl_file1 % "unmodified")
        self.assertEqual(repr(self.jsonl_file2),  fmt_jsonl_file2 % "unmodified")
        self.assertEqual(repr(self.trns_set_1a),  fmt_trns_set_1a % "unmodified")
        self.assertEqual(repr(self.trns_set_1b),  fmt_trns_set_1b % "unmodified")
        self.assertEqual(repr(self.trn_1a1),      fmt_trn_1a1     % "unmodified")
        self.assertEqual(repr(self.trn_1a2),      fmt_trn_1a2     % "unmodified")


    def testTrnFrields(self):
        """
        Test the Trn methods regarding field access: get_all_field_names() and get_field().
        """
        trn = self.trn_1a1

        self.assertEqual(trn.get_all_field_names(),
                {"_id", "_idx", "_is_modified", "_cat_alt", "line_num_in_csv",
                 "date", "value", "details",        # from columns dict
                 "cat", "cat_auto", "remark"})      # from notes dict

        self.assertEqual(trn.get_field("line_num_in_csv"), 4)
        self.assertEqual(trn.get_field("date"),            "1972-07-10")
        self.assertEqual(trn.get_field("value"),           "+100.78")
        self.assertEqual(trn.get_field("details"),         "Transfer 1a-1")
        self.assertEqual(trn.get_field("cat"),             "transfers")
        self.assertEqual(trn.get_field("cat_auto"),        True)
        self.assertEqual(trn.get_field("remark"),          "")

        self.assertEqual(trn.get_field("nonexisting_field"), "")


    def testTrnModified(self):
        """
        Test the Trn methods regarding modification status: is_modified().
        """
        trn = self.trn_1a1

        self.assertEqual(trn._is_modified,  False)
        self.assertEqual(trn.is_modified(), False)
        trn._is_modified = True
        self.assertEqual(trn._is_modified,  True)
        self.assertEqual(trn.is_modified(), True)


    def testTrnCat(self):
        """
        Test the Trn methods regarding category access: set_cat(), clear_cat().
        """
        trn = self.trn_1a1
        self.assertEqual(trn.get_field("cat"),      "transfers")
        self.assertEqual(trn.get_field("cat_auto"), True)
        self.assertEqual(trn.is_modified(),         False)

        trn.set_cat("xyz")
        self.assertEqual(trn.get_field("cat"),      "xyz")
        self.assertEqual(trn.get_field("cat_auto"), False)
        self.assertEqual(trn.is_modified(),         True)

        self._is_modified = False
        trn.clear_cat()
        self.assertEqual(trn.get_field("cat"),      "")
        self.assertEqual(trn.get_field("cat_auto"), None)
        self.assertEqual(trn.is_modified(),         True)

        trn.set_cat("JKL", cat_auto=True)
        self.assertEqual(trn.get_field("cat"),      "JKL")
        self.assertEqual(trn.get_field("cat_auto"), True)
        self.assertEqual(trn.is_modified(),         True)


    def testTrnRemark(self):
        """
        Test the Trn methods regarding category access: set_remark().
        """
        trn = self.trn_1a2
        self.assertEqual(trn.get_field("remark"),   "abc")
        self.assertEqual(trn.is_modified(),         False)

        trn.set_remark("1234")
        self.assertEqual(trn.get_field("remark"),   "1234")
        self.assertEqual(trn.is_modified(),         True)


    def testFileSave(self):
        """
        Test the saving of JSONL files.
        """
        # TBD


    def testFinmanDataFieldAccess(self):
        """
        Test the access of data fields from the FinmanData object.
        """
        self.assertEqual(self.finman_data.known_field_names,
                {"_id", "_idx", "_is_modified", "_cat_alt", "line_num_in_csv",
                 "date", "value", "details",        # from columns dict
                 "cat", "cat_auto", "remark",       # from notes dict
                 "account"})                        # This one is from part B.

        # Positive find by full name.
        self.assertEqual(self.finman_data.expand_fieldname('_id'), '_id')
        self.assertEqual(self.finman_data.expand_fieldname('_idx'), '_idx')
        self.assertEqual(self.finman_data.expand_fieldname('value'), 'value')

        # Positive find by partial name.
        self.assertEqual(self.finman_data.expand_fieldname('val'), 'value')

        # Negative find due to multiple expansions.
        self.assertEqual(self.finman_data.expand_fieldname('_i'), '')

        # Negative find due no expansions.
        self.assertEqual(self.finman_data.expand_fieldname('nonexisting_field'), '')

        # Btw, this function also works for attributes which are not present in all transactions.
        self.assertEqual(self.finman_data.expand_fieldname('account'), 'account')



if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    unittest.main()
