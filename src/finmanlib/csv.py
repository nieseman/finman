#!/usr/bin/env python3

import datetime
import hashlib
from typing import List, Tuple, Dict

from finmanlib.datafile import Trn, TrnsSet, SourceFileInfo, TrnsSetHeader



class CsvFmt:
    """
    Format description of one kind of CSV source file.
    """

    def __init__(self, **kwargs):
        # Default values.
        self.name                   = ""
        self.comment                = ""
        self.encoding               = "utf-8"
        self.separator              = ";"
        self.currency               = "EUR"
        self.num_header_lines       = 0
        self.line_with_column_names = 0
        self.fmt_date               = "YYYY-MM-DD"
        self.fmt_value              = "x,xxx.yy"
        self.columns                = {}
        
        # Store provided information.
        for key, value in kwargs.items():
            assert key in vars(self), f"Wrong field in CsvFmt: '{key}'"
            setattr(self, key, value)

        # Adjust format patterns.
        self.fmt_date = self.fmt_date.upper().replace('.', '/').replace('-', '/')
        self.fmt_value = self.fmt_value.lower()


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


    @staticmethod
    def conv_date(s: str, fmt_date: str) -> str:
        """
        Convert a given date to standard format.
        """
        assert len(s) == 10, f"Invalid length of date string '{s}'"

        if fmt_date == "DD/MM/YYYY":
            dd, mm, yyyy = s[0:2], s[3:5], s[6:10]
        elif fmt_date == "MM/DD/YYYY":
            mm, dd, yyyy = s[0:2], s[3:5], s[6:10]
        elif fmt_date == "YYYY/MM/DD":
            yyyy, mm, dd = s[0:4], s[5:7], s[8:10]
        else:
            assert False, f"Invalid date format: '{fmt_date}'"

        return f"{yyyy}-{mm}-{dd}"


    @staticmethod
    def conv_value(s: str, fmt_value: str) -> str:
        """
        Convert a given money value to standard format.
        """
        assert 4 <= len(s) <= 9, f"Invalid length of value string '{s}'"

        if fmt_value == "xxxx.yy":
            pass
        elif fmt_value == "x,xxx.yy":
            s = s.replace(',', '')
        elif fmt_value == "x.xxx,yy":
            s = s.replace('.', '').replace(',', '.')
        else:
            assert False, f"Invalid value format: '{fmt_value}'"

        return f"{float(s):+.2f}"


    def _column_mapping(self, lines_header: List[str]) -> Dict[str, int]:
        """
        Obtain a name-to-column-index mapping,
        from the column-header line in the CSV file.
        """
        csv_col_headers_line = lines_header[self.line_with_column_names - 1]
        csv_col_headers = [self.unquote(hdr) for hdr in csv_col_headers_line.split(self.separator)]
        csv_col_headers = [self.unquote(hdr) for hdr in csv_col_headers_line.split(self.separator)]
        csv_hdr_to_idx = {hdr: idx for idx, hdr in enumerate(csv_col_headers)}
        attr_name_to_idx = {attr_name: csv_hdr_to_idx[csv_hdr]
                for attr_name, csv_hdr in self.columns.items()}
        return attr_name_to_idx


    def _conv_trn(self, line_num_in_csv: int, line: str, col_map: Dict[str, int]) -> Trn:
        """
        Obtain a Trn object from the data contained in the given line from the
        CSV file.
        """
        column_values = line.split(self.separator)
        columns = {}
        for col_name, col_idx in col_map.items():
            col_value = self.unquote(column_values[col_idx])
            if col_name == 'date':
                col_value = self.conv_date(col_value, self.fmt_date)
            elif col_name == 'value':
                col_value = self.conv_value(col_value, self.fmt_value)
            columns[col_name] = col_value

        trn = Trn()
        trn.line_num_in_csv = line_num_in_csv
        trn.columns = columns
        return trn


    def _read_sourcefile(self, filename: str) -> Tuple[SourceFileInfo, List[str]]:
        """
        Obtain CSV file and SourceFile descriptor.
        """
        with open(filename, 'rb') as fh:
            blob = fh.read()
        lines = str(blob, encoding=self.encoding).split("\n")

        n = datetime.datetime.now()
        src = SourceFileInfo()
        src.conversion_date = \
                f"{n.year}-{n.month:>02}-{n.day:>02} " \
                f"{n.hour:>02}:{n.minute:>02}:{n.second:>02}"
        src.filename = filename
        src.filesize = len(blob)
        src.sha1 = hashlib.sha1(blob).hexdigest()
        src.csv_fmt = self.name
        src.currency = self.currency
        src.columns = self.columns
        src.num_lines = len(lines)
        src.num_trns = 0
        src.header_lines = lines[:self.num_header_lines]

        return src, lines


    def process_csv(self, filename: str) -> TrnsSet:
        """
        Create a transaction set from the given CSV file.
        """
        # Obtain lines from CSV files.
        src, lines = self._read_sourcefile(filename)
        num = self.num_header_lines
        lines_header = lines[:num]
        lines_trns = lines[num:]

        # Create set of Trn objects.
        col_map = self._column_mapping(lines_header)
        trns = [self._conv_trn(line_num_in_csv, line.strip(), col_map)
                    for line_num_in_csv, line in enumerate(lines_trns, start=num+1)]
        src.num_trns = len(trns)

        # Create TrnsSet object.
        # (For the moment, the TrnsSetHeader object is not filled; needs to be
        #  adjusted manually.)
        trns_set = TrnsSet()
        trns_set.src = src
        trns_set.header = TrnsSetHeader()
        trns_set.trns = trns

        return trns_set
