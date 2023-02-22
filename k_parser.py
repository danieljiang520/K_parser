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
        '''
        self.nodesDict = defaultdict(Node)
        self.elementDict = defaultdict(Element)
        self.partsDict = defaultdict(Part)
        # self.partsInfo = defaultdict(Part)


        if is_list_of_strings(args):
            for filename in args:
                self.__readFile__(filename)

        elif isinstance(args, str):
            self.__readFile__(args)

        else:
            eprint("unknown argument: ", args)
            return

        # self.nodesTree = KDTree(self.nodes)
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
            if self.nodesDict[id].lineNum != -1:
                eprint(f"Invalid {kline.keyword.name}: Repeated node; id: {id}, coord: {coord}")
                return
            else:
                # Update node
                self.nodesDict[id].coord = coord
                self.nodesDict[id].lineNum = kline.lineNum
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

            nodes = set()
            for nid in map(int, kline.values[2:2+numNodes]):
                # 0 is an invalid node id
                if nid == 0:
                    continue

                if nid not in self.nodesDict:
                    # Add node to dictionary
                    self.nodesDict[nid] = Node()
                nodes.add(self.nodesDict[nid])

        except ValueError:
            # Check if the types are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {kline.values}")
            return

        # Add element to dictionary
        if eid in self.elementDict:
            # NOTE: This is a repeated element (element_solid and element_shell might have the same eid)
            self.elementDict[eid].addType(type)
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

    def getNode(self, nid: int):
        ''' Return the node's coordinates given its ID
        '''
        if nid not in self.nodesDict:
            eprint(f"Node id: {nid} not in nodesIndDict")
            return None
        return self.nodesDict[nid]


    def getNodesCoord(self, nids: list[int]=[]):
        ''' Return a list of nodes' coordinates given a list of IDs
        '''
        return [self.nodesDict[nid].getCoord() for nid in nids]


    def getAllNodes(self):
        return [node.getCoord() for node in self.nodesDict]


    def getElement(self, eid: Union[int, Element]):
        ''' Return the ELEMENT given its ID
        '''
        if eid not in self.elementDict:
            eprint(f"Element id: {eid} not in elementShellDict")
            return None
        return self.elementDict[eid]


    def getElementCoord(self, element: Union[int, Element], outputType: int=0):
        ''' Return the ELEMENT given its ID

        Use outputType as:
            0 = list of coordinates of the corresponding nodes
            1 = indices of the corresponding nodes in self.nodes (better compatibility with vedo's
            mesh constructor)
        '''
        if isinstance(element, int):
            element = self.getElement(element)

        if not isinstance(element, Element):
            return None

        if outputType == 0:
            return [node.getCoord() for node in element.nodes]
        else :
            return None


    def getPart(self, pid: int):
        ''' Return the PART given its ID
        '''
        if pid not in self.partsDict:
            eprint(f"Part id: {pid} not in partsDict")
            return None
        return self.partsDict[pid]


    def getPartData(self, part: Union[int, Part], outputType: int=0, faceStart: int=0) -> Union[list[list[Tuple[float]]], list[list[int]]]:
        ''' Return the PART given its ID

        Use outputType as:
            0 = list of list of coordinates of the corresponding element shells.
                e.g. [[(x1,y1,z1),(x2,y2,z2),(x3,y3,z3)],[(x4,y4,z4)]] where p1,p2,p3 compose
                ELEMENT_SHELL1 and p4 composes ELEMENT_SHELL2
            1 = indices of the corresponding nodes in self.nodes (better compatibility with vedo's
                mesh constructor)
                e.g. [[n1_ind,n2_ind,n3_ind],[n4_ind]]
        '''
        if isinstance(part, int):
            part = self.getPart(part)

        if not isinstance(part, Part):
            return None

        if outputType == 0:
            verts = []
            faces = []
            for element in part.elements:
                faces.append([i for i in range(len(verts) + faceStart, len(verts) + len(element.nodes) + faceStart)])
                verts.extend(self.getElementCoord(element, outputType=0))
            return verts, faces
        else:
            return None


    def getAllPartsData(self):
        verts = []
        faces = []
        for part in self.partsDict:
            data = self.getPartData(part, faceStart=len(verts))
            if data is not None:
                verts.extend(data[0])
                faces.extend(data[1])
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
    # nodes = k_parser.getAllNodes()
    # verts, faces = k_parser.getPart(pid=20003)
    verts, faces = k_parser.getAllPartsData()
    # coord = k_parser.getNodesCoord([100000,100001])
    # coord = k_parser.getNode(100000)
    # verts = k_parser.getElement(100005)
    # k_parser.getPart(20003)

    print(len(verts))
    print(len(faces))

    print(f"verts: {verts[-1]}")
    print(f"faces: {faces[-1]}")

    print("Displaying object with vedo...")
    m = mesh.Mesh([verts, faces]).show()

