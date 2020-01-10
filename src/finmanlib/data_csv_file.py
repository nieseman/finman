#!/usr/bin/env python3

import copy
import decimal
import hashlib
import itertools
import os
from typing import List, Tuple, Dict, Iterator

from .error import Error
from .data_base_element import DataBaseElement
from .data_transaction import Transaction
from .formatter import Formatter



class CsvFile(DataBaseElement):
    """
        Content description of an actual CSV file. Also provides CSV importing.

        Front-end methods:
        * import_data()
    """

    _defaults = {
        'basename': "",
        'path': "",
        'size': -1,
        'sha1': "",
        'format': "",
        'currency': "",
        'columns': {
            'date': "",
            'value': ""
        },
        'header_full': "",
        'header_columns': "",
        'bank_account': "",
        'date_start': "",
        'date_end': "",
        'date_first': "",
        'date_last': "",
        'value_start': "",
        'value_end': "",
        'value_diff': "",
        'num_lines': -1,
        'num_transactions': -1,
        'num_imported': -1,
        'comments': []
    }

    _incomplete_subdicts = ('columns', )


    def import_data(self, 
                    filename: str,
                    csv_format_name: str,
                    csv_format: str) -> Tuple[List[str], List[Transaction]]:
        """
            Read, process and deliver from a CSV transactions file.
        """

        # Note: If an error occurs, fields may remain in an inconsistent state.

        fmt = csv_format.format
        self.format = csv_format_name
        self.currency = fmt['currency']
        Formatter.currency = self.currency
        Formatter.format_date = fmt['date']
        Formatter.replace_comma_with_point = fmt['header']['value_replace_comma_with_point']
        self.columns = copy.deepcopy(csv_format.columns)

        num_header_lines = fmt['header']['num_lines']
        lines = self._read_csv(filename, fmt['encoding'])
        lines_header = lines[:num_header_lines]
        lines_data = itertools.islice(lines, num_header_lines, None)
        self.header_columns = lines_header[fmt['header']['line_with_column_names'] - 1]
        self.header_full = "\n".join(lines_header)

        separator = fmt['separator']
        Formatter.remove_points = fmt['header']['value_remove_points']
        Formatter.replace_comma_with_point = fmt['header']['value_replace_comma_with_point']
        self._evaluate_header(lines_header, separator, csv_format.descriptors_in_header)

        col_idx = self._get_column_indices(separator, csv_format.columns)
        Formatter.remove_points = fmt['data_lines']['value_remove_points']
        Formatter.replace_comma_with_point = fmt['data_lines']['value_replace_comma_with_point']
        trns = self._evaluate_data_lines(lines_data, separator, col_idx, fmt['header']['num_lines'])

        # TBD: Problems in here!!
        self._complete_date_and_value_fields(trns)

        columns = list(csv_format.columns.keys())
        return columns, trns


    def _read_csv(self, filename: str, encoding: str) -> List[str]:
        """
            Read CSV file, and store file-related information in object
            members.
        """
        # TBD: use deque instead of list!
            
        try:
            csv_data = open(filename, 'rb').read()
        except:
            Error(f"Cannot read CSV file '{filename}'.")

        self.basename = os.path.basename(filename)
        self.path = filename
        self.size = len(csv_data)
        self.sha1 = hashlib.sha1(csv_data).hexdigest()

        lines = csv_data.decode(encoding).split("\n")
        self.num_lines = len(lines)

        return lines


    # Evaluate header.
    def _evaluate_header(self, lines: List[str], separator: str, descriptors_in_header: dict):
        """
            Evaluate header of CSV file, and store file-related information
            in object members. No conversion/adjustment is made yet on these
            values.
        """
        for field_name, indices in descriptors_in_header.items():
            if indices:
                if len(indices) == 2:
                    line_num, column_num, part_num = *indices, None
                elif len(indices) == 3:
                    line_num, column_num, part_num = indices
                else:
                    Error(f"Header descriptor '{field_name}' must be a list "
                            "with two or three members.")

                line = lines[line_num - 1]
                column = line.split(separator)[column_num - 1]
                column = Formatter.unquote(column)
                if part_num:
                    part = column.split()[part_num - 1]
                else:
                    part = column

                self.__dict__[field_name] = part



    def _complete_date_and_value_fields(self, trns):
#       print("___")
#       print(self.value_start)
#       print(self.value_end)
        if self.value_start:
            self.value_start = Formatter.value(self.value_start)
        if self.value_end:
            self.value_end = Formatter.value(self.value_end)
        if self.date_start:
            self.date_start = Formatter.date(self.date_start)
        if self.date_end:
            self.date_end = Formatter.date(self.date_end)

        dec = decimal.Decimal
        # Do some more evaluations:
        self.date_first = min(t.from_source['date'] for t in trns)
        self.date_last  = max(t.from_source['date'] for t in trns)
        for t in trns:
            v = t.from_source['value']
#           print(".....")
#           print(v)
#           print(dec(v))
        self.value_diff = Formatter.value(sum(dec(t.from_source['value']) for t in trns))

#       print("___")
#       print(self.value_start)
#       print(self.value_end)
#       print(self.value_diff)
        if self.value_start and self.value_end:
            if dec(self.value_end) - dec(self.value_begin) != dec(self.value_diff):
                Warning(f"Start/end value mismatch in file {self.basename}: "
                         "{self.value_end} - {self.value_begin} != {self.value_diff}")

        elif self.value_start and not self.value_end:
            self.value_end = Formatter.value(dec(self.value_begin) + dec(self.value_diff))

        elif not self.value_start and self.value_end:
            self.value_start = Formatter.value(dec(self.value_end) - dec(self.value_diff))


    def _get_column_indices(self, separator: str, columns: Dict[str, str]):
        col_names = [Formatter.unquote(s) for s in self.header_columns.split(separator)]

        col_idx = {}
        for field_name_in_json, col_name_in_csv in columns.items():
            for idx, col_name in enumerate(col_names):
                if col_name == col_name_in_csv:
                    col_idx[field_name_in_json] = idx
                    break
            else:
                Error(f"Column '{col_name_in_csv}' not found in CSV file '{filename}'.")

        return col_idx


    # Process CSV data lines.
    def _evaluate_data_lines(self,
            lines: Iterator[str],
            separator: str,
            col_idx: Dict[int, int],
            line_offset: int) -> List[Transaction]:
        trns = []
        for line_num, line in enumerate(lines, 1):

            columns = [Formatter.unquote(s) for s in line.split(separator)]
            src = {
                'account': "",
                'date': "",
                'value': ""
            }
            for field_name, idx in col_idx.items():
                src[field_name] = columns[idx]
            src['value'] = Formatter.value(src['value'])
            src['date'] = Formatter.date(src['date'])
            if src['account'] == "":
                src['account'] = self.bank_account
            trn = {
                'id': hashlib.sha1(line.encode()).hexdigest()[:7],
                'source': {
                    'filename': self.basename,
                    'linenum': line_num + line_offset,
                    'line': line
                },
                'from_source': src,
                'category': "",
                'remark': "",
                'flags': ""
            }

            trns.append(Transaction(trn))

        self.num_transactions = len(trns)

        return trns
