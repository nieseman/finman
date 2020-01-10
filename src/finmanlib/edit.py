#!/usr/bin/env python3

import decimal
import itertools
import json
import os
import readline
from typing import Tuple, List, Optional

from .error import Error
from .formatter import Formatter
from .subset import TransactionsSubset
from .data_transactions_file import TransactionsFile
from .data_csv_format import CsvFormat
from .data_csv_file import CsvFile



class TransactionsEdit:
    """
        Provide view/edit operations on a TransactionsFile object.

        Front-end methods (cf. command parsers in main program):
        * new()
        * info()
        * print()
        Additional methods for interactive command loop:
        * write()
        * quit()
    """

    def __init__(self, trns_file: TransactionsFile):
        self.trns_file = trns_file
        self.subset = TransactionsSubset(trns_file, None, "", "", "")
        self.last_used_category = ""    # TBD
        self.stop_loop = False
        self.interactive = False

        # TBD: additional option to use pager!?


    def import_data(self, kind: str, filename: str, csv_format_name: str = None):
        """
            TBD
        """
        if kind == 'categories':
            self._import_categories(filename)
        elif kind == 'csv-format':
            self._import_csv_format(filename)
        elif kind == 'csv':
            self._import_csv_file(filename, csv_format_name)

        if not self.interactive:
            self.trns_file.save()


    def info(self, subcmd: str):
        """
            Print information (specified by sub-command) to screen.
        """
        tf = self.trns_file

        if subcmd == 'file':
            date_min = min(t.from_source['date'] for t in tf.transactions)
            date_max = max(t.from_source['date'] for t in tf.transactions)
            print()
            print("Finman JSON transactions file:")
            print(f"    Filename:               {tf._filename}")
            print(f"    Number of entries:      {len(tf.transactions)}")
            print(f"    Date of first entry:    {date_min}")
            print(f"    Date of last entry:     {date_max}")
            print(f"    Modified:               {'yes' if tf.modified() else 'no'}")
            print(f"    Available transaction fields:")
            for column in tf.columns:
                print(f"        {column}")
        
        elif subcmd == 'cats':
            print()
            print(f"Available categories in file {tf._filename}:")
            for s in sorted(tf.get_category_strings()):
                print(f"    {s}")
        
        elif subcmd == 'used-cats':
            cat_count = {}
            for t in tf.transactions:
                try:
                    cat_count[t.category] += 1
                except KeyError:
                    cat_count[t.category] = 1
            print()
            print(f"Used categories in file {tf._filename}:")
            for cat in sorted(cat_count):
                print(f"    {cat} ({cat_count[cat]})")
        
        elif subcmd == 'options':
            print()
            print("Display options:")
            print(f"    Fields:             '{self.subset.fields_str}'")
            print(f"    Filter:             '{self.subset.filter_str}'")
            print(f"    Sorting:            '{self.subset.sort_str}'")
            print(f"    Last category:      '{self.last_used_category}'")
            print(f"    # filtered trns:    {len(self.subset.trns)}")


    def print(self,
            filter_str: Optional[str] = None,
            sort_str: Optional[str] = None,     # TBD
            ids: str = "",  # TBD
            indices_str: str = '*',
            fields_str: Optional[str] = None,
            store: bool = True,
            numbered: bool = True,
            csv: bool = False,
            export_filename: Optional[str] = None):
        """
            Print a filtered set of transactions to screen or file.
        """

        # Create subset of filtered transactions.
        subset = TransactionsSubset(self.trns_file, self.subset,
                        filter_str, sort_str, fields_str)
        subset.set_indexed_transactions(indices_str)

        # Prepare lines to be printed.
        if csv:
            lines = Formatter.csv_rows(subset, subset.fields, numbered)
        else:
            lines = self._table_lines(subset)

        # Print lines to screen or to file.
        if export_filename is None:
            for line in lines:
                print(line)
        else:
            try:
                with open(export_filename, 'x') as fh:
                    for line in lines:
                        fh.write(line + "\n")
                print(f"File '{export_filename}' written.")
            except FileExistsError:
                # TBD: raise error?
                print(f"File '{export_filename}' already exists!")
            except:
                raise   # TBD: give error message, without raise
                # TBD: raise error?
                print(f"Error: File '{filename}' could not be written!")
            
        # Store filtered transactions.
        if store:
            self.subset = subset


    def quit(self, only_if_unchanged: bool = True):
        """
            Initiate the quitting from the command loop.
        """
        if self.trns_file.modified() and only_if_unchanged:
            print(f"Unsaved changes.")
        else:
            self.stop_loop = True


    def set(self,
            filter_str: Optional[str] = None,
            sort_str: Optional[str] = None,     # TBD
            ids: str = "",      # TBD
            indices_str: str = '*',
            fields_str: Optional[str] = None,
            store: bool = True,
            value: Optional[str] = None,
            print_before: bool = True,
            print_each: bool = True,
            print_after: bool = True,
            kind: str = None):
        """

        TBD For info:
        - if value is not None: use value for all transactions; otherwise, enter
          each remark.
        """

        assert kind in ('remarks', 'categories')
        print(f"Setting {kind}...")

        # Create subset of filtered transactions.
        subset = TransactionsSubset(self.trns_file, self.subset,
                        filter_str, sort_str, fields_str)
        subset.set_indexed_transactions(indices_str)

        if print_before:
            for line in self._table_lines(subset):
                print(line)

        # Determine values for the selected/indexed transactions.
        if value is not None:
            values = [value] * len(subset.trns_indexed)
        else:
            values = []
            for idx, trn in subset.trns_indexed:
                if print_each:
                    pass    # TBD
                try:
                    # TBD: for transactions: select from transactions.
                    value = input(f"New value for transaction [{idx}]: ")
                    values.append(value)
                except EOFError:
                    print("\nNo change for this transaction.")
                    values.append(None)
                except KeyboardInterrupt:
                    print("\nSetting of {kind} canceled.")
                    return

        # Set remark/category for selected/indexed transactions.
        for (idx, trn), value in zip(subset.trns_indexed, values):
            if value is not None:
                if kind == 'remarks':
                    trn.set_remark(value)
                else:
                    trn.set_category(value)
                    # TBD: set transaction flags
                self.trns_file.modified(True)

        if print_after:
            for line in self._table_lines(subset):
                print(line)
            
        # Store filtered transactions.
        if store:
            self.subset = subset


    def cats(self,
            filter_str: Optional[str] = None,
            fields_str: Optional[str] = None,
            store: bool = True,
            cat_value: Optional[str] = None,
            print_before: bool = True):
        """
        """

        pass


    def write(self, confirm: bool):
        """
            If data has been changed, ask for confirmation and write JSON
            transactions file to disk.
        """
        # TBD: Move field 'modified' into class TransactionsFile.

        # TBD: print() => log() or Error()?

        if not self.trns_file.modified():
            print("    Data not modified, so JSON file not saved.")
            return

        try:
            if confirm:
                ch = input(f"Save JSON file '{self.trns_file._filename}'? (y/n)  ")
            else:
                ch = 'y'
            if ch == 'y':
                self.trns_file.save()
                print("File saved.")
            else:
                print("File not saved.")

        except (EOFError, KeyboardInterrupt):
            print()
            print("File not saved.")

        except OSError:
            print("Error: File could not be saved!")


    def _import_categories(self, filename: str):
        try:
            self.trns_file.categories = json.load(open(filename))
        except json.JSONDecodeError as e:
            Error("Cannot parse JSON categories text:\n%s" % e.msg)
        except:
            Error(f"Cannot read JSON categories file '{filename}'.")


    def _import_csv_format(self, filename: str):
        try:
            csv_format = json.load(open(filename))
            name = csv_format['name']
            self.trns_file.csv_formats[name] = CsvFormat(csv_format)
        except json.JSONDecodeError as e:
            Error("Cannot parse JSON categories text:\n%s" % e.msg)
        except KeyError:
            Error("JSON categories file '{filename}' does not contain field 'name'.")
        except:
            raise
            Error(f"Cannot read JSON categories file '{filename}'.")


    def _import_csv_file(self, filename: str, csv_format_name: str):
        tf = self.trns_file
        try:
            csv_format = tf.csv_formats[csv_format_name]
        except KeyError: 
            if tf.csv_formats.keys():
                valid_formats = f"Valid CSV formats are: " + \
                                ", ".join(tf.csv_formats.keys()) + "."
            else:
                valid_formats = "No CSV formats defined in Finman file."
            Error(f"Invalid CSV format '{csv_format_name}'. {valid_formats}")

        # Obtain data from CSV file.
        filename_base = os.path.basename(filename)
        if filename_base in tf.csv_source_files:
            Error(f"File '{filename_base}' already imported.")
        csv_file = CsvFile()
        columns, trns = csv_file.import_data(filename, csv_format_name, csv_format)

        
        # TBD: only store tf.csv_source_files now, not earlier. (because in
        # case of errors...)

        # Check/store imported data in transactions file.
        tf.modified(True)
        tf.csv_source_files[filename_base] = csv_file

        for col in columns:
            if col not in tf.columns:
                tf.columns.append(col)
        if 'account' not in tf.columns:
            tf.columns.append('account')

        # Store transactions.
        known_trn_ids = set(trn.id for trn in tf.transactions)
        for trn in trns:
            if trn.id in known_trn_ids:
                Warning(f"Transaction with ID '{trn.id}' "
                         "(line {trn.source['linenum']}) "
                         "already imported; skipping.")
            tf.transactions.append(trn)
            csv_file.num_imported += 1
            known_trn_ids.add(trn.id)
                

    def _table_lines(self, subset, numbered: bool = True):
        header_lines = (f"Filter string:   '{subset.filter_str}'",
                        f"Fields string:   '{subset.fields_str}'",
                        "")
        data_lines = Formatter.table_rows(subset, subset.fields, subset.widths, numbered)
        return itertools.chain(header_lines, data_lines)


    # TBD
