#!/usr/bin/env python3

import copy
import decimal
from typing import Generator, List, Optional, Tuple

from .formatter import Formatter



# Default view options.
DEFAULT_FIELDS_PLACEHOLDER = "~"
DEFAULT_FIELDS = "date|addressee:40|value|category|remark:30"
INDEX_SEPARATOR = ","
FIELD_SEPARATOR = "|"



class TransactionsSubset:
    """
        TBD
    """

    def __init__(self,
            trns_file: "TransactionsFile",
            prev_subset: "TransactionsSubset" = None,
            filter_str: Optional[str] = None,
            sort_str:   Optional[str] = None,
            fields_str: Optional[str] = None):
        """
            TBD.

            prev_subset is not stored, but used 

            Parameters:
                filter_str ("" for no filter, None for previous filter)
                sort_str ("" for no sort, None for previous sort)
                fields_str ("" for default fields, None for previous fields)
        """

        fields_str = Formatter.unquote(fields_str)
        filter_str = Formatter.unquote(filter_str)
        sort_str = Formatter.unquote(sort_str)

        # Store arguments.
        self.trns_file = trns_file

        # Filter rules and filtered transactions.
        self.filter_str = filter_str
        self.filters = []
        self.trns = []

        # Create filtered transactions, or copy from previous subset if
        # necessary.
        if filter_str is None:
            assert(prev_subset is not None)
            self.filter_str = prev_subset.filter_str
            self.filters = prev_subset.filters
            self.trns = prev_subset.trns
        else:
            self.filters = self._set_filters(self.filter_str)
            self.trns = self._set_transactions()

        if sort_str is None:
            assert(prev_subset is not None)
            self.sort_str = prev_subset.sort_str
        else:
            self.sort_str = sort_str

        # Create sorted list of transactions.
        self.sort_str = sort_str
        # TBD

        # Create list of fields (for display).
        if fields_str is None:
            assert(prev_subset is not None)
            self.fields_str = prev_subset.fields_str
        else:
            if fields_str == DEFAULT_FIELDS_PLACEHOLDER:
                self.fields_str = DEFAULT_FIELDS
            else:
                self.fields_str = fields_str
        self.fields, self.widths = self._unpack_fields(self.fields_str)

        # These fields are set separately by set_indexed_transactions().
        self.indices_str = ""
        self.indices = []
        self.trns_indexed = []


    def _set_filters(self, filter_str: str):

        filters = []

        if filter_str:
            for s in filter_str.split(FIELD_SEPARATOR):
                for op in ('<=', '>=', '<', '>', '='):
                    p = s.find(op)
                    if p >= 0:
                        field, filter_value = s[:p], s[p + len(op):]
                                # TBD: unquote filter_value?
                        if field == '':
                            assert(False)
                        field = self.trns_file.expand_field_name(field)

                        if op == '=':
                            if field != 'value':
                                op = 'contains'
                                filter_value = filter_value.lower()
                        else:
                            if field != 'value':
                                assert(False)
                            filter_value = decimal.Decimal(filter_value)

                        filters.append((op, field, filter_value))
                        break

                else:
                    assert(False)   # TBD

        return filters


    def _set_transactions(self):

        def match(s: str, substr: str) -> bool:
            """
                Check if substr is contained in s.
                Special case: If substr is empty, check if s is empty.
            """
            if substr == "":
                return s == ""
            else:
                return s.lower().find(substr) >= 0

        transactions = []

        for trn in self.trns_file.transactions:
            for op, field, filter_value in self.filters:

                value = decimal.Decimal(trn.from_source['value'])
                if op == '<':
                    if not value < filter_value:
                        break
                elif op == '<=':
                    if not value <= filter_value:
                        break
                elif op == '>':
                    if not value > filter_value:
                        break
                elif op == '>=':
                    if not value >= filter_value:
                        break
                elif op == '=':
                    if not value == filter_value:
                        break
                elif op == 'contains':
                    if field == 'category':
                        if not match(trn.category, filter_value):
                            break
                    elif field == 'remark':
                        if not match(trn.remark, filter_value):
                            break
                    else:
                        if not match(trn.from_source[field], filter_value):
                            break

            else:
                transactions.append(trn)

        return transactions


    def _set_indices(self, indices_str: str = '*'):
        """
            Convert a given indices list (given as string) into a list of index
            ranges. Indices must be within the given interval [1,idx_max].

            For example:
                "3,9-11,22"
            is converted to 
                [[3,3], [9,11], [22,22]].
        """
        self.indices_str = indices_str
        self.indices = []
        indices = []
        idx_max = len(self.trns)

        # This is the default case: use all elements.
        if indices_str == '*':
            indices_str = f"1-{idx_max}"

        # Split string into integer pairs.
        for idx_entry in indices_str.split(INDEX_SEPARATOR):
            try:
                idx = int(idx_entry)
                if not idx >= 1:
                    raise ValueError(f"Value '{idx}' below lower limit '{1}'.")
                if not idx <= idx_max:
                    raise ValueError(f"Value '{idx}' above upper limit '{idx_max}'.")

                indices.append((idx, idx))

            except ValueError:
                s1, s2 = idx_entry.split('-')
                idx1, idx2 = int(s1), int(s2)
                if not idx1 >= 1:
                    raise ValueError(f"Lower range boundary '{idx1}' below lower limit '{1}'.")
                if not idx2 <= idx_max:
                    raise ValueError(f"Upper range boundary '{idx2}' above upper limit '{idx_max}'.")

                if idx1 > idx2:
                    idx1, idx2 = idx2, idx1

                indices.append((idx1, idx2))

        if not indices:
            raise ValueError(f"No index ranges defined in string '{indices_str}'.")

        self.indices = indices


    def _index_is_selected(self, idx: int) -> bool:
        return any(idx_min <= idx <= idx_max for idx_min, idx_max in self.indices)


    def set_indexed_transactions(self, indices_str: str = '*'):
        self._set_indices(indices_str)
        self.trns_indexed = []

        for idx, trn in enumerate(self.trns, 1):
            if self._index_is_selected(idx):
                self.trns_indexed.append((idx, trn))


    def get_data_rows(self,
            fields: List[str],
            numbered: bool = False) \
                -> Generator[List[str], None, None]:
        """
            For a given set of transactions, deliver a (possibly numbered) list
            of rows, containing the specified fields. Limit to given indices if
            provided.

            Empty strings are used for fields that do not exist in transactions.
            (This could be the case in a JSON file which contains transactions
             imported from CSV files with different sets of columns.)
        """

        # TBD: check that fields are valid

        # Deliver header row.
        row = ["#"] if numbered else []
        yield row + fields

        # Deliver data rows.
        for idx, trn in self.trns_indexed:
            row = [str(idx)] if numbered else []
            for field in fields:
                row.append(trn.get_field(field, False))

            yield row


    def _unpack_fields(self, fields_str: Optional[str] = None) -> \
                            Tuple[List[str], List[Optional[int]]]:
        """
            Unpack a fields specifier (items 'column:width' separated by a pipe
            '|') into dedicated list.

            'column' may be an abbreviation, which is subsequently expanded to
            the full column name.
        """
        if fields_str:
            fields = []
            widths = []

            for field_spec in fields_str.split(FIELD_SEPARATOR):
                try:
                    parts = field_spec.split(':')
                    if len(parts) == 1:
                        field, width = parts[0], None
                    elif len(parts) == 2:
                        field, width = parts[0], int(parts[1])
                    else:
                        raise Exception()   # TBD
                    fields.append(self.trns_file.expand_field_name(field))
                    widths.append(width)
                except:
                    raise   # TBD: Error()

        else:
            fields = copy.deepcopy(self.trns_file.columns)
            widths = [None] * len(fields)

        return fields, widths
