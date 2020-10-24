#!/usr/bin/env python3

import datetime
import hashlib
from typing import List, Tuple, Dict

from finmanlib.datafile import Trn, TrnsSet, SourceFileInfo, SourceFileHeader



class ValueFmt:

    date: str = "YYYY-MM-DD"
    has_thousands_comma: bool = True
    has_comma_as_decimal: bool = True


class CsvFmt:
    """
    Format description of one kind of CSV source file.
    """

    def __init__(self, d: Dict):
        # Default values.
        self.name                   = ""
        self.comment                = ""
        self.encoding               = "utf-8"
        self.separator              = ";"
        self.currency               = "EUR"
        self.currency_sym           = "€"
        self.currency_in_front      = False
        self.header_lines           = 0
        self.line_with_column_names = 0
        self.fmt                    = ValueFmt()
        self.fmt_header             = ValueFmt()
        self.values_in_header       = {}
        self.columns                = {}
        
        # Store provided information.
        for key, value in d.items():
            if key not in vars(self):
                assert False, "TBD: wrong field"
            if key == 'fmt':
                for key2, value2 in value.items():
                    setattr(self.fmt, key2, value2)
            elif key == 'fmt_header':
                for key2, value2 in value.items():
                    setattr(self.fmt, key2, value2)
            else:
                setattr(self, key, value)


    @staticmethod
    def unquote(s: str) -> str:
        """
        Remove quotes from a string.
        """
        # TBD: make new field
        if type(s) is not str:
            return s
        if len(s) >= 2 and \
           ((s[0] == "'" and s[-1] == "'") or \
            (s[0] == '"' and s[-1] == '"')):
            return s[1:-1]
        else:
            return s


    def conv_date(self, s: str, fmt: ValueFmt) -> str:
        """
        Convert a given date to standard format.
        """
        date_pattern = self.fmt.date.upper().replace('.', '/').replace('-', '/')
        if date_pattern == "DD/MM/YYYY":
            dd, mm, yyyy = s[0:2], s[3:5], s[6:10]
        elif date_pattern == "MM/DD/YYYY":
            mm, dd, yyyy = s[0:2], s[3:5], s[6:10]
        elif date_pattern == "YYYY/MM/DD":
            yyyy, mm, dd = s[0:4], s[5:7], s[8:10]
        else:
            assert(False)

        return f"{yyyy}-{mm}-{dd}"


    def conv_value(self, s: str, fmt: ValueFmt) -> str:
        if fmt.has_thousands_comma:
            s = s.replace(',', '')
        if fmt.has_comma_as_decimal:
            s = s.replace(',', '.')
        return "{:+.2f}".format(float(s))


    def column_mapping(self, lines_header: List[str]) -> Dict[str, int]:
        csv_col_headers_line = lines_header[self.line_with_column_names - 1]
        csv_col_headers = [self.unquote(hdr) for hdr in csv_col_headers_line.split(self.separator)]
        csv_col_headers = [self.unquote(hdr) for hdr in csv_col_headers_line.split(self.separator)]
        csv_hdr_to_idx = {hdr: idx for idx, hdr in enumerate(csv_col_headers)}
        attr_name_to_idx = {attr_name: csv_hdr_to_idx[csv_hdr]
                for attr_name, csv_hdr in self.columns.items()}
        return attr_name_to_idx


    def conv_trn(self,
            line_num_in_csv: int, line: str, col_map: Dict[str, int],
            fmt: ValueFmt) -> Trn:

        column_values = line.split(self.separator)
        columns = {}
        for col_name, col_idx in col_map.items():
            col_value = self.unquote(column_values[col_idx])
            if col_name == 'date':
                col_value = self.conv_date(col_value, fmt)
            elif col_name == 'value':
                col_value = self.conv_value(col_value, fmt)
            columns[col_name] = col_value

        trn = Trn()
        trn.line_num_in_csv = line_num_in_csv
        trn.columns = columns
        return trn


    def read_sourcefile(self, filename: str) -> Tuple[SourceFileInfo, List[str]]:
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

        return src, lines


    def process_csv(self, filename: str) -> TrnsSet:
        """
        TBD
        """
        if self.fmt_header is None:
            self.fmt_header = self.fmt

        # Obtain lines from CSV files.
        src, lines = self.read_sourcefile(filename)
        num = self.header_lines
        lines_header = lines[:num]
        lines_trns = lines[num:]

        # Create transaction set.
        col_map = self.column_mapping(lines_header)
        trns = [self.conv_trn(line_num_in_csv, line.strip(), col_map, self.fmt)
                    for line_num_in_csv, line in enumerate(lines_trns, start=num+1)]
        src.num_trns = len(trns)
        # TBD: populate src.header_values

        header = SourceFileHeader()
        # TBD: populate SourceFileHeader

        trns_set = TrnsSet()
        trns_set.src = src
        trns_set.header = header
        trns_set.trns = trns
        return trns_set