#   def set_option(self, args):

#       def set_option(opt, text):
#           try:
#               inp = input("    %s  " % text)
#               if inp == "":
#                   print("    ... leaving unchanged.")
#               else:
#                   self.__dict__[opt] = inp
#               return False

#           except (EOFError, KeyboardInterrupt):
#               print()
#               return True

#       print("Set options:  (Ctrl-C/Ctrl-D to skip, empty input for no change.)")
#       if set_option('filter', 'Filter:') or \
#          set_option('fields', 'Fields:'):
#           return



#   def set_categories(self, args):

#       def print_selected_entries():
#           print()
#           print(f"Selected entries for setting of category:")
#           print()
#           lines = list(self._get_formatted_data_list(self.filtered_trns,
#                                                           self.fields_str,
#                                                           numbered = True))
#           self.print_trns(lines, indices)

#       def select_category():

#           def print_list(cat_list):
#               for idx, cat in enumerate(cat_list):
#                   if cat != "":
#                       print("    %3i %s" % (idx, cat))

#           last_cat = self.last_used_category
#           if last_cat:
#               last_cat += " (used last)"
#           new_cat = ""
#           cat_list = [last_cat]
#           while not new_cat:
#               print()
#               print("Please select: 'l' = list all; 's <match>' = search; number = select")

