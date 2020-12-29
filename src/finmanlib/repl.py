#!/usr/bin/env python3

"""
An interactive REPL (read-eval-print loop) for Finman.
"""

import code
import os
import readline
import sys
from typing import Optional

from finmanlib.categories import Categories
from finmanlib.datafile import FinmanData
from finmanlib.selection import Selection


USAGE = """
Usage:

Show transactions:
    p                       print current selection
    f <filter_str>          set filter for selection
    fields <fields_str>     set fields to be printed
    s <fields_str>          set sort order
    d <subset_str>          show details of subset of selection

Modify transactions:
    r <subset_str>          set remarks for subset of selection
    c <subset_str>          set identical category for subset of selection
    cat-auto                automatically set categories by conditions

Other:
    save                    save JSONL file(s)
    q                       quit if no changes unsaved
    Q                       force quit (no save)
    cat-list                list categories and conditions
    cat-reload              reload catgories file
    vars                    print variables
    py                      interactive Python session
    ?                       help
"""

# TBD: listing categories, add new category, set/modify category match string.



class FinmanREPL:

    HIST_FILE = f"{os.getenv('HOME')}/.finman_history"

    # TBD: optimize?
    #DEFAULT_FIELDS_STR = "dat|desc|val"
    #DEFAULT_FIELDS = "date|addressee:40|value|category|remark:30"
    #DEFAULT_FIELDS = "date|desc:40|value|_is_mod|cat|remark:40"
    DEFAULT_FIELDS = "date|addr:30|desc:40|value|_is_mod|cat|remark:40"
    FIELDS_CAT_DIFF = "date|addr:20|desc:20|value|_is_mod|_cat_alt|cat:20"

    def __init__(self, args):
        if args.cat is None:
            self.categories = None
        else:
            self.categories = Categories(cats_file=args.cat)

        try:
            self.finman_data = FinmanData(filenames=args.jsonl)
        except Exception as e:
            print(str(e))
            sys.exit(1)

        self.sort_str = ""
        self.filter_str = ""
        self.fields_str = self.DEFAULT_FIELDS
        self.selection = Selection(self.finman_data, filter_str="", sort_str="")


    def run_repl(self):
        """
        Run simple REPL loop.
        """
        try:
            readline.read_history_file(self.HIST_FILE)
        except OSError:
            pass

        print("Enter '?' for help.")
        quit = None
        while quit is not True:
            
            # Read command.
            try:
                cmd_line = input("\n> ")
            except (KeyboardInterrupt, EOFError):
                print("Enter 'q' to quit.")
                continue

            # Ignore empty and comment-like commands.
            cmd_line = cmd_line.strip()
            if cmd_line == "" or cmd_line.startswith('#'):
                continue

            # Evaluating input string.
            cmd_parts = cmd_line.split()
            cmd = cmd_parts[0]
            arg = cmd_parts[1] if len(cmd_parts) >= 2 else ""
            quit = self.run_cmd(cmd, arg)

        try:
            readline.write_history_file(self.HIST_FILE)
        except OSError:
            print(f"Cannot write file {self.HIST_FILE}.")


    def run_cmd(self, cmd: str, arg: str) -> Optional[bool]:
        """
        Run given command with argument. Return True if the REPL should stop.
        """
        if cmd == '?':
            print()
            print(USAGE.strip())

        # Saving and quitting program.
        elif cmd == 'Q':
            if self.finman_data.is_modified():
                print("Skipping unsaved changes.")
            return True

        elif cmd == 'q':
            if self.finman_data.is_modified():
                print("Unsaved changes; will not quit.")
            else:
                return True

        elif cmd == 'save':
            self.finman_data.save()

        # Selection and printing.
        elif cmd == 'p':
            self.print_transactions()

        elif cmd == 'd':
            self.print_details(subset_str=arg)

        elif cmd == 'f':
            self.set_filter(filter_str=arg)

        elif cmd == 'fields':
            self.set_fields(fields_str=arg)

        elif cmd == 's':
            self.set_sort(sort_str=arg)

        # Remarks and categories.
        elif cmd == 'r':
            self.set_remarks(subset_str=arg)

        elif cmd == 'c':
            self.set_category(subset_str=arg)

        elif cmd == 'cat-list':
            self.list_categories()

        elif cmd == 'cat-reload':
            self.categories.load()

        elif cmd == 'cat-auto':
            self.set_categories_auto()

        # Python stuff.
        elif cmd == 'vars':
            self.print_variables()

        elif cmd == 'py':
            self.start_python_repl()

        else:
            print(f"Unknown command: '{cmd}'")


    def print_transactions(self, subset_str=None):
        """
        Print current selection of transactions.
        """
        print()
        self.selection.print_trns_table(
                fields_str=self.fields_str,
                subset_str=subset_str,
                index_col=True)


    def print_details(self, subset_str=None):
        """
        Print current selection of transactions.
        """
        if subset_str == "":
            subset_str = "1-"
        self.selection.print_trns_details(
                fields_str=self.fields_str,
                subset_str=subset_str)


    def set_filter(self, filter_str: str):
        try:
            self.selection = Selection(self.finman_data, filter_str=filter_str, sort_str=self.sort_str)
            self.filter_str = filter_str
            self.print_transactions()
        except ValueError as e:
            print(f"Error: {e} TBD: to be checked")


    def set_fields(self, fields_str: str):
        try:
            if fields_str == "":
                fields_str = self.DEFAULT_FIELDS
            # TBD: re-shuffle these lines;
            # TBD: adapt print_transactions()?
            # TBD: to properly catch error
            self.fields_str = fields_str
            self.print_transactions()
        except ValueError as e:
            print(f"Error: {e} TBD: to be checked")


    def set_sort(self, sort_str: str):
        try:
            self.selection = Selection(self.finman_data, filter_str=self.filter_str, sort_str=sort_str)
            self.sort_str = sort_str
            self.print_transactions()
        except ValueError as e:
            print(f"Error: {e} TBD: to be checked")


    def set_remarks(self, subset_str: str):
        self.print_transactions(subset_str)
        print()
        for trn in self.selection.get_subset(subset_str):
            try:
                remark = input(f"Remark for #{trn._idx}: ")
            except KeyboardInterrupt:
                print("... setting of remaining remarks canceled.")
                return
            trn.set_remark(remark)
        self.print_transactions(subset_str)


    def set_category(self, subset_str: str):
        self.print_transactions(subset_str)
        print()
        try:
            new_cat = None
            while new_cat is None:

                # Provide categories to choose from.
                cat_hint = input("Give category hint: ")
                cats = self.categories.get_filtered_cats(cat_hint)
                num_len = len(str(len(cats)))
                for idx, cat in enumerate(cats, 1):
                    print(f"    {str(idx).rjust(num_len)}  {cat}")

                # Choose category.
                cat_idx = input("Which category to set? ")
                try:
                    cat_idx = int(cat_idx) - 1
                    new_cat = cats[cat_idx]
                except (ValueError, KeyError):
                    print(f" Invalid category index '{cat_idx}'. Again.")

        except KeyboardInterrupt:
            print("... setting of category canceled.")
            return

        # Setting new category.
        for trn in self.selection.get_subset(subset_str):
            trn.set_cat(new_cat, cat_auto=False)
        self.print_transactions(subset_str)


    def list_categories(self):
        if self.categories is None:
            print("No categories loaded")
        else:
            print(f"Categories file '{self.categories.cats_file}':")
            max_len = max(len(cat) for cat in self.categories.cats.keys())
            for cat, conds in self.categories.cats.items():
                print(f"    {cat.ljust(max_len)}    {', '.join(conds)}")


    def set_categories_auto(self):

        # Determine new categories, and store these category candidates in the
        # Trn objects.
        aa = self.categories.get_auto_assignments(
                self.finman_data,
                trns=self.selection.trns)

        for trn, new_cat in aa.no_prev.items():
            trn.set_cat_alt(new_cat)
        for trn, new_cat in aa.prev_auto.items():
            trn.set_cat_alt(new_cat)
        for trn, new_cat in aa.prev_man.items():
            trn.set_cat_alt(new_cat)
        for trn, new_cats in aa.multi.items():
            trn.set_cat_alt(", ".join(new_cats))


        # Show foreseen categories and ask for confirmation.
        try:
            to_be_confirmed = True
            while to_be_confirmed:
                print()
                print(f"1) no previous category:             {len(aa.no_prev):>4}")
                print(f"2) previous category auto set:       {len(aa.prev_auto):>4}")
                print(f"3) previous category manually set:   {len(aa.prev_man):>4}")
                print(f"4) multiple new categories:          {len(aa.multi):>4}")
                print(f"   unchanged transactions:           {aa.num_unchanged:>4}")
                print(f"                                    -----")
                print(f"   Total:                            {aa.num_total:>4}")
                print()
                selection = input("Enter 1/2/3/4 to view. Enter 'yes' to store 1/2: ").lower()
                if selection in "1234":
                    if selection == "1":
                        trns_dict = aa.no_prev
                    elif selection == "2":
                        trns_dict = aa.prev_auto
                    elif selection == "3":
                        trns_dict = aa.prev_man
                    elif selection == "4":
                        trns_dict = aa.multi

                    tmp_fields_str = self.FIELDS_CAT_DIFF
                    trns = list(trns_dict.keys())
                    Selection(self.finman_data, trns=trns).print_trns_table(
                            fields_str=tmp_fields_str,
                            index_col=True)
                elif selection == "yes":
                    to_be_confirmed = False     # quit loop
                else:
                    print("Bad input '{selection}'.")

        except KeyboardInterrupt:
            print("... automatic setting of category canceled.")
            return
                    
        # Set categories.
        for trn, new_cat in aa.no_prev.items():
            trn.set_cat(new_cat, cat_auto=True)
        for trn, new_cat in aa.prev_auto.items():
            trn.set_cat(new_cat, cat_auto=True)
            


    def print_variables(self):
        """
        Print all relevant variables and information.
        """
        print()
        print("Variables:")
        print(f"    finman_data:   {self.finman_data}")
        print(f"    selection:     {self.selection}")
        print(f"    filter_str:    '{self.filter_str}'")
        print(f"    fields_str:    '{self.fields_str}'")
        print(f"    categories:    {self.categories}")
        print("And by the way:")
        print(f"    known fields:  {','.join(sorted(self.finman_data.known_field_names))}")


    def start_python_repl(self):
        self.print_variables()
        print("Entering Python REPL (hit Ctrl-D to quit)...")
        print()
        code.interact(local={
                'finman_data': self.finman_data,
                'selection':   self.selection,
                'filter_str':  self.filter_str,
                'fields_str':  self.fields_str,
                'categories':  self.categories,
                **globals()})
