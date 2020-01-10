#!/usr/bin/env python3

import decimal
from typing import Optional, Union, Tuple, List, Generator



class FinmanError(Exception):
    pass

def Error(msg):
    raise FinmanError(msg)

def Warning(msg):
    print(msg)



#ef expand_indices(min, max, indices_str = '*'):
#   """

#   """
#   if indices_str == '*':
#       return set(range(min, max + 1))

#   indices = set()
#   for idx_entry in indices_str.split():
#       try:
#           i = int(idx_entry)
#           if not i >= min:
#               raise ValueError(f"Value {i} below lower limit {min}.")
#           if not i <= max:
#               raise ValueError(f"Value {i} above upper limit {max}.")

#           indices.add(i)

#       except ValueError:
#           s1, s2 = idx_entry.split('-')
#           i1, i2 = int(s1), int(s2)
#           if not i1 >= min:
#               raise ValueError(f"Lower range boundary {i1} below lower limit {min}.")
#           if not i2 <= max:
#               raise ValueError(f"Upper range boundary {i2} above upper limit {max}.")

#           # TBD: needs to be fixed?
#           indices += range(i1, i2 + 1)

#   if len(indices) == 0:
#       raise ValueError(f"Index list is empty")
#               
#   return indices
