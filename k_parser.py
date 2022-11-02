import argparse
from collections import defaultdict
from enum import Enum
# from scipy.spatial import KDTree
from sys import stderr
from typing import NamedTuple, Union, Tuple


# Public functions and types
#===================================================================================================

class Part(NamedTuple):
    header: str
    secid: int
    mid: int
    eosid: int
    hgid: int
    grav: int
    adpopt: int
    timid: int


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


class KLine:
    ''' Lexer for the parser
    Reference: https://supunsetunga.medium.com/writing-a-parser-getting-started-44ba70bb6cc9

    Attributes:
        is_keyword: bool
        is_valid: bool
        keyword: KEYWORD
        values: list
    '''

    def __init__(self, line: str, currKeyword: KEYWORD) -> None:
        line = line.split()
        firstItem = line[0]

        # Comment or empty line (technically empty line is invalid in a k file, but we will allow it)
        if firstItem[0] == '$' or not line:
            self.is_valid = False

        # Keyword line
        elif firstItem[0] == '*':
            keyword = firstItem[1:]
            self.is_valid = True
            self.is_keyword = True
            # if keyword is not defined, set keyword to UNKNOWN; otherwise, set keyword
            self.keyword = KEYWORD[firstItem[1:]] if keyword in KEYWORD._member_names_ else KEYWORD.UNKNOWN

        # Everything else
        else:
            self.is_valid = True
            self.is_keyword = False
            self.keyword = currKeyword
            self.values = line




def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


# Dyna Model Definition
#===================================================================================================

class DynaModel:
    ''' Parser for reading LS-DYNA k files
    '''

    def __init__(self, args: Union[list[str],  str]) -> None:
        '''
        '''
        self.elementShellDict = defaultdict(list[int]) # {eid1: [nid1, nid2, nid3, nid4]}
        self.nodes = []
        self.nodesIndDict = defaultdict(int)
        self.partsDict = defaultdict(list[int]) # {pid: [eid, eid, eid]}
        self.partsInfo = defaultdict(Part)

        if type(args) == list:
            for filename in args:
                self.__readFile(filename)

        elif type(args) == str:
            self.__readFile(args)

        else:
            print("unknown argument: ", args)
            return

        # self.nodesTree = KDTree(self.nodes)
        print("Finished Reading kfiles!")
        print(f"Total nodes: {len(self.nodesIndDict)}")
        print(f"Total elements_shells: {len(self.elementShellDict)}")
        print(f"Total parts: {len(self.partsDict)}")


    def __readFile(self, filename: str) -> None:
        '''
        '''

        # Keyword mode
        currMode = KEYWORD.KEYWORD
        partlist = []

        with open(filename) as reader:
            # Read the entire file line by line
            for line in reader:
                kline = KLine(line, currMode)

                # Skip comment or empty line
                if not kline.is_valid:
                    continue

                # Keyword line
                elif kline.is_keyword:
                    # Execute part
                    # NOTE: PART has multiple lines of data, therefore we record all the lines and
                    # process them at the end of the KEYWORD section
                    if currMode is KEYWORD.PART:
                        self.__modesDict[currMode](self, partlist)
                        partlist.clear()

                    # Update mode
                    currMode = kline.keyword

                # Data line
                elif kline.keyword in self.__modesDict:
                    # if keyword is PART, Add kline to partlist
                    if kline.keyword is KEYWORD.PART:
                        partlist.append(kline)
                    # Execute line
                    else:
                        self.__modesDict[kline.keyword](self, kline)


    def __NODE(self, kline: KLine) -> None:
        '''
        '''

        # Error Handling
        if len(kline.values) < 4:
            eprint(f"Invalid {kline.keyword.name}: too less arguments; args: {kline.values}")
            return

        try:
            id = int(kline.values[0])
            pos = (float(kline.values[1]), float(kline.values[2]), float(kline.values[3]))
        except ValueError:
            # Check if the types of id and pos are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {kline.values}")
            return

        # Check if id already exists
        if id in self.nodesIndDict:
            eprint(f"Invalid {kline.keyword.name}: Repeated node; id: {id}, coord: {pos}")
        else:
            self.nodesIndDict[id] = len(self.nodes)
            self.nodes.append(pos)


    def __ELEMENT_SHELL(self, kline: KLine) -> None:
        '''
        '''

        # Error Handling
        if len(kline.values) < 3:
            eprint(f"Invalid {kline.keyword.name}: too less arguments; args: {kline.values}")
            return

        try:
            kline.values = [int(n) for n in kline.values]
        except ValueError:
            # Check if the types are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {kline.values}")
            return

        eid = kline.values[0]
        pid = kline.values[1]
        nodes = [n for n in kline.values[2:] if n > 0]

        # Check if id already exists
        if eid in self.elementShellDict:
            eprint(f"Repeated Element id: {eid}, coord: {nodes}")
        else:
            self.elementShellDict[eid] = nodes
            self.partsDict[pid].append(eid)


    def __PART(self, klineList: list[KLine]) -> None:
        ''' NOTE: Only reading the basic information of Part
        '''

        if len(klineList) < 2:
            eprint(f"Invalid PART: too less arguments")
            return

        header = klineList[0].values[0]

        if len(klineList[1].values) != 8:
            eprint(f"Invalid PART: too less arguments")
            return

        args = [int(i) for i in klineList[1].values]
        pid = args[0]
        secid = args[1]
        mid = args[2]
        eosid = args[3]
        hgid = args[4]
        grav = args[5]
        adpopt = args[6]
        timid = args[7]

        self.partsInfo[pid] = Part(header, secid, mid, eosid, hgid, grav, adpopt, timid)


    def __KEYWORD(self, kline: KLine):
        pass


    def __END(self, kline: KLine):
        pass


    __modesDict = {
        KEYWORD.ELEMENT_SHELL: __ELEMENT_SHELL,
        KEYWORD.END: __END,
        KEYWORD.KEYWORD: __KEYWORD,
        KEYWORD.NODE: __NODE,
        KEYWORD.PART: __PART,
    }


