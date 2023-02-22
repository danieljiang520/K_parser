# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# This file contains the types (enums and type classes) used throughout the application.
# -----------------------------------------------------------

# %% standard lib imports
import copy
from enum import Enum
import numpy as np
from pathlib import Path
from sys import stderr
from typing import Union

#===================================================================================================
# Enums
class KEYWORD_TYPE(Enum):
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


class ELEMENT_TYPE(Enum):
    ''' Enumerations for different types of ELEMENT
    NOTE: Alphabetically sorted, and the parser only support the following keywords
          Different types of elements have different number of nodes
    usage: ELEMENT_TYPE.name, ELEMENT_TYPE.value, hashable with string
    '''
    UNKNOWN = 1
    BEAM = 2
    DISCRETE = 3
    SHELL = 4
    SOLID = 5


#===================================================================================================
# Type classes
class Node():
    ''' Class for storing the information of a node
    '''
    def __init__(self, plist=(0, 0, 0), lineNum: int=-1):

        if isinstance(plist, Node):  # passing a node
            self.coord = copy.deepcopy(plist.coord)
        elif is_sequence(plist):  # passing a list
            self.coord = plist
        else:
            raise ValueError("Invalid input type for Node")

        self.lineNum = lineNum

    def getCoord(self):
        ''' Return the coordinates of the node
        '''
        return self.coord

    def __str__(self) -> str:
        return f"Node({self.coord})"


class Element():
    ''' Class for storing the information of an element
    '''
    def __init__(self, nodes: list[Node]=[], type=ELEMENT_TYPE.UNKNOWN, lineNum: int=-1):

        # nodes
        if isinstance(nodes, list):
            self.nodes = set(nodes)
        elif isinstance(nodes, set):
            self.nodes = nodes
        else:
            raise ValueError("Invalid input type for Element")

        # types
        self.types = []
        if isinstance(type, ELEMENT_TYPE):
            self.addType(type)
        elif isinstance(type, list):
            self.types = type
        elif isinstance(type, str):
            self.addType(type)
        else:
            raise ValueError("Invalid input type for Element")

        # line number
        self.lineNum = lineNum

    def __str__(self) -> str:
        return f"Element_{self.types}({self.nodes})"

    def addType(self, type: Union[ELEMENT_TYPE, str]):
        ''' Add a type to the element
        '''
        if isinstance(type, ELEMENT_TYPE):
            self.types.append(type)
        elif isinstance(type, str) and type in ELEMENT_TYPE.__members__:
            self.types.append(ELEMENT_TYPE[type])
        else:
            raise ValueError("Invalid input for Element.addType")


class Part():
    ''' Class for storing the information of a part
    '''
    def __init__(self,  elements: list[Element]=[], lineNum: int=-1, header: str="", secid: int=0, mid: int=0, eosid: int=0, hgid: int=0, grav: int=0, adpopt: int=0, timid: int=0):
        self.elements = set(elements)
        self.lineNum = lineNum

        self.header = header
        self.secid = secid
        self.mid = mid
        self.eosid = eosid
        self.hgid = hgid
        self.grav = grav
        self.adpopt = adpopt
        self.timid = timid

    def __str__(self) -> str:
        return f"Part({self.elements})"




#===================================================================================================
# Helper functions
def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def make3d(pts, transpose=False):
    """
    Convert a list of 2D or 3D points to a numpy array of 3D points.
    """
    pts = np.asarray(pts)

    if pts.dtype == "object":
        raise ValueError("Cannot form a valid numpy array, input may be non-homogenous")

    if pts.shape[0] == 0:  # empty list
        raise ValueError("Empty list is not supported.")

    if pts.ndim == 1:
        if pts.shape[0] == 2:
            return np.hstack([pts, [0]]).astype(pts.dtype)
        elif pts.shape[0] == 3:
            return pts
        else:
            raise ValueError

    if pts.shape[1] == 3:
        return pts

    if transpose:
        pts = pts.T

    if pts.shape[1] == 2:
        return np.c_[pts, np.zeros(pts.shape[0], dtype=pts.dtype)]

    if pts.shape[1] != 3:
        raise ValueError("input shape is not supported.")
    return pts


def is_list_of_strings(lst):
    ''' Check if the list is a list of strings
    '''
    return isinstance(lst, list) and all(isinstance(elem, str) or isinstance(elem, Path) for elem in lst)


def is_sequence(arg):
    ''' Check if the input is iterable.
    Reference: https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
    '''
    if hasattr(arg, "strip"):
        return False
    if hasattr(arg, "__getslice__"):
        return True
    if hasattr(arg, "__iter__"):
        return True
    return False


def getAllKFilesInFolder(folderPath: str) -> list[str]:
    ''' Return a list of all .k files in the folder
    '''
    return list(Path(folderPath).glob('*.k'))