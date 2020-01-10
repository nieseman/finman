#!/usr/bin/env python3

import decimal
from typing import Optional, Union, Tuple, List, Generator


CSV_SEPARATOR = ";"


class Formatter:
    """
        Provide all text formatting for the Finman program
    """

    remove_points = True
    replace_comma_with_point = True
    format_date = "DD.MM.YYYY"
    currency = "EUR"

    @staticmethod
    def unquote(s: str) -> str:
        """
            Remove quotes from a string.
        """
        if type(s) is not str:
            return s
        if len(s) >= 2 and \
           ((s[0] == "'" and s[-1] == "'") or \
            (s[0] == '"' and s[-1] == '"')):
            return s[1:-1]
        else:
            return s


    @classmethod
    def date(cls, s: str) -> str:
        """
            Return a given date in standard format.
        """
        if cls.format_date == "DD.MM.YYYY":
            return "%s-%s-%s" % (s[6:10], s[3:5], s[0:2])
        else:
            assert(False)


    @classmethod
    def value(cls, val: Union[str, int, decimal.Decimal]) -> str:
        """
            Return a given money value in standard format.
        """
        if type(val) == str:
            if val.endswith(cls.currency):
                val = val[:-len(cls.currency)]
            val = val.strip()
            if cls.remove_points:
                val = val.replace('.', '')
            if cls.replace_comma_with_point:
                val = val.replace(',', '.')
        elif type(val) in (int, decimal.Decimal):
            val = str(val)
        else:
            assert(False)   # TBD

        if val and val[0] != '-':
            val = "+" + val
        return val


    @classmethod
    def csv_rows(cls,
            subset: "TransactionsSubset",
            fields: List[str],
            numbered: bool = False) \
                -> Generator[str, None, None]:
        """
            Deliver given transactions in CSV format.
        """
        # TBD: Quoting of some characters? semicolon?

        for line in subset.get_data_rows(fields, numbered):
            yield CSV_SEPARATOR.join(col for col in row)


    @classmethod
    def table_rows(cls,
            subset: "TransactionsSubset",
            fields: List[str],
            widths: List[int],
            numbered: bool = False) \
                -> Generator[str, None, None]:
        """
            Deliver given transactions in tabular text format.
        """
        # Obtain the data to print.
        data_lines = list(subset.get_data_rows(fields, numbered))
        if numbered:
            fields = ["#"] + fields
            widths = [None] + widths

        # Determine widths which were specified only as 'None'.
        for idx, width in enumerate(widths):
            if width is None:
                if data_lines:
                    col_width = max(len(line[idx]) for line in data_lines)
                else:
                    col_width = 0
                widths[idx] = col_width

        # Determine whether the 'value' column is among the fields.
        for idx, field in enumerate(fields):
            if field == 'value':
                value_idx = idx
                break
        else:
            value_idx = None

        # If yes, calculate sum of entries, and adjust width of column 'value'.
        if value_idx:
            sum = decimal.Decimal(0.0)
            first_line = True
            for line in data_lines:
                if first_line:
                    first_line = False
                    continue
                sum += decimal.Decimal(line[value_idx])
            sum_str = Formatter.value(sum)

            widths[value_idx] = max(widths[value_idx], len(sum_str))

        # Construct format string.
        sep_header = "─┼─"
        separator_line = sep_header.join("─" * width for width in widths)
        sep_data = " │ "
        fmt_str = ""
        for idx, (field, width) in enumerate(zip(fields, widths)):
            if fmt_str != "":
                fmt_str += sep_data
            if field == 'value':
                fmt_str += "%" + str(width) + "s"
            else:
                fmt_str += "%-" + str(width) + "s"

        # Provide header, data rows, and footer with sum of values.
        header_line = fmt_str % tuple(fields)
        yield header_line
        yield separator_line
        first_line = True

        # Provide data rows.
        for line in data_lines:
            if first_line:
                first_line = False
                continue
            if value_idx:
                sum += decimal.Decimal(line[value_idx])
            yield fmt_str % tuple(col[:width] for col, width in zip(line, widths))

        # Provide footer with sum of values.
        if value_idx:
            bottom_columns = [""] * len(fields)
            bottom_columns[value_idx] = sum_str
            bottom_line = fmt_str % tuple(bottom_columns)
            yield separator_line
            yield bottom_line