# Public methods
#---------------------------------------------------------------------------------------------------

    def getNode(self, nid: int) -> Tuple[float]:
        '''
        '''
        if nid not in self.nodesIndDict:
            eprint(f"Node id: {nid} not in nodesIndDict")
            return () # empty tuple
        return self.nodes[self.nodesIndDict[nid]]


    def getNodes(self, nids: list[int]=[]) -> list[Tuple[float]]:
        return [self.getNode(nid) for nid in nids]


    def getAllNodes(self) -> list[Tuple[float]]:
        return self.nodes


    def getElementShell(self, eid: int, outputType: int=0) -> Union[list[Tuple[float]], list[int]]:
        ''' Return the ELEMENT_SHELL given its ID

        Use outputType as:
            0 = list of coordinantes of the corresponding nodes
            1 = indices of the cooresponding nodes in self.nodes (better compatibility with vedo's
            mesh constructor)
        '''
        if eid not in self.elementShellDict:
            eprint(f"Element_Shell id: {eid} not in elementShellDict")
            return []

        nodeIds = self.elementShellDict[eid]

        # NOTE: match requires python 3.10+
        match outputType:
            case 0:
                return self.getNodes(nodeIds)
            case 1:
                return [self.nodesIndDict[nid] for nid in nodeIds]
            case _:
                return None


    def getPart(self, pid: int, outputType: int=0) -> Union[list[list[Tuple[float]]], list[list[int]]]:
        ''' Return the PART given its ID

        Use outputType as:
            0 = list of list of coordinantes of the corresponding element shells.
                e.g. [[(x1,y1,z1),(x2,y2,z2),(x3,y3,z3)],[(x4,y4,z4)]] where p1,p2,p3 compose
                ELEMENT_SHELL1 and p4 composes ELEMENT_SHELL2
            1 = indices of the cooresponding nodes in self.nodes (better compatibility with vedo's
                mesh constructor)
                e.g. [[n1_ind,n2_ind,n3_ind],[n4_ind]]
        '''
        if pid not in self.partsDict:
            eprint(f"Part id: {pid} not in partsDict")
            return []

        elementShellIds = self.partsDict[pid]
        match outputType:
            case 0:
                return [self.getElementShell(eid) for eid in elementShellIds]

            case 1:
                faces = []
                # Append each element (in terms of its nodes' indices) to faces
                for eid in elementShellIds:
                    nodeIds = self.elementShellDict[eid]
                    faces.append([self.nodesIndDict[nid] for nid in nodeIds])
                return faces

            case _:
                return None


    def getAllPart(self):
        faces = []
        for pid in self.partsDict:
            faces.extend(self.getPart(pid, 1))
        return faces



# Main
#===================================================================================================


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f','--filepaths', nargs='+', help='Input k files\' filepaths', required=True)
    args = argparser.parse_args()
    k_parser = DynaModel(args=args.filepaths)


    # Example: display a part using vedo
    # command: python3 k_parser.py -f /Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k /Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k
    from vedo import mesh
    verts = k_parser.getAllNodes()
    # faces = k_parser.getPart(pid=20003, outputType=1)
    faces = k_parser.getAllPart()
    m = mesh.Mesh([verts, faces]).show()

    # k_parser.getNodes([100000,100001])
    # k_parser.getElementShell(100005)
    # k_parser.getPart(20003)