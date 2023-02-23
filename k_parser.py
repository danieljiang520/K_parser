# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# -----------------------------------------------------------

# %% standard lib imports
from collections import defaultdict
import re, argparse
from typing import Union, Tuple

# %% first party imports
from utils import *

#===================================================================================================
# KLine Class
class KLine:
    ''' Lexer for the parser
    Reference: https://supunsetunga.medium.com/writing-a-parser-getting-started-44ba70bb6cc9

    Attributes:
        is_keyword: bool
        is_valid: bool
        keyword: KEYWORD
        keyword_args: list[str]
        values: list
    '''

    def __init__(self, line: str='*KEYWORD', currKeyword: KEYWORD_TYPE=KEYWORD_TYPE.KEYWORD, lineNum: int=-1) -> None:
        ''' Initialize KLine
        '''

        # split line by space, comma, and fixed-width whitespace (multiple spaces are treated as one space).
        line = re.findall(r'[^,\s]+', line)

        # Empty line
        if len(line) == 0:
            self.is_valid = False
            return

        firstItem = line[0]

        # Comment or empty line (technically empty line is invalid in a k file, but we will allow it)
        if firstItem[0] == '$' or not line:
            self.is_valid = False

        # Keyword line
        elif firstItem[0] == '*':
            temp = firstItem[1:].split('_')
            keyword = temp[0].upper()
            keyword_args = temp[1:]
            self.is_valid = True
            self.is_keyword = True
            # if keyword is not defined, set keyword to UNKNOWN; otherwise, set keyword
            if keyword in KEYWORD_TYPE._member_names_:
                self.keyword = KEYWORD_TYPE[keyword]
                self.keyword_args = keyword_args
            else:
                self.keyword = KEYWORD_TYPE.UNKNOWN

        # Everything else
        else:
            self.is_valid = True
            self.is_keyword = False
            self.keyword = currKeyword
            self.values = line

        self.lineNum = lineNum


