# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# This file contains the types (enums and type classes) used throughout the application.
# -----------------------------------------------------------

# %% standard lib imports
from enum import Enum
from pathlib import Path
from sys import stderr
from typing import NamedTuple

#===================================================================================================
# Enums
class KEYWORD(Enum):
    ''' Enumerations for different types of KEYWORD
    NOTE: Alphabetically sorted, and the parser only support the following keywords

    usage: KEYWORD.name, KEYWORD.value, hashable with string
    '''
    UNKNOWN = 1
    ELEMENT_SHELL = 2
    END = 3
    KEYWORD = 4
    NODE = 5
    PART = 6

#===================================================================================================
# Type classes
class Part(NamedTuple):
    header: str
    secid: int
    mid: int
    eosid: int
    hgid: int
    grav: int
    adpopt: int
    timid: int

#===================================================================================================
# Helper functions
def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def is_list_of_strings(lst):
    ''' Check if the list is a list of strings
    '''
    return isinstance(lst, list) and all(isinstance(elem, str) or isinstance(elem, Path) for elem in lst)


def getAllKFilesInFolder(folderPath: str) -> list[str]:
    ''' Return a list of all .k files in the folder
    '''
    return list(Path(folderPath).glob('*.k'))