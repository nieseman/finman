#!/usr/bin/env python3

"""
This module provides class Selection, which is the essential way to access
transactions from a FinmanData object:
- Print the selection.
- Access/modify specific Trn objects.
"""

from collections import namedtuple
import logging
import os
import sys
from typing import List, Optional

from finmanlib.datafile import FinmanData, Trn


# Separator used in field_str and filter_str variables
SEPARATOR = '|'

# The value column with this name is treated special.
COL_VALUE = 'value'



class Selection:
    """
    A selection of transactions.
    """

    def __init__(self, finman_data: FinmanData, filter_str=""):
        trn_filter = TrnFilter(finman_data._expand_fieldname, filter_str)

        self.trns = self._get_filtered_trns(finman_data, trn_filter)
        self.expand_fieldname = finman_data._expand_fieldname
        self.filter_str = filter_str

        # Enumerate filtered transactions.
        for idx, trn in enumerate(self.trns, start=1):
            trn._idx = str(idx)


    def __repr__(self):
        return f"<Selection '{self.filter_str}' ({len(self.trns)} transactions)>"


    @staticmethod   # TBD: rename, put 'sorted' into function name?
    def _get_filtered_trns(finman_data: FinmanData, trn_filter: 'TrnFilter') -> List[Trn]:
        """
        Get all transactions which match the filter conditions.
        Those conditions have been stored in trn_filter.

        In each contained Trn object, their index in this selection is stored in
        attribute '_idx'.
        """

        # Determine filtered transactions.
        trns = []
        for jsonl in finman_data.jsonl_files:
            for trns_set in jsonl.trns_sets:
                for trn in trns_set.trns:
                    if trn_filter.match(trn):
                        trns.append(trn)

        # TBD: sorting.


        return trns


    def print(self,
            fields_str: str,
            subset_str=None,
            index_col=False,
            max_width=None,
            print_csv=False,
            csv_sep=",",
            fh=sys.stdout):
        """
        Print the whole selection of transactions, or a subset thereof.

        fields_str      The fields to print (type: str)
        subset_str      The subset of transactions to print (type: Optional[str])
        index_col       Print index column? (type: bool)
        max_width       Maximum width of formatted output (type: Optional[int])
                        max_width < 0 uses terminal width as maximum width.
        print_csv       Print CSV instead of column format? (type: bool)
        csv_sep         Separator for CSV output (type: str)
        fh              File handle for output
        """
        # Preperations.
        fields = [self.expand_fieldname(field.strip())
                    for field in fields_str.split(SEPARATOR)]
        column_headers = fields[:]
        if index_col:
            fields = ["_idx"] + fields
            column_headers = ["#"] + column_headers
        if not print_csv:
            if max_width is not None and max_width < 0:
                max_width = os.get_terminal_size().columns
            fmt = ColumnFormatter(self.trns, fields, max_width)

        # Print header.
        if print_csv:
            header = csv_sep.join(column_headers) + "\n"
        else:
            header = fmt.get_formatted_line(column_headers) + \
                     fmt.get_separator_line()
        fh.write(header)

        # Print data lines.
        for trn in self.get_subset(subset_str):
            values = [trn.get_field(field) for field in fields]
            if print_csv:
                line = csv_sep.join(values) + "\n"
            else:
                line = fmt.get_formatted_line(values)
            fh.write(line)

        # Print footer.
        if not print_csv:
            footer = fmt.get_separator_line() + \
                     fmt.get_formatted_line(column_headers)
        fh.write(footer)


    def get_subset(self, subset_str: Optional[str] = None) -> List[Trn]:
        """
        Get a subset of the selection, as specified by subset_str.
        """
        if subset_str is None:
            return self.trns[:]
        else:
            trns = []
            for rng in Ranges.get(subset_str, len(self.trns)):
                rng_min, rng_max = rng
                if rng_max == None:
                    trns += self.trns[rng_min - 1:]
                else:
                    trns += self.trns[rng_min - 1:rng_max]
            return trns



class Ranges:
    """
    Determine a list of range specifications from a specifier string.
    """

    @classmethod
    def get(cls, subset_str: str, max_len: int) -> List[List]:
        """
        Get reduced set of ranges from string.

        For example:
        '3,5-9,6-11,14-' => [[3,3], [5,11], [14,max_len]]
        """
        ranges = cls.get_ranges(subset_str, max_len)
        return cls.reduce_ranges(ranges)


    def get_ranges(subset_str: str, max_len: int) -> List[List]:
        """
        Get set of ranges from string.

        For example:
        '3,6-11,5-9,14-' => [[3,3], [6,11], [5,9], [14,max_len]]
        """
        ranges = []
        for range_str in subset_str.split(','):
            range_str = range_str.strip()
            if range_str == "":
                continue    # Ignore empty range.

            # Determine upper and lower bound of range.
            parts = [s.strip() for s in range_str.split('-')]
            if len(parts) == 1:
                rng_min, rng_max = parts[0], parts[0]
            elif len(parts) == 2:
                if parts[1] == "":
                    rng_min, rng_max = parts[0], max_len
                else:
                    rng_min, rng_max = parts[0], parts[1]
            else:
                logging.info(f"Range string '{range_str}' has {len(parts)} parts; ignoring.")
                continue

            # Convert bounds to integer.
            try:
                rng_min = int(rng_min)
                rng_max = int(rng_max)
            except ValueError:
                logging.info(f"No integer range: {rng_min}-{rng_max}.")
                continue

            # Store range.
            ranges.append([rng_min, rng_max])

        return ranges


    def reduce_ranges(ranges: List[List]) -> List[List]:
        """
        Reduce a set of ranges.

        For example:
        [[3,3], [6,11], [5,9], [14,max_len]] => [[3,3], [5,11], [14,max_len]]
        """
        # Anything to do?
        if len(ranges) == 0:
            return []

        # Sort input ranges.
        assert all(len(range) == 2 for range in ranges), "Bad ranges list"
        ranges.sort(key=lambda rng: rng[1])
        ranges.sort(key=lambda rng: rng[0])

        # Loop over all ranges.
        ranges_new = [ranges[0]]
        for rng in ranges[1:]:
            rng_prev = ranges_new[-1]

            # If that previous range extends to the end, we are done.
            if rng_prev[1] is None:
                break

            if rng[0] > rng_prev[1] + 1:
                # Next range is separate (i.e. does not overlap with previous
                # range, and is not directly consecutive) => add that range.
                ranges_new.append(rng)
            else:
                # Next range does overlap with previous range, or is directly
                # consecutive) => extend previous range.
                rng_prev[1] = rng[1]

        return ranges_new