#===================================================================================================
# Dyna Model Definition
class DynaModel:
    ''' Parser for reading LS-DYNA k files
    '''

    def __init__(self, args: Union[list[str],  str]) -> None:
        ''' Initialize DynaModel

        nodesDict: dict[int, Node] - dictionary of nodes with node id as key.
                   Value can be None if not defined in the k file but referenced in the element
        elementDict: dict[int, Element] - dictionary of elements with element id as key.
        partsDict: dict[int, Part] - dictionary of parts with part id as key.
        '''
        self.nodesDict = defaultdict(Node)
        self.elementDict = defaultdict(Element)
        self.partsDict = defaultdict(Part)

        if is_list_of_strings(args):
            for filename in args:
                self.__readFile__(filename)
        elif isinstance(args, str):
            self.__readFile__(args)
        else:
            eprint("unknown argument: ", args)
            return

        print("Finished Reading kfiles!")
        print(f"Total nodes: {len(self.nodesDict)}")
        print(f"Total elements: {len(self.elementDict)}")
        print(f"Total parts: {len(self.partsDict)}")


    def __readFile__(self, filename: str) -> None:
        ''' Read a k file
        '''

        # Keyword mode
        currKeyword = KLine()
        partList = []

        with open(filename) as reader:
            # Read the entire file line by line
            for i, line in enumerate(reader):
                kline = KLine(line, currKeyword.keyword, i)

                # Skip comment or empty line
                if not kline.is_valid:
                    continue

                # Keyword line
                elif kline.is_keyword:
                    # Execute part
                    # NOTE: PART has multiple lines of data, therefore we record all the lines and
                    # process them at the end of the section
                    if currKeyword.keyword is KEYWORD_TYPE.PART:
                        self._modesDict[currKeyword.keyword](self, partList, currKeyword.keyword_args)
                        partList.clear()

                    # Update mode
                    currKeyword = kline

                # Data line
                elif kline.keyword in self._modesDict:
                    # if keyword is PART, Add kline to partlist
                    if kline.keyword is KEYWORD_TYPE.PART:
                        partList.append(kline)
                    # Execute line
                    else:
                        self._modesDict[kline.keyword](self, kline, currKeyword.keyword_args)


    def __NODE__(self, kline: KLine, keyword_args: list[str]) -> None:
        ''' Parse NODE line
        '''

        # Error Handling
        if len(kline.values) < 4:
            eprint(f"Invalid {kline.keyword.name}: too less arguments; args: {kline.values}")
            return

        # NOTE: might not need to use and try and except block since make3d will check for this
        try:
            id = int(kline.values[0])
            coord = (float(kline.values[1]), float(kline.values[2]), float(kline.values[3]))
        except ValueError:
            # Check if the types of id and pos are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {kline.values}")
            return

        # Check if id already exists
        if id in self.nodesDict:
            node = self.nodesDict[id]
            if node is not None:
                eprint(f"Invalid {kline.keyword.name}: Repeated node; id: {id}, coord: {coord}")
                return
            else:
                # Update node
                self.nodesDict[id] = Node(coord, kline.lineNum)
        else:
            # Add node to dictionary
            self.nodesDict[id] = Node(coord, kline.lineNum)


    def __ELEMENT__(self, kline: KLine, keyword_args) -> None:
        ''' Parse ELEMENT line
        '''

        # Error Handling
        if len(kline.values) < 3:
            eprint(f"Invalid {kline.keyword.name}: too less arguments; args: {kline.values}")
            return

        type = ELEMENT_TYPE[keyword_args[0]] if keyword_args[0] in ELEMENT_TYPE._member_names_ else ELEMENT_TYPE.UNKNOWN

        # Element type specific settings
        numNodes = 0
        if type == ELEMENT_TYPE.UNKNOWN:
            # Disregard unknown element type
            # eprint(f"Invalid {kline.keyword.name}: unknown element type; args: {kline.values}")
            return
        elif type == ELEMENT_TYPE.BEAM:
            numNodes = 3
        elif type == ELEMENT_TYPE.DISCRETE:
            numNodes = 2
        elif type == ELEMENT_TYPE.SHELL:
            numNodes = 8
        elif type == ELEMENT_TYPE.SOLID:
            numNodes = 8

        try:
            eid = int(kline.values[0])
            pid = int(kline.values[1])

            nodes = []
            for nid in map(int, kline.values[2:2+numNodes]):
                # 0 is an invalid node id
                if nid == 0:
                    continue

                if nid not in self.nodesDict:
                    # Add node to dictionary
                    self.nodesDict[nid] = None
                nodes.append(self.nodesDict[nid])

        except ValueError:
            # Check if the types are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {kline.values}")
            return

        # Add element to dictionary
        if eid in self.elementDict:
            # NOTE: This is a repeated element
            # e.g., element_solid and element_shell might have the same eid
            self.elementDict[eid].addType(type)
            self.elementDict[eid].addLineNum(kline.lineNum)
        else:
            self.elementDict[eid] = Element(nodes, type, kline.lineNum)

        # NOTE: an element can be used by multiple parts. Add element to part
        self.partsDict[pid].elements.add(self.elementDict[eid])


    def __PART__(self, klineList: list[KLine], keyword_args) -> None:
        ''' NOTE: Only reading the basic information of Part
        '''

        if len(klineList) < 2:
            eprint(f"Invalid PART: too less arguments")
            return

        header = klineList[0].values[0]

        if len(klineList[1].values) != 8:
            eprint(f"Invalid PART: too less arguments")
            return

        pid, secid, mid, eosid, hgid, grav, adpopt, timid = [int(i) for i in klineList[1].values]
        self.partsDict[pid].lineNum = klineList[0].lineNum
        self.partsDict[pid].header = header
        self.partsDict[pid].secid = secid
        self.partsDict[pid].mid = mid
        self.partsDict[pid].eosid = eosid
        self.partsDict[pid].hgid = hgid
        self.partsDict[pid].grav = grav
        self.partsDict[pid].adpopt = adpopt
        self.partsDict[pid].timid = timid


    def __KEYWORD__(self, kline: KLine):
        pass


    def __END__(self, kline: KLine):
        pass


    _modesDict = {
        KEYWORD_TYPE.ELEMENT: __ELEMENT__,
        KEYWORD_TYPE.END: __END__,
        KEYWORD_TYPE.KEYWORD: __KEYWORD__,
        KEYWORD_TYPE.NODE: __NODE__,
        KEYWORD_TYPE.PART: __PART__,
    }


