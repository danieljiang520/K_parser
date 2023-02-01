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
    ELEMENT = 2
    END = 3
    KEYWORD = 4
    NODE = 5
    PART = 6

#===================================================================================================
# Type classes
class Element():
    ''' Class for storing the information of an element
    '''
    def __init__(self, nodes: list[int]=[], option: list[str]=[]):
        self.nodes = nodes
        self.option = option

class Part():
    ''' Class for storing the information of a part
    '''
    def __init__(self,  elements: list[int]=[], header: str="", secid: int=0, mid: int=0, eosid: int=0, hgid: int=0, grav: int=0, adpopt: int=0, timid: int=0):
        self.elements = elements
        self.header = header
        self.secid = secid
        self.mid = mid
        self.eosid = eosid
        self.hgid = hgid
        self.grav = grav
        self.adpopt = adpopt
        self.timid = timid

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