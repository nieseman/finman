#!/usr/bin/env python3

"""
A simple interactive REPL (read-eval-print loop) for Finman.
"""

import code
import readline

from finmanlib.datafile import FinmanData


USAGE = """
Usage:
    p                   print
    f <filter_str>      set filter, and print
    fields <fields_str> set fields, and print
    cat <subset_str>    print, set identical category for subset, and print
    rem <subset_str>    print, set remarks for subset, and print
    save                save file(s)
    q                   quit if no changes unsaved
    Q                   force quit (no save)
    vars                print variables
    py                  interactive Python session
    ?                   help
"""

# TBD: listing categories, add new category, set/modify category match string.



class FinmanREPL:

    # TBD: optimize?
    #DEFAULT_FIELDS_STR = "dat|desc|val"
    #DEFAULT_FIELDS = "date|addressee:40|value|category|remark:30"
    DEFAULT_FIELDS = "date|desc|value|cat|remark"

    def __init__(self, args):
        self.finman_data = FinmanData(filenames=args.jsonl)
        self.selection = self.finman_data.filter("")
        self.filter_str = ""
        self.fields_str = self.DEFAULT_FIELDS


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

            # 'save'/'q'/'Q' = Saving/quitting program.
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

            # 'f'/'fields'/'p' = Setting/printing selection.
            elif cmd == 'p':
                self.print_trns()

            elif cmd == 'f':
                try:
                    self.selection = self.finman_data.filter(arg)
                    self.filter_str = arg
                    self.print_trns()
                except ValueError as e:
                    print(f"Error: {e} TBD: to be checked")

            elif cmd == 'fields':
                try:
                    if arg == "":
                        fields_str = self.DEFAULT_FIELDS
                    else:
                        fields_str = arg
                    # TBD: re-shuffle these lines;
                    # TBD: adapt print_trns()?
                    # TBD: to properly catch error
                    self.fields_str = fields_str
                    self.print_trns()
                except ValueError as e:
                    print(f"Error: {e} TBD: to be checked")

            # 'cat' = Setting comments of transactions.
            elif cmd == 'cat':
                subset_str = arg
                self.print_trns(subset_str)
                try:
                    cat = self.get_cat()
                except KeyboardInterrupt:
                    print("... setting category canceled.")
                    continue
                for trn in self.selection.get_subset(subset_str):
                    trn.set_cat(cat, cat_auto=False)
                self.print_trns(subset_str)

            # 'rem' = Setting remarks of transactions.
            elif cmd == 'r':
                subset_str = arg
                self.print_trns(subset_str)
                for trn in self.selection.get_subset(subset_str):
                    try:
                        remark = input(f"Remark for #{trn._idx}: ")
                    except KeyboardInterrupt:
                        print("... setting remarks canceled.")
                        continue
                    trn.set_remark(remark)
                self.print_trns(subset_str)

            # 'vars', 'py' = Variables and interactive session
            elif cmd == 'vars':
                self.print_vars()

            elif cmd == 'py':
                self.print_vars()
                print("Entering Python REPL (hit Ctrl-D to quit)...")
                print()
                code.interact(local={
                        'finman_data': self.finman_data,
                        'selection':   self.selection,
                        'filter_str':  self.filter_str,
                        'fields_str':  self.fields_str,
                        **globals()})

            else:
                print(f"Unknown command: '{cmd}'")


    def print_trns(self, subset_str=None):
        """
        Print current selection of transactions.
        """
        print()
        self.selection.print(
                fields_str=self.fields_str,
                subset_str=subset_str,
                index_col=True,
                max_width=-1)


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
        print("And by the way:")
        print(f"    known fields:  {','.join(sorted(self.finman_data.known_field_names))}")


    def get_cat(self):
        assert False, "TBD: This whole 'select categories' thing."