#               try:
#                   choice = input("Choice: ")
#                   idx = int(choice)
#                   if 0 <= idx < len(cat_list) and cat_list[idx] != "":
#                       new_cat = cat_list[idx]
#                   else:
#                       print("Invalid number.")
#                   
#               except ValueError:
#                   if choice == 'l':
#                       cat_list = [last_cat] + list(self.trns_file.get_category_strings())
#                       print_list(cat_list)
#                   elif choice.startswith('s'):
#                       args = choice.split()[1:]
#                       if args:
#                           match = args[0]
#                           cat_list = [last_cat] + list(self.trns_file.get_category_strings(match))
#                           print_list(cat_list)
#                       else:
#                           print("Missing search argument.")
#                   else:
#                       print("Invalid choice.")

#           return new_cat

#       def set_category(new_cat):
#           # Set the selected new category in all selected items.
#           for idx in indices:
#               t = self.filtered_trns[idx - 1]
#               t.set_category(new_cat)

#           self.trns_file._modified = True
#           self.last_used_category = new_cat
#           # TBD: category_selection


#       # Main part of set_categories().
#       if not self.filtered_trns:
#           print("No results filtered yet.")
#           return

#       try:
#           indices = expand_indices(1, len(self.filtered_trns), args)
#       except ValueError as e:
#           print(f"Invalid incides: {e}")
#           return

