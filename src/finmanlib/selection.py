#!/usr/bin/env python3

"""
This module provides class Selection, which is the essential way to access
transactions from a FinmanData object:
- Print the selection.
- Access/modify specific Trn objects.
"""

from collections import namedtuple
import decimal
import logging
import os
import sys
from typing import List, Optional, Tuple, Callable

from finmanlib.datafile import FinmanData, Trn, \
    COL_ID, COL_IDX, COL_MOD, COL_DATE, COL_VALUE, COL_CAT_ALT 



class Selection:
    """
    A selection of transactions.
    """
    SEPARATOR_FIELDS = '|'

    def __init__(self, finman_data: FinmanData, filter_str="", trns=None):
        self.finman_data = finman_data

        if trns is None:
            # Determine filtered set of transactions from 'filter_str'.
            trn_filter = TrnFilter(finman_data, filter_str)
            self.trns = self._get_filtered_trns(finman_data, trn_filter)
            self.filter_str = filter_str

            # Enumerate filtered transactions.
            for idx, trn in enumerate(self.trns, start=1):
                trn._idx = str(idx)

        else:
            # Use set of transactions as provided by 'trn'.
            self.trns = trns
            self.filter_str = ""


    def __repr__(self):
        return f"<Selection '{self.filter_str}' ({len(self.trns)} transactions)>"


    @staticmethod   # TBD: rename, put 'sorted' into function name?
    def _get_filtered_trns(finman_data: FinmanData, trn_filter: 'TrnFilter') -> List[Trn]:
        """
        Get all transactions which match the filter conditions.
        Those conditions have been stored in trn_filter.

        In each contained Trn object, their index in this selection is stored in
        attribute '_idx' (COL_IDX).
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


    def _eval_fields_str(self, fields_str: str) -> Tuple[List[str], List[str]]:
        """
        Evaluate a fields specification.
        """
        FIXED_COLUMN_HEADINGS = {
            COL_IDX: '#',
            COL_MOD: 'mod',
            COL_CAT_ALT: 'cat new'
        }

        field_names = []
        column_headings = []
        max_widths = []
        for field in fields_str.split(self.SEPARATOR_FIELDS):
            # Determine maximum column width, if given in string.
            max_width = None
            if (pos := field.find(':')) >= 0:
                try:
                    max_width = int(field[pos + 1:])
                except ValueError:
                    pass
                field = field[:pos]
            max_widths.append(max_width)

            # Determine field name and column heading.
            field_name = self.finman_data.expand_fieldname(field.strip())
            try:
                column_heading = FIXED_COLUMN_HEADINGS[field_name]
            except KeyError:
                column_heading = field_name
            field_names.append(field_name)
            column_headings.append(column_heading)

        return field_names, column_headings, max_widths


    def print_trns(self,
            fields_str: str,
            subset_str=None,
            index_col=False,
            output_width=None,
            print_csv=False,
            csv_sep=",",
            fh=sys.stdout):
        """
        Print the whole selection of transactions, or a subset thereof.

        fields_str      The fields to print (type: str)
        subset_str      The subset of transactions to print (type: Optional[str])
        index_col       Print index column? (type: bool)
        output_width       Maximum width of formatted output (type: Optional[int])
                        output_width < 0 uses terminal width as maximum width.
        print_csv       Print CSV instead of column format? (type: bool)
        csv_sep         Separator for CSV output (type: str)
        fh              File handle for output
        """

        # Preperations.
        if index_col:
            fields_str = f"{COL_IDX}{self.SEPARATOR_FIELDS}{fields_str}"

        field_names, column_headings, max_widths = self._eval_fields_str(fields_str)

        if not print_csv:
            if output_width is not None and output_width < 0:
                output_width = os.get_terminal_size().columns
            fmt = ColumnFormatter(self.trns, field_names, column_headings, max_widths, output_width)

        # Print header.
        if print_csv:
            header = csv_sep.join(column_headings) + "\n"
        else:
            header = fmt.get_formatted_line(column_headings) + \
                     fmt.get_separator_line()
        fh.write(header)

        # Print data lines.
        invalid_fields = set()
        for trn in self.get_subset(subset_str):

            # Determine column values. Special treatment of "modified"-flag.
            values = []
            for field_name in field_names:
                value = trn.get_field(field_name, invalid_fields)
                if field_name == COL_MOD:
                    value = "*" if value is True else ""
                values.append(value)

            if print_csv:
                line = csv_sep.join(values) + "\n"
            else:
                line = fmt.get_formatted_line(values)
            fh.write(line)

        # Print footer.
        if not print_csv:
            footer = fmt.get_separator_line() + \
                     fmt.get_formatted_line(column_headings)
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
    SEPARATOR_RANGE  = ','

    @classmethod
    def get(cls, subset_str: str, max_len: int) -> List[List]:
        """
        Get reduced set of ranges from string.

        For example:
        '3,5-9,6-11,14-' => [[3,3], [5,11], [14,max_len]]
        """
        ranges = cls.get_ranges(subset_str, max_len)
        return cls.reduce_ranges(ranges)


    @classmethod
    def get_ranges(cls, subset_str: str, max_len: int) -> List[List]:
        """
        Get set of ranges from string.

        For example:
        '3,6-11,5-9,14-' => [[3,3], [6,11], [5,9], [14,max_len]]
        """
        ranges = []
        for range_str in subset_str.split(cls.SEPARATOR_RANGE):
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

    def __init__(self,
            trns: List[Trn],
            field_names: List[str],
            column_headings: List[str],
            max_widths: List[int],
            output_width: Optional[int] = None):
        self.output_width = output_width
        self.col_fmts = self._get_formats(trns, field_names, column_headings, max_widths)


    @classmethod
    def _get_formats(cls,
            trns: List[Trn],
            field_names: List[str],
            column_headings: List[str],
            max_widths: List[int]) -> List[ColumnFormat]:
        """
        Get format (width, alignment) for all columns.
        """
        col_fmts = []
        invalid_fields = set()

        for field_name, column_heading, max_width in zip(field_names, column_headings, max_widths):

            # Loop over all data lines.
            values = [column_heading] + [trn.get_field(field_name, invalid_fields) for trn in trns]
            lengths = [(1 if type(value) is bool else len(value)) for value in values]

            # Create ColumnFormat object.
            width = max(lengths)
            if max_width is not None:
                width = min(width, max_width)
            left_aligned = not (field_name in (COL_VALUE, COL_IDX))
            col_fmts.append(cls.ColumnFormat(width, left_aligned))

        return col_fmts


    def get_formatted_line(self, values: List[str]) -> str:
        """
        Get formatted line for given list of values.
        """
        values_fmt = []
        for fmt, value in zip(self.col_fmts, values):
            value = value[:fmt.width]
            if fmt.left_aligned:
                values_fmt.append(value.ljust(fmt.width))
            else:
                values_fmt.append(value.rjust(fmt.width))

        line = " │ ".join(values_fmt)
        if self.output_width is not None:
            return line[:self.output_width] + "\n"
        else:
            return line + "\n"


    def get_separator_line(self) -> str:
        """
        Get the line separating header from data lines.
        """
        fillers = ('─' * fmt.width for fmt in self.col_fmts)
        line = "─┼─".join(fillers)
        if self.output_width is not None:
            return line[:self.output_width] + "\n"
        else:
            return line + "\n"



class TrnFilter:
    """
    A filter which determines whether a given transaction matches certain
    conditions.
    """
    SEPARATOR_COND   = '|'

    FilterCond = namedtuple('FilterCond', 'field op value')

    def __init__(self, finman_data, filter_str=""):
        self.filter_conds = self._get_filter_conds(finman_data, filter_str)


    @classmethod
    def _get_filter_conds(cls,
            finman_data: FinmanData,
            filter_str="") -> List[FilterCond]:
        """
        Get the filter conditions from given string.
        """
        operators = ('<=', '>=', '<', '>', '=~', '=')

        filter_conds = []
        for cond_str in filter_str.split(cls.SEPARATOR_COND):
            if cond_str == "":
                continue    # Ignoring empty conditions.

            for op in operators:

                # Split condition in field/operator/value.
                p = cond_str.find(op)
                if p < 0:
                    # Not the correct operator.
                    continue
                field, value = cond_str[:p], cond_str[p + len(op):]
                field = field.strip()
                value = value.strip()

                # Check for empty fields.
                if field == "":
                    logging.warning(f"No field in condition '{cond_str}'; ignoring.")
                    break
                if value == "":
                    logging.warning(f"No value in condition '{cond_str}'; ignoring.")
                    break

                # Expand field name.
                field_exp = finman_data.expand_fieldname(field)
                if field_exp == "":
                    logging.warning(f"No expansion for field '{field}'; ignoring.")
                    break
                field = field_exp

                # Unquote value.
                if len(value) >= 2:
                    if (value[0] == '"' and value[-1] == '"') or \
                       (value[0] == "'" and value[-1] == "'"):
                        value = value[1:-1]

                # In case of "contains" operator: prepare for case-insensitive comparison.
                if op == '=~':
                    op = "contains"
                    value = value.upper()

                # The text operator 'contains' does not make much sense on numerical values...
                if op == "contains":
                    if field in (COL_ID, COL_IDX, COL_VALUE):
                        logging.warning(f"Invalid condition: operator '{op}' and field '{field}'; ignoring.")
                        break

                # while the numeric operators do not make much sense on text values.
                else:
                    if field not in (COL_ID, COL_IDX, COL_DATE, COL_VALUE):
                        logging.info(f"Unusual condition: operator '{op}' and field '{field}'.")

                # Some fields do not contain text but numbers.
                if field in (COL_ID, COL_IDX):
                    value = int(value)
                elif field == COL_VALUE:
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
        invalid_fields = set()
        for fc in self.filter_conds:

            if fc.op == 'contains':
                # Search for sub-string.
                value = trn.get_field(fc.field, invalid_fields).upper()
                if not (value.find(fc.value) >= 0):
                    return False
            else:
                value = trn.get_field(fc.field, invalid_fields)
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
