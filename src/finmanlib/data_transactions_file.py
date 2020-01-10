#!/usr/bin/env python3

"""

Fixed names:

- For each transaction, the fields 'date' and 'value' are expected.
- In filter and column strings, all fields of a transaction as well as the
  description fields 'category' and 'remark' can be used.

"""

import copy
import decimal
import json
import os
from typing import Optional

from .data_base_element import DataBaseElement
from .data_transaction import Transaction
from .data_csv_format import CsvFormat
from .data_csv_file import CsvFile
from .error import FinmanError, Error


file_kind_id = "finman-transactions-file-v1"
cat_sep = ' ▶ '


class TransactionsFile(DataBaseElement):
    """
        Manage the data in a Finman JSON transactions file.
    """

    _defaults = {
        "filekind": file_kind_id,
        "comments": [],
        "categories": {},
        "csv_formats": {},
        "csv_source_files": {},
        "columns": [],
        "transactions": []
    }

    _ignore_subdicts = ("categories", "csv_formats", "csv_source_files")


    def __init__(self, filename: str):
        super().__init__()
        self._filename = filename
        self._modified = False


    def modified(self, val: Optional[bool] = None) -> Optional[bool]:
        if val is None:
            return self._modified
        else:
            self._modified = val


    def check_structure(self):

        def check_dict(d, value_type):
            for key, value in d.items():
                if type(key) is not str:
                    Error("TBD_05")
                if type(value) is not value_type:
                    Error("TBD_06")
                if isinstance(value, DataBaseElement):
                    value.check_structure()

        def check_list(l, value_type):
            for el in l:
                if type(el) is not value_type:
                    Error("TBD_08")
                if isinstance(el, DataBaseElement):
                    el.check_structure()

        super().check_structure()

        check_dict(self.csv_formats, CsvFormat)
        check_dict(self.csv_source_files, CsvFile)
        check_list(self.transactions, Transaction)
        check_list(self.columns, str)

        mandatory_trn_fields = tuple(Transaction._defaults['from_source'].keys())
        if self.csv_source_files:
            for field in mandatory_trn_fields:
                if field not in self.columns:
                    Error(f"Mandatory field '{field}' not listed in 'columns'.")


    def load(self):
        try:
            _filename = self._filename
            self.__dict__ = json.load(open(self._filename))
            self._filename = _filename
            self.modified(False)

            # Replace sub-dicts/lists with respective objects.
            self.csv_formats = {key: CsvFormat(value) \
                    for key, value in self.csv_formats.items()}
            self.csv_source_files = {key: CsvFile(value) \
                    for key, value in self.csv_source_files.items()}
            self.transactions = [Transaction(trn) \
                    for idx, trn in enumerate(self.transactions)]

        except json.JSONDecodeError as e:
            Error("Cannot parse JSON text:\n%s" % e.msg)
        except:
            Error(f"Cannot read JSON file '{self._filename}'.")

        try:
            self.check_structure()
        except FinmanError as e:
            raise FinmanError(f"Structure mismatch in JSON file '{self._filename}': {e}")


    def save(self):
        self.check_structure()
        text = json.dumps(self, indent = 4, ensure_ascii = False,
                default = lambda x: {key: value for key, value in x.__dict__.items() if not key.startswith('_')})
                    # TBD: omit private fields
        try:
            open(self._filename, 'w').write(text)
            self.modified(False)
        except:
            Error(f"Cannot write file '{self._filename}'.")


    def expand_field_name(self, field_part: str) -> str:
        # TBD: make things nicer here.
        available_fields = ('index', 'category', 'remark') + tuple(self.columns)

        for field_in_json in available_fields:
            if field_in_json.startswith(field_part):
                return field_in_json

        for field_in_json in available_fields:
            if field_in_json.find(field_part) >= 0:
                return field_in_json

        if self.columns:
            valid_fields = f"Valid fields are: {', '.join(self.columns)}."
        else:
            valid_fields = "No transaction fields in Finman file."
        Error(f"Cannot resolve field '{field_part}'. {valid_fields}")


    def evaluate_category_filters(self):

        def evaluate_filters(categories, cat_path):
            nonlocal assignments

            # 'categories' contains a sub-dict of categories.
            if type(categories) is dict:
                for cat, subcat in categories.items():
                    evaluate_filters(subcat, cat_path + [cat])

            # 'categories' contains a list of filter commands as strings.
            elif type(categories) is list:
                cat_str = cat_sep.join(cat_path)
                for filter_str in categories:
                    for t in self.get_filtered_transactions(filter_str):
                        assignments.append((t.id, cat_str))

            else:
                assert(False)

        assignments = []
        evaluate_filters(self.categories, [])
        return assignments


    def get_category_strings(self, filter = None):

        def iterate_dict(d, cat_str):
            if type(d) is not dict:
                return
            for key, value in d.items():
                if cat_str:
                    new_cat_str = cat_str + cat_sep + key
                else:
                    new_cat_str = key
                if not filter or new_cat_str.lower().find(filter) >= 0:
                    yield new_cat_str

                for s in iterate_dict(value, new_cat_str):
                    yield s
    
        if filter:
            filter = filter.lower()
        for s in iterate_dict(self.categories, ""):
            yield s
