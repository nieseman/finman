#!/usr/bin/env python3

"""
This module provides the Finman data classes.

- Data is stored in Finman transactions files (TrnsFile) in JSON Lines format.
- A transactions file contains a list of transactions sets (TrnsSet).
- A transaction set contains one transaction set descriptor (TrnsSetDesc) and
  a list of transactions (Trn).


TBD:
* The following data is considered necessary (or variable).
All objects and dicts may contain additional entries.

* In general: attributes with leading underscore are not written to disk.
  (Can be used for volatile/hidden information.)

* Hierachy:
  - A FinmanData instance may contain multiple JsonlFile instances.
  - A JsonlFile instances may contain multiple TrnsSet instances.
  - A TrnsSet instances may contain multiple Trn instances.
* Typically, the amount of Trn data within a JsonlFile is created when
  converting CSV files.
* TBD: The amount of Trns is not changed afterwards by Finman (but may be
  changed manually by hand by editing or amending a JSONL file).
* TBD: The only changes within JSONL files done by Finman refer to the 'notes'
  dict of Trns (using the functions set_cat(), clear_cat(), set_remark(),
  set_field()).

TBD: All present fields are set in initializer.

Core functions: Edit 'notes' attributes of Trns
Evaluation functions: may do further data evaluation, including polling of
header information (e.g. date ranges)

"""

from collections.abc import Sequence
from enum import Enum, auto
import json
import logging
from typing import Set, List, Dict, Optional, Union


# Field names.  TBD: rename "column" to "field" or "attribute"?
COL_ID      = '_id'
COL_IDX     = '_idx'
COL_MOD     = '_is_modified'
COL_DATE    = 'date'
COL_VALUE   = 'value'
COL_CAT_ALT = '_cat_alt'


def plural(word: str, count: Union[int, Sequence]) -> str:
    if isinstance(count, Sequence):
        count = len(count)
    return word + "s" if count != 1 else word

def str_modified(obj) -> str:
    return "modified" if obj.is_modified() else "unmodified"



class Trn:
    """
    A Finman transaction, corresponding to one data line of a CSV file.

    Attributes:

    _id             Unique ID during program run, set during loading of JSONL files.
    _idx            The index within the latest selection
    _is_modified    Have the transaction's 'note' attributes been modified?
    _cat_alt        Temporary alternative category name
    line_num_in_csv Line number in CSV file described in current block in JSONL.
    columns         Fields copied from CSV file (remain unchanged).
                    Field COL_VALUE is treated special (see selection.py).
    notes           User annotations.
                    Fields 'cat', 'cat_auto', 'remark' are expectedd.
                    Add any custom fields here; they remain unchanged.
    """

    def __init__(self, _id: Optional[str]=None):
        self._id                      = _id
        self._idx                     = None
        self._is_modified             = False
        self._cat_alt                 = ""
        self.line_num_in_csv          = None
        self.columns: Dict[str, str]  = {}
        self.notes                    = {
            'cat': "",
            'cat_auto': None,
            'remark': "",
        }


    def __repr__(self):
        return f"<Trn #{self._id} " \
               f"({str_modified(self)})>"


    def is_modified(self):
        return self._is_modified


    def _check_fields(self):
        """
        Give infos/warnings if expected attributes are not present.
        """
        if not hasattr(self, '_id'):
            logging.info(f"Trn has no ID.")
        if not hasattr(self, 'line_num_in_csv'):
            logging.info(f"{self} has no field 'line_num_in_csv'.")
        if not hasattr(self, 'columns'):
            logging.warning(f"{self} has no field 'columns'!")
        if not hasattr(self, 'notes'):
            logging.warning(f"{self} has no field 'notes'!")
        if COL_VALUE not in self.columns:
            logging.warning(f"{self} has no field 'columns.{COL_VALUE}'!")
        if 'cat' not in self.notes:
            logging.warning(f"{self} has no field 'notes.cat'!")
        if 'cat_auto' not in self.notes:
            logging.warning(f"{self} has no field 'notes.cat_auto'!")
        if 'remark' not in self.notes:
            logging.warning(f"{self} has no field 'notes.remark'!")


    def get_all_field_names(self) -> Set[str]:
        top_level_fields = {'_id', '_idx', '_is_modified', '_cat_alt', 'line_num_in_csv'}
        return top_level_fields.union(self.columns, self.notes)


    def get_field(self, field: str) -> str:
        """
        Get field of transaction by name.

        Note: Fields may be hidden due to the order of look-up.
        """
        if field == '_id':
            return self._id
        elif field == '_idx':
            return self._idx
        elif field == '_is_modified':
            return self._is_modified
        elif field == '_cat_alt':
            return self._cat_alt
        elif field == 'line_num_in_csv':
            return self.line_num_in_csv
        elif field in self.columns:
            return self.columns[field]
        elif field in self.notes:
            return self.notes[field]
        else:
            logging.info(f"{self}: Invalid field name '{field}'")
            return ""


    def set_cat_alt(self, cat: str):
        """
        Set temporary alternative category of transaction.
        """
        self._cat_alt = cat


    def set_cat(self, cat: str, cat_auto: bool = False):
        """
        Set category of transaction.

        'cat_auto' indicates if category was set according to automatic rule.
        """
        if self.notes['cat'] != cat:
            self.notes['cat'] = cat
            self.notes['cat_auto'] = cat_auto
            self._is_modified = True


    def clear_cat(self):
        if self.notes['cat'] != "":
            self.notes['cat'] = ""
            self.notes['cat_auto'] = None
            self._is_modified = True


    def set_remark(self, remark=""):
        if self.notes['remark'] != remark:
            self.notes['remark'] = remark
            self._is_modified = True


    def clear_modified(self):
        self._is_modified = False



