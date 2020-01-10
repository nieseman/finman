#!/usr/bin/env python3

from .data_base_element import DataBaseElement



class CsvFormat(DataBaseElement):
    """
        Format description of one kind of CSV source file.
    """

    _defaults = {
        "name": "",
        "comments": [],
        "format": {
            "encoding": "",
            "separator": ";",
            "currency": "EUR",
            "currency_symbol": "€",
            "date": "",
            "header": {
                "value_remove_points": True,
                "value_replace_comma_with_point": True,
                "num_lines": -1,
                "line_with_column_names": -1
            },
            "data_lines": {
                "value_remove_points": True,
                "value_replace_comma_with_point": True
            },
        },
        "descriptors_in_header": {},
        "columns": {
            "date": "",
            "value": ""
        }
    }

    _incomplete_subdicts = ('descriptors_in_header', 'columns')