class ColumnFormatter:
    """
    Provide formatted tabular output of values.
    """

    ColumnFormat = namedtuple('ColumnFormat', 'width left_aligned')

    def __init__(self, trns: List[Trn], fields: List[str], max_width: Optional[int] = None):
        self.max_width = max_width
        self.col_fmts = self._get_formats(trns, fields)


    @classmethod
    def _get_formats(cls, trns: List[Trn], fields: List[str]) -> List[ColumnFormat]:
        """
        Get format (width, alignment) for all columns.
        """
        col_fmts = []
        # TBD: Allow syntax for like 'date,descr:40,value'.

        for field in fields:
            max_len = max((len(trn.get_field(field)) for trn in trns), default=1)
            if field != '_idx':
                max_len = max(max_len, len(field))
            left_aligned = not (field in (COL_VALUE, '_idx'))
            col_fmts.append(cls.ColumnFormat(
                        width=max_len,
                        left_aligned=left_aligned))

        return col_fmts


    def get_formatted_line(self, values: List[str]) -> str:
        """
        Get formatted line for given list of values.
        """
        values_fmt = []
        for fmt, value in zip(self.col_fmts, values):
            if fmt.left_aligned:
                values_fmt.append(value.ljust(fmt.width))
            else:
                values_fmt.append(value.rjust(fmt.width))

        line = " │ ".join(values_fmt)
        if self.max_width is not None:
            return line[:self.max_width] + "\n"
        else:
            return line + "\n"


    def get_separator_line(self) -> str:
        """
        Get the line separating header from data lines.
        """
        fillers = ('─' * fmt.width for fmt in self.col_fmts)
        line = "─┼─".join(fillers)
        if self.max_width is not None:
            return line[:self.max_width] + "\n"
        else:
            return line + "\n"



class TrnFilter:
    """
    A filter which determines whether a given transaction matches certain
    conditions.
    """

    FilterCond = namedtuple('FilterCond', 'field op value')

    def __init__(self, expand_fieldname, filter_str=""):
        self.filter_conds = self._get_filter_conds(expand_fieldname, filter_str)


    @classmethod
    def _get_filter_conds(cls, expand_fieldname, filter_str="") -> List[FilterCond]:
        """
        Get the filter conditions from given string.
        """
        operators = ('<=', '>=', '<', '>', '=')

        filter_conds = []
        for cond_str in filter_str.split(SEPARATOR):
            if cond_str == "":
                continue    # Ignoring empty conditions.

            for op in operators:
                p = cond_str.find(op)
                if p >= 0:
                    field, value = cond_str[:p], cond_str[p + len(op):]
                    if field == '':
                        logging.warning(f"No field in condition '{cond_str}'; ignoring.")
                        break
                    # TBD: unquote value?
                    field = expand_fieldname(field)

                    if op == '=':
                        # Operator '=' is understood
                        # as 'exact-equal' for field COL_VALUE, but 
                        # as 'contains' for other fields.
                        if field != COL_VALUE:
                            op = 'contains'
                            value = value.lower()
                    else:
                        # The other operators (for value comparison) only make
                        # sense for field COL_VALUE.
                        if field != COL_VALUE:
                            logging.warning(f"Operator '{op}' not valid for field '{field}'; ignoring.")
                            break
                        value = decimal.Decimal(value)

                    # Valid condition; store it.
                    filter_conds.append(cls.FilterCond(field, op, value))
                    break

            else:
                logging.warning(f"No valid operator in condition '{cond_str}'; ignoring.")

        return filter_conds


    def match(self, trn: Trn) -> bool:
        """
        Check if given transaction matches the conditions.

        Return False on any failed condition; or True otherwise.
        """
        for fc in self.filter_conds:

            if fc.op == 'contains':
                # Search for sub-string.
                value = trn.get_field(fc.field).lower()
                if not (value.find(fc.value) >= 0):
                    return False
            else:
                value = trn.get_field(fc.field)
                if fc.field == COL_VALUE:
                    # Column COL_VALUE contains decimal numbers.
                    value = decimal.Decimal(value)

                if fc.op == '<':
                    if not (value < fc.value):
                        return False
                elif fc.op == '<=':
                    if not (value <= fc.value):
                        return False
                elif fc.op == '>':
                    if not (value > fc.value):
                        return False
                elif fc.op == '>=':
                    if not (value >= fc.value):
                        return False
                elif fc.op == '=':
                    if not (value == fc.value):
                        return False
                else:
                    assert False, f"Invalid comparison operator '{op}'."

        return True