#       try:
#           print_selected_entries()
#           new_cat = select_category()
#           set_category(new_cat)
#       except (EOFError, KeyboardInterrupt):
#           print("\nCanceling setting category.")
#           return



#   def set_remarks(self, args):
#       if not self.filtered_trns:
#           print("No results filtered yet.")
#           return

#       # Check indices.
#       try:
#           indices = expand_indices(1, len(self.filtered_trns), args)
#       except ValueError as e:
#           print(f"Invalid incides: {e}")
#           return

#       # Determine printed output.
#       lines = list(self._get_formatted_data_list(
#                   self.filtered_trns,
#                   self.fields_str,
#                   numbered = True))

#       for idx in indices:
#           # Print to-be-modified entry, and ask for new remark.
#           print()
#           self.print_trns(lines, (idx,))
#           t = self.filtered_trns[idx - 1]
#           try:
#               remark = input("Remark: ")
#           except (EOFError, KeyboardInterrupt):
#               print("\nCanceling setting remarks.")
#               return

#           # Process input.
#           if remark == "":
#               print("Leaving remark unchanged.")
#           elif remark.strip() == "":
#               print("Clear remark.")
#               t.set_remark("")
#               self.trns_file._modified = True
#           else:
#               t.set_remark(remark)
#               self.trns_file._modified = True



##  def _get_formatted_data_list(self, trns, indices, fields_str, csv, numbered):
##      fields, data_lines = self.trns_file.get_data_list(trns, fields_str)

##      # TBD: Temporary limit.
##      for line in data_lines:
##          for idx, s in enumerate(line):
##              if len(s) > 40:
##                  line[idx] = s[:40]

##      if numbered:
##          fields = ['#'] + fields
##          for i in range(len(data_lines)):
##              data_lines[i] = [str(i + 1)] + data_lines[i]

##      if csv:
##          yield ";".join(fields)
##          for idx, data_line in enumerate(data_lines, 1):
##              if idx in indices:
##                  yield ";".join(data_line)
##      else:
##          # Determine column widths.
##          if data_lines:
##              widths = [max(len(line[i]) for line in data_lines) for i in range(len(fields))]
##          else:
##              widths = [0] * len(fields)
##          widths = [max(w, len(field)) for w, field in zip(widths, fields)]

##          # Determine whether the 'value' column is among the fields.
##          for idx, field in enumerate(fields):
##              if field == 'value':
##                  value_idx = idx
##                  break
##          else:
##              value_idx = None

##          # If yes, calculate sum of entries, and adjust width of column 'value'.
##          if value_idx:
##              sum = decimal.Decimal(0.0)
##              for line in data_lines:
##                  sum += decimal.Decimal(line[value_idx])
##              sum_str = Formatter.value(sum)

##              widths[value_idx] = max(widths[value_idx], len(sum_str))

##          # Construct format string.
##          sep_header = "─┼─"
##          separator_line = sep_header.join("─" * width for width in widths)
##          sep_data = " │ "
##          fmt_str = ""
##          for idx, (field, width) in enumerate(zip(fields, widths)):
##              if fmt_str != "":
##                  fmt_str += sep_data
##              if field == 'value':
##                  fmt_str += "%" + str(width) + "s"
##                  value_idx = idx
##              else:
##                  fmt_str += "%-" + str(width) + "s"


##          # Provide the header, data rows, and footer with sum of values.
##          header_line = fmt_str % tuple(fields)
##          yield header_line
##          yield separator_line
##          for idx, line in enumerate(data_lines, 1):
##              if idx in indices:
##                  if value_idx:
##                      sum += decimal.Decimal(line[value_idx])
##                  yield fmt_str % tuple(line)

##          if value_idx:
##              bottom_columns = [""] * len(fields)
##              bottom_columns[value_idx] = sum_str
##              bottom_line = fmt_str % tuple(bottom_columns)
##              yield separator_line
##              yield bottom_line
