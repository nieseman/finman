#!/usr/bin/env python3

from finmanlib.test_base import TestBase



class TestFinmanData(TestBase):
    """
    Test class FinmanData and the classes of all instances contained within
    (i.e. all classes in file datafile.py).
    """

    def testLoading(self):
        """
        Test the loading of JSONL data by checking some attributes.
        """
        # Some of the loading is implicitly tested in setUp(), testRepr().

        # FinmanData and JsonlFile objects.
        self.assertEqual(self.finman_data.filenames,        [self.jsonl_filename])
        self.assertEqual(self.jsonl_file.filename,          self.jsonl_filename)

        # TrnsSet objects.
        self.assertEqual(self.trns_set_a.src.filename,      "test1a.csv")
        self.assertEqual(self.trns_set_a.header.date_start, "1972-07-01")
        self.assertEqual(self.trns_set_a.header.date_end,   "1972-07-31")
        self.assertEqual(self.trns_set_a.src.columns,       {
            "Datum": "date",
            "Betrag": "value",
            "Beschreibung": "details"
        })
        self.assertEqual(self.trns_set_b.src.filename,      "test1b.csv")
        self.assertEqual(self.trns_set_b.header.date_start, "1972-08-01")
        self.assertEqual(self.trns_set_b.header.date_end,   "1972-08-31")
        self.assertEqual(self.trns_set_b.src.columns,       {
            "Datum": "date",
            "Betrag": "value",
            "Beschreibung": "details",
            "Konto": "account"
        })

        # Trn objects.
        self.assertEqual(self.trn_a1._is_modified,    False)
        self.assertEqual(self.trn_a1.line_num_in_csv, 4)
        self.assertEqual(self.trn_a1.columns,         {
            "date": "1972-07-10",
            "value": "+100.78",
            "details": "Transfer 1a-1"
        })
        self.assertEqual(self.trn_a1.notes,           {
            "cat": "transfers",
            "cat_auto": True,
            "remark": ""
        })
        self.assertEqual(self.trn_a2._is_modified,    False)
        self.assertEqual(self.trn_a2.line_num_in_csv, 5)
        self.assertEqual(self.trn_a2.columns,         {
            "date": "1972-07-20",
            "value": "+200.78",
            "details": "Transfer 1a-2"
        })
        self.assertEqual(self.trn_a2.notes,           {
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

        # Repr's before modification.
        self.assertEqual(repr(self.finman_data),  f"<FinmanData: 1 JSONL file (unmodified): {self.jsonl_filename}>")
        self.assertEqual(repr(self.jsonl_file),   f"<JsonlFile {self.jsonl_filename} (unmodified): 2 transaction sets, 4 transactions>")
        self.assertEqual(repr(self.trns_set_a),   f"<TrnsSet test1a.csv (unmodified): 3 transactions>")
        self.assertEqual(repr(self.trns_set_b),   f"<TrnsSet test1b.csv (unmodified): 1 transaction>")
        self.assertEqual(repr(self.trn_a1),       f"<Trn #3 (unmodified)>")
        self.assertEqual(repr(self.trn_a2),       f"<Trn #4 (unmodified)>")

        # Repr's after modification of transaction trn1.
        self.trn_a1.set_remark('abc')
        self.assertEqual(repr(self.finman_data),  f"<FinmanData: 1 JSONL file (modified): {self.jsonl_filename}>")
        self.assertEqual(repr(self.jsonl_file),   f"<JsonlFile {self.jsonl_filename} (modified): 2 transaction sets, 4 transactions>")
        self.assertEqual(repr(self.trns_set_a),   f"<TrnsSet test1a.csv (modified): 3 transactions>")
        self.assertEqual(repr(self.trns_set_b),   f"<TrnsSet test1b.csv (unmodified): 1 transaction>")
        self.assertEqual(repr(self.trn_a1),       f"<Trn #3 (modified)>")
        self.assertEqual(repr(self.trn_a2),       f"<Trn #4 (unmodified)>")

        # Repr's after clearing of transaction trn1.
        self.trn_a1.clear_modified()
        self.assertEqual(repr(self.finman_data),  f"<FinmanData: 1 JSONL file (unmodified): {self.jsonl_filename}>")
        self.assertEqual(repr(self.jsonl_file),   f"<JsonlFile {self.jsonl_filename} (unmodified): 2 transaction sets, 4 transactions>")
        self.assertEqual(repr(self.trns_set_a),   f"<TrnsSet test1a.csv (unmodified): 3 transactions>")
        self.assertEqual(repr(self.trns_set_b),   f"<TrnsSet test1b.csv (unmodified): 1 transaction>")
        self.assertEqual(repr(self.trn_a1),       f"<Trn #3 (unmodified)>")
        self.assertEqual(repr(self.trn_a2),       f"<Trn #4 (unmodified)>")


    def testTrnFrields(self):
        """
        Test the Trn methods regarding field access: get_all_field_names() and get_field().
        """
        trn = self.trn_a1

        self.assertEqual(trn.get_all_field_names(),
                {"_id", "_idx", "line_num_in_csv",
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
        trn = self.trn_a1

        self.assertEqual(trn._is_modified,  False)
        self.assertEqual(trn.is_modified(), False)
        trn._is_modified = True
        self.assertEqual(trn._is_modified,  True)
        self.assertEqual(trn.is_modified(), True)


    def testTrnCat(self):
        """
        Test the Trn methods regarding category access: set_cat(), clear_cat().
        """
        trn = self.trn_a1
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
        trn = self.trn_a2
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
                {"_id", "_idx", "line_num_in_csv",
                 "date", "value", "details",        # from columns dict
                 "cat", "cat_auto", "remark",       # from notes dict
                 "account"})                        # This one is from part B.

        # Positive find by full name.
        self.assertEqual(self.finman_data._expand_fieldname('_id'), '_id')
        self.assertEqual(self.finman_data._expand_fieldname('_idx'), '_idx')
        self.assertEqual(self.finman_data._expand_fieldname('value'), 'value')

        # Positive find by partial name.
        self.assertEqual(self.finman_data._expand_fieldname('val'), 'value')

        # Negative find due to multiple expansions.
        self.assertEqual(self.finman_data._expand_fieldname('_i'), '')

        # Negative find due no expansions.
        self.assertEqual(self.finman_data._expand_fieldname('nonexisting_field'), '')

        # Btw, this function also works for attributes which are not present in all transactions.
        self.assertEqual(self.finman_data._expand_fieldname('account'), 'account')