class SourceFileInfo:
    """
    Information about a CSV source file (excluding header data).

    These attributes are not used by the core functions, 
    """

    def __init__(self):
        self.conversion_date:   str = None
        self.filename:          str = None
        self.filesize:          int = None
        self.sha1:              str = None
        self.csv_fmt:           str = None
        self.currency:          str = None
        self.columns:           Dict[str, str] = {}
        self.header_values:     Dict[str, str] = {}
        self.num_lines:         int = None
        self.num_trns:          int = None

    def __repr__(self):
        return f"<SourceFileInfo {self.filename}>"


class TrnsSetHeader:
    """
    Header for a consecutive set of transactions, containing some summary
    information.

    Initially, the transactions from one CSV file will be written as one
    transaction set. However, if one manually splits this into multiple
    transaction sets (possibly in different JSONL files), one may also manually
    create corresponding TrnsSetHeader entries.
    """

    def __init__(self):
        self.date_start:    str = None
        self.date_end:      str = None
        self.date_first:    str = None
        self.date_last:     str = None
        self.value_start:   str = None
        self.value_end:     str = None
        self.value_diff:    str = None

    def __repr__(self):
        return f"<TrnsSetHeader {self.date_start} to {self.date_end}>"


class TrnsSet:
    """
    A set of transactions, consisting of description and list of transactions.
    """

    def __init__(self):
        self.src             = SourceFileInfo()
        self.header          = TrnsSetHeader()
        self.trns: List[Trn] = []

    def __repr__(self):
        return f"<TrnsSet {self.src.filename} " \
               f"({str_modified(self)}): " \
               f"{len(self.trns)} {plural('transaction', self.trns)}>"

    def is_modified(self):
        return any(trn.is_modified() for trn in self.trns)



