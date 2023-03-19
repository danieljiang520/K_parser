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
    def __init__(self, nid, plist=(0, 0, 0), source: tuple[int, int]=None):
        ''' Initialize the node with a list of coordinates and a line number
        '''
        # node id
        self._nid = nid

        # the coordinates are stored as a tuple
        self._coord = plist

        # source file index and line number
        self._source = source

        # modified flag
        self.modified = False

    @property
    def nid(self):
        ''' Return the node id of the node
        '''
        return self._nid

    @property
    def coord(self):
        ''' Return the coordinates of the node
        '''
        return self._coord

    @coord.setter
    def coord(self, value):
        ''' Set the coordinates of the node
        '''
        if isinstance(value, Node):  # passing a node
            self._coord = copy.deepcopy(value._coord)
        elif isinstance(value, tuple):  # passing a tuple or a list
            self._coord = value
        else:
            raise ValueError("Invalid input type for Node")

        # set the modified flag
        self.modified = True

    @property
    def source(self):
        ''' Return the source of the node
        '''
        return self._source

    def __str__(self) -> str:
        return f"Node({self.coord})"

    def toK(self, sep=", "):
        ''' Return the node in K format
        '''
        return f"{self.nid}{sep}{self.coord[0]}{sep}{self.coord[1]}{sep}{self.coord[2]}"


class Element():
    ''' Class for storing the information of an element
    '''
    def __init__(self, eid, nodes: list[Node]=[], type=ELEMENT_TYPE.UNKNOWN, source: tuple[int, int]=None):

        # element id
        self._eid = eid

        # nodes
        self._nodes = nodes

        # type
        self._type = type

        # source file index and line number
        self._source = source

        # modified flag
        self.modified = False

    @property
    def eid(self):
        ''' Return the element id of the element
        '''
        return self._eid

    @property
    def nodes(self):
        ''' Return the nodes of the element
        '''
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        ''' Set the nodes of the element
        '''
        # NOTE: there can be duplicate nodes in an element
        if is_sequence(value):
            self._nodes = value
        else:
            raise ValueError("Invalid input type for Element")

        # set the modified flag
        self.modified = True

    @property
    def type(self):
        ''' Return the type of the element
        '''
        return self._type

    @type.setter
    def type(self, value):
        ''' Set the type of the element
        '''
        if isinstance(value, ELEMENT_TYPE):
            self._type = value
        else:
            raise ValueError("Invalid input type for Element")

        # set the modified flag
        self.modified = True

    @property
    def source(self):
        ''' Return the source of the element
        '''
        return self._source

    def __str__(self) -> str:
        return f"Element_{self.type}({self.nodes})"

    def toK(self, pid, sep=", "):
        ''' Return the element in K format
        '''
        return f"{self.eid}{sep}{pid}{sep}{sep.join([str(node) for node in self.nodes])}"


class Part():
    ''' Class for storing the information of a part
    '''
    def __init__(self, pid, elements: list[Element]=[], elementType: ELEMENT_TYPE=ELEMENT_TYPE.UNKNOWN, source: tuple[int, int, int]=None, header: str="", secid: int=0, mid: int=0, eosid: int=0, hgid: int=0, grav: int=0, adpopt: int=0, tmid: int=0):
        ''' Initialize the part with a list of elements and a line number
        '''
        # part id
        self._pid = pid

        # the elements are stored as a set
        self._elements = set(elements)

        # element type
        self._elementType = elementType

        # source: (file index, line number, last line number (inclusive))
        self._source = source

        # other part data
        self._header = header
        self._secid = secid
        self._mid = mid
        self._eosid = eosid
        self._hgid = hgid
        self._grav = grav
        self._adpopt = adpopt
        self._tmid = tmid

        # modified flag
        self.modified = False

    @property
    def pid(self):
        ''' Return the part id of the part
        '''
        return self._pid

    @property
    def elements(self):
        ''' Return the elements of the part
        '''
        return self._elements

    @elements.setter
    def elements(self, value):
        ''' Set the elements of the part
        '''
        if is_sequence(value):
            self._elements = set(value)
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def elementType(self):
        ''' Return the element type of the part
        '''
        return self._elementType

    @property
    def source(self):
        ''' Return the source of the part
        '''
        return self._source

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

    def __str__(self) -> str:
        return f"Part({self._elements})"

    def toK(self, sep=", "):
        ''' Return the part in K format
        '''
        return f"{self._header}\n{self.pid}{sep}{self._secid}{sep}{self._mid}{sep}{self._eosid}{sep}{self._hgid}{sep}{self._grav}{sep}{self._adpopt}{sep}{self._tmid}"



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