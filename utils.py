# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# This file contains the types (enums and type classes) used throughout the application.
# -----------------------------------------------------------

# %% standard lib imports
import copy
from enum import Enum
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
        elif is_sequence(plist):  # passing a tuple or a list
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
    def __init__(self, nodes: list[Node]=[], type=ELEMENT_TYPE.UNKNOWN, lineNums: list[int]=[]):

        # nodes
        # NOTE: there can be duplicate nodes in an element
        if is_sequence(nodes):
            self.nodes = nodes
        else:
            raise ValueError("Invalid input type for Element")

        # types
        self.types = []
        if isinstance(type, list):
            self.types = type
        elif isinstance(type, ELEMENT_TYPE):
            self.addType(type)
        elif isinstance(type, str):
            self.addType(type)
        else:
            raise ValueError("Invalid input type for Element")

        # line number
        self.lineNum = []
        if isinstance(lineNums, list):
            self.lineNum = lineNums
        elif isinstance(lineNums, int):
            self.addLineNum(lineNums)
        else:
            raise ValueError("Invalid input type for Element")

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

    def addLineNum(self, lineNum: int):
        ''' Add a line number to the element
        '''
        self.lineNum.append(lineNum)


class Part():
    ''' Class for storing the information of a part
    '''
    def __init__(self,  elements: list[Element]=[], lineNum: int=-1, lineLastNum: int=-1, header: str="", secid: int=0, mid: int=0, eosid: int=0, hgid: int=0, grav: int=0, adpopt: int=0, tmid: int=0):
        self.elements = set(elements)
        self.lineNum = lineNum # line number of the header
        self.lineLastNum = lineLastNum # line number of the last line

        self.header = header
        self.secid = secid
        self.mid = mid
        self.eosid = eosid
        self.hgid = hgid
        self.grav = grav
        self.adpopt = adpopt
        self.tmid = tmid

    def __str__(self) -> str:
        return f"Part({self.elements})"

    def getPartData(self):
        ''' Return the PART data given its ID

            verts = list of coordinates of the corresponding element shells.
                    e.g. [(x1,y1,z1),(x2,y2,z2),(x3,y3,z3),(x4,y4,z4),(x5,y5,z5),(x6,y6,z6)]
            faces = indices of the corresponding nodes in verts (compatible with vedo's
                    mesh constructor)
                    e.g. [[n1_ind,n2_ind,n3_ind,n4_ind],[n4_ind,n5_ind,n6_ind]]
        '''

        # Create a set of the vertices that only appear in the part
        verts = list({v.coord for element in self.elements for v in element.nodes})

        # Create a mapping from the new vertex list to the new index
        vert_map = dict(zip(verts, range(len(verts))))

        # Iterate over the reduced vertex list and update the face indices
        faces = [[vert_map[v.coord] for v in element.nodes] for element in self.elements]
        return verts, faces




#===================================================================================================
# Helper functions
def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


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