#---------------------------------------------------------------------------------------------------
# Public methods

    def getNode(self, nid: int) -> Node:
        ''' Return the node's coordinates given its ID
        '''
        if nid not in self.nodesDict:
            eprint(f"Node id: {nid} not in nodesIndDict")
            return None
        return self.nodesDict[nid]


    def getNodes(self, nids: list[int]=[]) -> list[Node]:
        ''' Return a list of nodes given a list of IDs
        '''
        return [self.nodesDict[nid] for nid in nids]


    def getNodesCoord(self, nids: list[int]=[]) -> list[tuple[float, float, float]]:
        ''' Return a list of nodes' coordinates given a list of IDs
        '''
        return [self.nodesDict[nid].getCoord() for nid in nids]


    def getAllNodesCoord(self) -> list[Node]:
        return [node.getCoord() for node in self.nodesDict]


    def getElement(self, eid: Union[int, Element]) -> Element:
        ''' Return the ELEMENT given its ID
        '''
        if eid not in self.elementDict:
            eprint(f"Element id: {eid} not in elementShellDict")
            return None
        return self.elementDict[eid]


    def getElementCoords(self, element: Union[int, Element]) -> list[tuple[float, float, float]]:
        ''' Return a list of coordinates of the element's nodes given the element or eid
        '''
        if isinstance(element, int):
            element = self.getElement(element)

        if not isinstance(element, Element):
            return None

        return [node.getCoord() for node in element.nodes]


    def getPart(self, pid: int) -> Part:
        ''' Return the PART given its ID
        '''
        if pid not in self.partsDict:
            eprint(f"Part id: {pid} not in partsDict")
            return None
        return self.partsDict[pid]


    def getPartData(self, part: Union[int, Part]):
        ''' Return the PART data given its ID

            verts = list of coordinates of the corresponding element shells.
                    e.g. [(x1,y1,z1),(x2,y2,z2),(x3,y3,z3),(x4,y4,z4),(x5,y5,z5),(x6,y6,z6)]
            faces = indices of the corresponding nodes in verts (compatible with vedo's
                    mesh constructor)
                    e.g. [[n1_ind,n2_ind,n3_ind,n4_ind],[n4_ind,n5_ind,n6_ind]]
        '''
        if isinstance(part, int):
            part = self.getPart(part)

        if not isinstance(part, Part):
            return None

        verts = list({v.coord for element in part.elements for v in element.nodes})
        vert_map = dict(zip(verts, range(len(verts))))

        faces = [[vert_map[v.coord] for v in element.nodes] for element in part.elements]
        return verts, faces


    def getAllPartsData(self):

        verts = list({v.coord for part in self.partsDict.values() for element in part.elements for v in element.nodes})
        elements = {element for part in self.partsDict.values() for element in part.elements}
        # verts = [node.coord for node in self.nodesDict.values()]
        # elements = self.elementDict.values()

        vert_map = dict(zip(verts, range(len(verts))))

        faces = [[vert_map[v.coord] for v in element.nodes] for element in elements]
        return verts, faces



#===================================================================================================
# Main
if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    group = argparser.add_mutually_exclusive_group(required=True)
    # list of filepaths
    group.add_argument('-f','--filepaths', nargs='+', help='Input k files\' filepaths', required=False)
    # single string of the directory path
    group.add_argument('-d','--directory', help='Input k files\' directory', required=False)
    args = argparser.parse_args()

    if args.filepaths:
        k_parser = DynaModel(args=args.filepaths)
    elif args.directory:
        args.directory = getAllKFilesInFolder(args.directory)
        k_parser = DynaModel(args=args.directory)
    else:
        eprint("No input filepaths or directory provided")
        exit(1)

    """
    Example: display a part using vedo
    python3 k_parser.py -d data/UMTRI_M50
    python3 k_parser.py -f data/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k data/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k
    """

    from vedo import mesh
    print("starting...")
    # Examples for M50
    # coords = k_parser.getAllNodesCoord()
    # verts, faces = k_parser.getAllPartsData()
    # verts, faces = k_parser.getPartData(20003) # M50
    # coord = k_parser.getNodesCoord([100000,100001]) # M50
    # node = k_parser.getNode(100000) # M50
    # coords = k_parser.getElementCoord(100005) # M50
    # part = k_parser.getPart(20003) # M50

    # Examples for Manual-chair
    verts, faces = k_parser.getAllPartsData()
    # verts, faces = k_parser.getPartData(250004) # Manual-chair
    # node = k_parser.getNode(2112223) # Manual-chair
    # coords = k_parser.getElementCoords(2110001) # Manual-chair

    print(f"len(verts): {len(verts)}")
    print(f"len(faces): {len(faces)}")

    print(f"last vert: {verts[-1]}")
    print(f"last face: {faces[-1]}")

    print("Displaying object with vedo...")
    m = mesh.Mesh([verts, faces]).show()

