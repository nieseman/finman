#!/usr/bin/env python3

"""
Tests of file selection.py.
"""

import decimal
import io
import logging
import textwrap
import unittest

from test_base import TestWithSampleJsonFiles
from finmanlib.selection import *



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
        self.finman_data = FinmanData((self.jsonl_filename1, self.jsonl_filename2))


    def testSelection(self):
        """
        Test class Selection.

        Test this by checking the output of the print() function. This
        implicitly tests class ColumnFormatter.
        """

        def check(fields_str: str, filter_str: str, output_expected: str):
            sel = Selection(self.finman_data, filter_str)
            out = io.StringIO()
            sel.print_trns(fields_str, index_col=True, fh=out)

            output = out.getvalue()
            if output_expected[0] == "\n":
                output_expected = output_expected[1:]
            output_expected = textwrap.dedent(output_expected)

            self.assertEqual(output, output_expected)

        fields_str = "date|details|value|cat|rem"
        check(fields_str, filter_str="", output_expected=OUTPUT_1)


    def testRanges(self):
        """
        Test class Ranges.
        """
        max_len = 18

        def check(subset_str: str, ranges_expected: List[List]):
            ranges = Ranges.get(subset_str, max_len)
            self.assertEqual(ranges, ranges_expected)

        #
        # Positive tests.
        #

        # Simple tests.
        check("5-9",            [[5,9]])
        check("5",              [[5,5]])
        check("5-",             [[5,18]])

        # Consecutive ranges.
        check("5-9,11-18",      [[5,9], [11,18]])

        # Two adjacent ranges.
        check("5-9,10-18",      [[5,18]])

        # Two overlapping ranges.
        check("5-9,9-18",       [[5,18]])
        check("5-9,8-18",       [[5,18]])

        #
        # Ignored ranges.
        #
        check("",               [])
        check("-5",             [])
        check("a",              [])
        check("a-",             [])
        check("-b",             [])
        check("a-b",            [])
        check("3-b",            [])
        check("a-3",            [])
        check("5-9-11",         [])
        check("5-9,9-a",        [[5,9]])
        check("a-b,5-9,8-c,11-18,e-22",  [[5,9], [11,18]])

        #
        # Combined test.
        #
        check("3,5-9,6-11,14-", [[3,3], [5,11], [14,18]])


    def testTrnFilter(self):
        """
        TBD
        """
        FC = TrnFilter.FilterCond
        Dec = decimal.Decimal

        def check(filter_str: str, filter_conds: List[FC]):
            trn_filter = TrnFilter(self.finman_data.expand_fieldname, filter_str)
            self.assertEqual(trn_filter.filter_conds, filter_conds)

        #
        # Positive test.
        #

        # Single condition field/operator/value.
        check("details=abc",        [FC("details", "=", "abc")])

        # Spaces are stripped.
        check(" details =    abc ", [FC("details", "=", "abc")])

        # Fields are expanded.
        check("det=abc",            [FC("details", "=", "abc")])

        # Values are unquoted, but only if enclosed (i.e. at the beginning and
        # end of value).
        check("det='abc'",          [FC("details", "=", "abc")])
        check("det='abc",           [FC("details", "=", "'abc")])

        # Test all operators.
        # Operators >, >=, <, <= on text field 'details' are unusual but valid.
        check("details>=abc",       [FC("details",  ">=", "abc")])
        check("details<=abc",       [FC("details",  "<=", "abc")])
        check("details>abc",        [FC("details",  ">",  "abc")])
        check("details<abc",        [FC("details",  "<",  "abc")])
        check("details=abc",        [FC("details",  "=",  "abc")])
        check("details=~abc",       [FC("details",  "contains", "ABC")])

        # For conditions on certain fields, values are converted to numerical format. 
        check("_id=3",              [FC("_id",   "=", 3)])
        check("_idx=3",             [FC("_idx",  "=", 3)])
        check("value=3",            [FC("value", "=", Dec('3'))])
        check("value=3.254",        [FC("value", "=", Dec('3.254'))])

        # Test multiple conditions
        check("details=~abc|date>=2005-07-01", [
                FC("details", "contains", "ABC"),
                FC("date",    ">=",       "2005-07-01")
        ])


        #
        # Ignored conditions.
        #

        # Badly formatted conditions are ignored.
        check("details=abc",        [FC("details", "=", "abc")])
        check("details_abc",        [])
        check("details=",           [])
        check("details",            [])
        check("=abc",               [])
        check("=",                  [])
        check("",                   [])

        # Conditions with fields that cannot be expanded are ignored.
        check("detailss=abc",       [])
        check("detals=abc",         [])
        check("xx=abc",             [])

        # Text operator conditions on numerical columns are ignored.
        check("_id=~abc",           [])
        check("_idx=~abc",          [])
        check("value=~abc",         [])


        #
        # Combined test.
        #
        check("date>=2005-07-01|dat<2006-01-01|val>30.65|_id>10|det=~debt", [
                FC("date",      ">=",       "2005-07-01"),
                FC("date",      "<",        "2006-01-01"),
                FC("value",     ">",        Dec("30.65")),
                FC("_id",       ">",        10),
                FC("details",   "contains", "DEBT")
        ])



OUTPUT_1 = """
     # │ date       │ details       │   value │ cat       │ remark
    ───┼────────────┼───────────────┼─────────┼───────────┼───────
     1 │ 1972-07-10 │ Transfer 1a-1 │ +100.78 │ transfers │       
     2 │ 1972-07-20 │ Transfer 1a-2 │ +200.78 │           │ abc   
     3 │ 1972-07-30 │ Transfer 1a-3 │ +300.78 │           │       
     4 │ 1972-08-05 │ Transfer 1b-1 │ +100.55 │           │       
     5 │ 1973-01-11 │ Transfer 2-11 │  +11.00 │           │       
     6 │ 1973-01-12 │ Transfer 2-12 │  +11.00 │           │       
     7 │ 1973-01-13 │ Transfer 2-13 │  +11.00 │           │       
     8 │ 1973-01-14 │ Transfer 2-14 │  +11.00 │           │       
     9 │ 1973-01-15 │ Transfer 2-15 │  +11.00 │           │       
    10 │ 1973-01-16 │ Transfer 2-16 │  +11.00 │           │       
    11 │ 1973-01-17 │ Transfer 2-17 │  +11.00 │           │       
    12 │ 1973-01-18 │ Transfer 2-18 │  +11.00 │           │       
    13 │ 1973-01-19 │ Transfer 2-19 │  +11.00 │           │       
    14 │ 1973-01-20 │ Transfer 2-20 │  +11.00 │           │       
    15 │ 1973-01-21 │ Transfer 2-21 │  +11.00 │           │       
    16 │ 1973-01-22 │ Transfer 2-22 │  +11.00 │           │       
    ───┼────────────┼───────────────┼─────────┼───────────┼───────
     # │ date       │ details       │   value │ cat       │ remark
"""



if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    unittest.main()
