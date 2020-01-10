#!/usr/bin/env python3

import copy

from .error import Error


class DataBaseElement:
    """
        Base class for elements in a Finman JSON transactions file.

        All deived classes provide a unified initializer and structure check.
        Motivation: duck typing is nice, but we want to have strict content
        checks on the JSON.

        Derived classes may provide additional front-end methods.
    """

    # Default members of the class. Will also be used for structure check.
    _defaults = {}

    # On the check of first-level sub-dicts, the 'defaults' definition of the
    # following dicts may be incomplete (i.e. they may have additional members).
    _incomplete_subdicts = ()

    # On the check of first-level sub-dicts, the following dicts are ignored.
    _ignore_subdicts = ()


    def __init__(self, data: dict = None):
        """
            Initialize the object with either passed data or default data.
        """
        self.clear()
        if data:
            self.__dict__ = data
    
    
    def clear(self):
        self.__dict__ = copy.deepcopy(self._defaults)


    def check_structure(self):
        """
            Check that the structure of the members of this object match the
            specified defaults (taking into account incomplete and ignored
            sub-dicts).
        """

        def check_dict(dict_id, dict_obj, dict_defaults, check_completeness):
            """
                Check given dict object against given default dict object.
                Depending on argument, excess elements may be permitted.
                Members starting with underscore are ignored.
            """
            for key in dict_defaults:
                if not key.startswith('_'):
                    if key not in dict_obj:
                        Error(f"[{dict_id}] Key '{key}' in defaults but not in object.")

            for key in dict_obj:
                if not key.startswith('_'):
                    if key not in dict_defaults:
                        if check_completeness:
                            Error(f"[{dict_id}] Key '{key}' in object but not in defaults.")
                    else:
                        type_obj = type(dict_obj[key])
                        type_default = type(dict_defaults[key])
                        if type_obj is not type_default:
                            Error(f"[{dict_id}] Value for '{key}' in object has "
                                  f"type '{type_obj.__name__}' but not "
                                  f"type '{type_default.__name__}'.")

        # Check completeness of top level.
        dict_id = self.__class__.__name__
        dict_obj = self.__dict__
        dict_defaults = self._defaults
        check_dict(dict_id, dict_obj, dict_defaults, True)

        # Check dictionaries on first sub-level.
        for key in dict_obj:
            if type(dict_obj[key]) is not dict:
                continue
            if key in self._ignore_subdicts:
                continue

            check_completeness = key not in self._incomplete_subdicts
            check_dict(f"{dict_id}/{key}",
                       dict_obj[key], dict_defaults[key], check_completeness)
