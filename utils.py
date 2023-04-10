# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# This file contains the types (enums and type classes) used throughout the application.
# -----------------------------------------------------------

# %% standard lib imports
import copy, re
from enum import Enum
from pathlib import Path
from sys import stderr

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
        return f" {self.nid}{sep}{self.coord[0]}{sep}{self.coord[1]}{sep}{self.coord[2]}"


class Element():
    ''' Class for storing the information of an element
    '''
    def __init__(self, eid, nodes: list[Node]=[], type=ELEMENT_TYPE.UNKNOWN, source: tuple[int, int]=None, priorEid: int=None):

        # element id
        self._eid = eid

        # nodes
        self._nodes = nodes

        # type
        self._type = type

        # source file index and line number
        self._source = source

        # prior element id
        self._priorEid = priorEid

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
        if is_sequence(value) and all(isinstance(node, Node) for node in value):
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

    @property
    def priorEid(self):
        ''' Return the prior element id of the element
        '''
        return self._priorEid

    def toK(self, pid, sep=", "):
        ''' Return the element in K format
        '''
        return f" {self.priorEid}{sep}{pid}{sep}{sep.join([str(node.nid) for node in self.nodes])}"


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
        if is_sequence(value) and all(isinstance(elem, Element) for elem in value):
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

    @elementType.setter
    def elementType(self, value):
        ''' Set the element type of the part
        '''
        if isinstance(value, ELEMENT_TYPE):
            self._elementType = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def source(self):
        ''' Return the source of the part
        '''
        return self._source

    @property
    def header(self):
        ''' Return the header of the part
        '''
        return self._header

    @header.setter
    def header(self, value):
        ''' Set the header of the part
        '''
        if isinstance(value, str):
            self._header = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def secid(self):
        ''' Return the secid of the part
        '''
        return self._secid

    @secid.setter
    def secid(self, value):
        ''' Set the secid of the part
        '''
        if isinstance(value, int):
            self._secid = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def mid(self):
        ''' Return the mid of the part
        '''
        return self._mid

    @mid.setter
    def mid(self, value):
        ''' Set the mid of the part
        '''
        if isinstance(value, int):
            self._mid = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def eosid(self):
        ''' Return the eosid of the part
        '''
        return self._eosid

    @eosid.setter
    def eosid(self, value):
        ''' Set the eosid of the part
        '''
        if isinstance(value, int):
            self._eosid = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def hgid(self):
        ''' Return the hgid of the part
        '''
        return self._hgid

    @hgid.setter
    def hgid(self, value):
        ''' Set the hgid of the part
        '''
        if isinstance(value, int):
            self._hgid = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def grav(self):
        ''' Return the grav of the part
        '''
        return self._grav

    @grav.setter
    def grav(self, value):
        ''' Set the grav of the part
        '''
        if isinstance(value, int):
            self._grav = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def adpopt(self):
        ''' Return the adpopt of the part
        '''
        return self._adpopt

    @adpopt.setter
    def adpopt(self, value):
        ''' Set the adpopt of the part
        '''
        if isinstance(value, int):
            self._adpopt = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

    @property
    def tmid(self):
        ''' Return the tmid of the part
        '''
        return self._tmid

    @tmid.setter
    def tmid(self, value):
        ''' Set the tmid of the part
        '''
        if isinstance(value, int):
            self._tmid = value
        else:
            raise ValueError("Invalid input type for Part")

        # set the modified flag
        self.modified = True

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

    def toK(self, sep=", "):
        ''' Return the part in K format
        '''
        return f"{self._header}\n {self.pid}{sep}{self._secid}{sep}{self._mid}{sep}{self._eosid}{sep}{self._hgid}{sep}{self._grav}{sep}{self._adpopt}{sep}{self._tmid}"



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


def splitString(s, groupLengths, enforcedGroups):
    ''' Split a string into groups of specified lengths
    s: string to split
    groupLengths: list of group lengths
    enforcedGroups: list of booleans indicating whether the group is enforced
    '''
    pattern = ''.join(f'(.{{{length}}})' if enforced else f'(.{{{length}}})?' for length, enforced in zip(groupLengths, enforcedGroups))
    pattern = f'^{pattern}$'
    match = re.match(pattern, s)

    if match:
        groups = match.groups()
        return groups
    else:
        return None