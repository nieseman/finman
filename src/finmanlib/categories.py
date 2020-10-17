#!/usr/bin/env python3

"""
This module provides class Selection, which is the essential way to access
transactions from a FinmanData object:
- Print the selection.
- Access/modify specific Trn objects.
"""

from collections import namedtuple
import json
import logging
from typing import List, Callable

from finmanlib.datafile import Trn
from finmanlib.selection import TrnFilter



CatAutoAssignment = namedtuple('CatAutoAssignment',
        "num_total num_unchanged no_prev prev_auto prev_man multi")
# num_total     = total number of checked transactions
# num_unchanged = number of unchanged transactions
# no_prev       = one new category, no previous category
# prev_auto     = one new category, previous category was automatically set
# prev_man      = one new category, previous category was manually set
# multi         = multiple new categories


class Categories:
    """
    A selection of transactions.
    """
    SEPARATOR_CATS = ' ▶ '

    def __init__(self, cats_file: str):
        self.cats_file = cats_file
        self.cats = {}
        self.load()


    def __repr__(self):
        return f"<Categories '{self.cats_file}': {len(self.cats)} elements>"


    def load(self):
        msg_prefix = f"Categories file '{self.cats_file}': "
        try:
            with open(self.cats_file) as fh:
                cat_data = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            logging.warning(f"{msg_prefix}Cannot load: {e}.")
            return

        try:
            cats = {}
            self._extract_cats(cats, "", cat_data)
        except ValueError as e:
            logging.warning(f"{msg_prefix}{e}")
            return

        self.cats = cats


    @classmethod
    def _extract_cats(cls, d: dict, prefix: str, cat_data: dict):
        """
        Extract the categories from the given JSON dict into the given
        categories dict.

        Raise value error in case of invalid syntax.
        """
        if not isinstance(cat_data, dict):
            raise ValueError("Dict expected.")

        if prefix != "":
            prefix += cls.SEPARATOR_CATS

        for key, value in cat_data.items():
            if not isinstance(key, str):
                raise ValueError("Dict key must be str.")

            if isinstance(value, dict):
                d[prefix + key] = ""
                cls._extract_cats(d, prefix + key, value)
            elif isinstance(value, list):
                if not all(isinstance(v, str) for v in value):
                    raise ValueError("List elements must be strings.")
                d[prefix + key] = value
            else:
                raise ValueError("Value must be dict or list.")


    def get_filtered_cats(self, cat_hint: str) -> List[str]:
        cat_hint = cat_hint.lower()
        return [cat for cat in self.cats.keys() if cat.lower().find(cat_hint) >= 0]


    def get_auto_assignments(self,
            expand_fieldname: Callable[[str], str],
            trns: List[Trn]) -> CatAutoAssignment:

        # TBD: adjust var names?

        # Prepare Filter objects.
        filter_dict: Dict[str, List[TrnFilter]] = {}
        for cat, conds in self.cats.items():
            if len(conds) > 0:
                filter_dict[cat] = [TrnFilter(expand_fieldname, filter_str=cond) for cond in conds]
                
        # Prepare result variables.
        num_total = len(trns)
        num_unchanged = 0
        no_prev = {}
        prev_auto = {}
        prev_man = {}
        multi = {}

        for trn in trns:

            # Determine (from filters) all new categories for this transaction.
            new_cats = []
            for cat, trn_filters in filter_dict.items():
                if any(trn_filter.match(trn) for trn_filter in trn_filters):
                    new_cats.append(cat)

            # Store results for new category.
            if len(new_cats) == 0:
                num_unchanged += 1
            elif len(new_cats) == 1:
                new_cat = new_cats[0]
                old_cat = trn.get_field('cat')
                old_cat_auto = trn.get_field('cat_auto')
                if new_cat == old_cat:
                    num_unchanged += 1
                else:
                    if old_cat == "":
                        no_prev[trn] = new_cat
                    else:
                        if old_cat_auto == False:
                            prev_man[trn] = new_cat
                        else:
                            prev_auto[trn] = new_cat
            else:
                multi[trn] = new_cats

        return CatAutoAssignment(num_total, num_unchanged,
                no_prev, prev_auto, prev_man, multi)
