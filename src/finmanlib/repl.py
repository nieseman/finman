#!/usr/bin/env python3

"""
An interactive REPL (read-eval-print loop) for Finman.
"""

import code
import readline

from finmanlib.categories import Categories
from finmanlib.datafile import FinmanData
from finmanlib.selection import Selection


USAGE = """
Usage:

Show transactions:
    p                       print current selection
    f <filter_str>          set filter for selection
    fields <fields_str>     set fields to be printed

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

    # TBD: optimize?
    #DEFAULT_FIELDS_STR = "dat|desc|val"
    #DEFAULT_FIELDS = "date|addressee:40|value|category|remark:30"
    DEFAULT_FIELDS = "date|desc|value|_is_mod|cat|remark"

    def __init__(self, args):
        if args.cat is None:
            self.categories = None
        else:
            self.categories = Categories(cats_file=args.cat)
        self.finman_data = FinmanData(filenames=args.jsonl)
        self.filter_str = ""
        self.fields_str = self.DEFAULT_FIELDS
        self.selection = Selection(self.finman_data, filter_str="")


    def run(self):
        """
        Run simple REPL loop.
        """
        print("Enter '?' for help.")
        quit = False
        while not quit:
            
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
            if cmd == '?':
                print()
                print(USAGE.strip())

            # Saving and quitting program.
            elif cmd == 'Q':
                if self.finman_data.is_modified():
                    print("Skipping unsaved changes.")
                quit = True

            elif cmd == 'q':
                if self.finman_data.is_modified():
                    print("Unsaved changes; will not quit.")
                else:
                    quit = True

            elif cmd == 'save':
                self.finman_data.save()

            # Selection and printing.
            elif cmd == 'p':
                self.print_trns()

            elif cmd == 'f':
                self.set_filter(filter_str=arg)

            elif cmd == 'fields':
                self.set_fields(fields_str=arg)

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
                self.print_vars()

            elif cmd == 'py':
                self.start_python_repl()

            else:
                print(f"Unknown command: '{cmd}'")


    def print_trns(self, subset_str=None):
        """
        Print current selection of transactions.
        """
        print()
        self.selection.print_trns(
                fields_str=self.fields_str,
                subset_str=subset_str,
                index_col=True,
                max_width=-1)


    def set_filter(self, filter_str: str):
        try:
            self.selection = Selection(self.finman_data, filter_str=filter_str)
            self.filter_str = filter_str
            self.print_trns()
        except ValueError as e:
            print(f"Error: {e} TBD: to be checked")


    def set_fields(self, fields_str: str):
        try:
            if fields_str == "":
                fields_str = self.DEFAULT_FIELDS
            # TBD: re-shuffle these lines;
            # TBD: adapt print_trns()?
            # TBD: to properly catch error
            self.fields_str = fields_str
            self.print_trns()
        except ValueError as e:
            print(f"Error: {e} TBD: to be checked")


    def set_remarks(self, subset_str: str):
        self.print_trns(subset_str)
        print()
        for trn in self.selection.get_subset(subset_str):
            try:
                remark = input(f"Remark for #{trn._idx}: ")
            except KeyboardInterrupt:
                print("... setting of remaining remarks canceled.")
                return
            trn.set_remark(remark)
        self.print_trns(subset_str)


    def set_category(self, subset_str: str):
        self.print_trns(subset_str)
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
        self.print_trns(subset_str)


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
                self.finman_data.expand_fieldname,
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

                    tmp_fields_str = "date|desc|value|_is_mod|cat|_cat_alt"
                    trns = list(trns_dict.keys())
                    Selection(self.finman_data, trns=trns).print_trns(
                            fields_str=tmp_fields_str,
                            index_col=True,
                            max_width=-1)
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
            


    def print_vars(self):
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
        self.print_vars()
        print("Entering Python REPL (hit Ctrl-D to quit)...")
        print()
        code.interact(local={
                'finman_data': self.finman_data,
                'selection':   self.selection,
                'filter_str':  self.filter_str,
                'fields_str':  self.fields_str,
                'categories':  self.categories,
                **globals()})
