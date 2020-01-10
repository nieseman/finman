#!/usr/bin/env python3

from typing import Optional, Dict

from .data_base_element import DataBaseElement



class Transaction(DataBaseElement):
    """
        One transaction in a Finman JSON transactions file.
    """

    _defaults = {
        'id': "",
        'source': {
            'filename': "",
            'linenum': -1,
            'line': ""
        },
        'from_source': {
            'account': "",
            'date': "",
            'value': ""
        },
        'category': "",
        'remark': "",
        'flags': ""
    }

    _incomplete_subdicts = ('from_source', )

    FLAGS_SEPARATOR = ';'


    def get_field(self, field_name: str, exc_if_nonexistent: bool = True):
        if field_name in ('id', 'category', 'remark', 'flags'):
            return self.__dict__[field_name]
        elif field_name in self.from_source:
            return self.from_source[field_name]
        else:
            if exc_if_nonexistent:
                raise(f"Field {field_name} does not exist in transaction {self.id}.")
            else:
                return ""


    def set_category(self, category: str):
        """
            Setter for the field 'category'.
        """
        assert(category != "")
        self.category = category


    def set_remark(self, remark: str):
        """
            Setter for the field 'remark'.
        """
        self.remark = remark


    def set_flag(self, flag_name: str, flag_value: str):
        """
            Setter for the field 'flags'.
        """
        flags = self._get_flags_dict()
        flags[flag_name] = flag_value
        self._set_flags_list(flags)


    def get_flag(self, flag_name) -> Optional[str]:
        """
            Getter for the field 'flags'.
        """
        flags = self._get_flags_dict()
        if flag_name in flags:
            return flags[flag_name]
        else:
            return None


    def _get_flags_dict(self) -> Dict[str, str]:
        """
            Construct a dictionary from the string self.flags.
        """

        # Setup flags dictionary.
        flags_dict = {}
        for key_and_value in self.flags.split(self.FLAGS_SEPARATOR):
            pos = key_and_value.find('=')

            # As flags shall only be set by self.set_flag(), self.flags consists
            # of valid key=value pairs.
            assert(pos > 0)

            key, value = key_and_value[:pos], key_and_value[pos + 1:]
            flags_dict[key] = value

        return flags_dict


    def _set_flags_list(self, flags: Dict[str, str]):
        """
            Set string self.flags from the given dict.
        """
        self.flags = self.FLAGS_SEPARATE.join(
                    f"{key}={value.strip()}" for key, value in flags.items())