class JsonlFile:
    """
    A transactions file, consisting of zero, one or multiple transaction sets.
    """

    def __init__(self, filename: str, trn_id_prefix=""):
        self.filename                   = filename
        self.trns_sets: List[TrnsSet]   = []

        if filename:
            self.load(trn_id_prefix)


    def __repr__(self):
        cnt_trns = sum(len(trns_set.trns) for trns_set in self.trns_sets)
        return f"<JsonlFile {self.filename} " \
               f"({str_modified(self)}): " \
               f"{len(self.trns_sets)} transaction {plural('set', self.trns_sets)}, " \
               f"{cnt_trns} {plural('transaction', cnt_trns)}>"


    def is_modified(self):
        return any(trns_set.is_modified() for trns_set in self.trns_sets)


    def save(self):
        """
        Save all modified files in the given FinMan data.
        """
        if self.is_modified():
            with open(self.filename, 'w') as fh:
                self._write(fh)
            self.modified = False

        # Clear modified flag.
        for trns_set in self.trns_sets:
            for trn in trns_set.trns:
                trn.clear_modified()


    def _write(self, fh):

        def get_json(obj) -> str:
            """
            Deliver the JSONified variables of an object, with a type marker added.
            """
            pub_dict = {key: getattr(obj, key) for key in vars(obj) if not key.startswith('_')}
            d = {'type': obj.__class__.__name__, **pub_dict}
            return json.dumps(d)

        for trns_set in self.trns_sets:
            fh.write(get_json(trns_set.src) + "\n")
            fh.write(get_json(trns_set.header) + "\n")
            for trn in trns_set.trns:
                fh.write(get_json(trn) + "\n")
            fh.write("\n")


    def load(self, trn_id_prefix: str):
        try:
            dicts = {}
            with open(self.filename) as fh:
                for line_num_in_jsonl, line in enumerate(fh.readlines(), start=1):
                    line = line.strip()
                    if line:
                        dicts[line_num_in_jsonl] = json.loads(line)

            self.trns_sets = []
            self._construct_from_dicts(dicts, trn_id_prefix)

        except OSError as e:
            raise Exception(f"Error reading JSONL file {filename}: {e}")

        except Exception as e:
            raise Exception(f"Error reading JSONL file {self.filename}, "
                            f"line {line_num_in_jsonl + 1}: {e}")


    @staticmethod
    def _update(obj, d: Dict):
        # TBD:
        # - Do not overwrite existing stuff (e.g. columns, notes)!
        # - Ignore anything beginning with '_'?
        # - Only update existing top-level fields, and contents of
        #   dicts (e.g. columns, notes)?
        for key, value in d.items():
            setattr(obj, key, value)


    def _construct_from_dicts(self, dicts: Dict[int, Dict], trn_id_prefix):
        """
        Create a JsonlFile object from a list of variable dicts (each of which
        originates from one line in a JSONL file).
        """

        class ReadState(Enum):
            ExpectingSourceFileInfo = auto()
            ExpectingTrnsSetHeader = auto()
            ExpectingTrnOrSourceFileInfo = auto()
        # TBD: extend this function so that a TrnsSetHeader can be read without
        # a preceeding SourceFileInfoHeader; re-use a previous
        # SourceFileInfoHeader in that case.

        def finish_trns_set():
            nonlocal trns_set
            self.trns_sets.append(trns_set)
            trns_set = None

        trns_set = None
        read_state = ReadState.ExpectingSourceFileInfo

        for line_num_in_jsonl, d in dicts.items():
            # d is dict with all elements from JSONL line.
            tp = d['type']
            del d['type']
            if tp not in ('SourceFileInfo', 'TrnsSetHeader', 'Trn'):
                logging.warning(f"{self.filename} line {line_num_in_jsonl}: "
                                f"invalid entry type {tp}; ignoring.")
                continue

            # If a new transaction set starts, finish a previous transaction set.
            if read_state == ReadState.ExpectingTrnOrSourceFileInfo and tp == 'SourceFileInfo':
                finish_trns_set()
                read_state = ReadState.ExpectingSourceFileInfo

            # In case of a new source file header: store it in a new TrnsSet object.
            if read_state == ReadState.ExpectingSourceFileInfo:
                if tp != 'SourceFileInfo':
                    raise ValueError("Expected type 'SourceFileInfo'")
                assert trns_set is None, "wrong state of trns_set"

                trns_set = TrnsSet()
                self._update(trns_set.src, d)
                read_state = ReadState.ExpectingTrnsSetHeader

            # In case of a new source file header: store it.
            elif read_state == ReadState.ExpectingTrnsSetHeader:
                assert trns_set is not None, "wrong state of trns_set"
                if tp != 'TrnsSetHeader':
                    raise ValueError("Expected type 'TrnsSetHeader'")

                self._update(trns_set.header, d)
                read_state = ReadState.ExpectingTrnOrSourceFileInfo

            elif read_state == ReadState.ExpectingTrnOrSourceFileInfo:
                assert tp != 'SourceFileInfo', "tp==SourceFileInfo should have been covered above"
                assert trns_set is not None, "wrong state of trns_set"
                if tp != 'Trn':
                    raise ValueError("Expected type 'Trn'")

                _id = f"{trn_id_prefix}{line_num_in_jsonl}"
                trn = Trn(_id)
                self._update(trn, d)
                trn._check_fields()
                trns_set.trns.append(trn)

            else:
                assert False, f"invalid state {read_state}"

        if trns_set is not None:
            if read_state != ReadState.ExpectingTrnOrSourceFileInfo:
                raise ValueError("Missing type 'TrnsSetHeader'")
            finish_trns_set()



class FinmanData:
    """ TBD: add comments (also below) """

    def __init__(self, filenames: Union[str, List[str]]):
        if isinstance(filenames, str):
            filenames = filenames.split()

        self.filenames          = filenames
        self.jsonl_files        = []
        self.load()
        self.known_field_names  = self._get_field_names()


    def __repr__(self):
        return f"<FinmanData: " \
               f"{len(self.jsonl_files)} JSONL {plural('file', self.jsonl_files)} " \
               f"({str_modified(self)}): " \
               f"{', '.join(jsonl.filename for jsonl in self.jsonl_files)}>"


    def is_modified(self):
        return any(jsonl.is_modified() for jsonl in self.jsonl_files)


    def load(self):
        if len(self.filenames) == 0:
            self.jsonl_files = []
        if len(self.filenames) == 1:
            self.jsonl_files = [JsonlFile(self.filenames[0])]
        else:
            self.jsonl_files = [JsonlFile(filename, trn_id_prefix=f"{idx}-")
                                for idx, filename in enumerate(self.filenames, start=1)]


    def _get_field_names(self) -> Set[str]:
        s = set()
        for jsonl_file in self.jsonl_files:
            for trns_set in jsonl_file.trns_sets:
                for trn in trns_set.trns:
                    s = s.union(trn.get_all_field_names())
        return s


    def save(self):
        for jsonl_file in self.jsonl_files:
            jsonl_file.save()


    def expand_fieldname(self, field) -> str:
        fields = set(f for f in self.known_field_names if f.startswith(field))
        if field in fields:
            return field

        if len(fields) == 0:
            logging.warning(f"Field name '{field}' has no expansions.")
            return ""
        elif len(fields) == 1:
            field_exp = list(fields)[0]
            logging.debug(f"Field name expanded: '{field}' => '{field_exp}'.")
            return field_exp
        else:
            logging.warning(f"Field name '{field}' has multiple expansions: ({','.join(fields)}).")
            return ""
