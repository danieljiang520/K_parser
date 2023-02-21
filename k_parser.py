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

    def __init__(self, line: str='*KEYWORD', currKeyword: KEYWORD=KEYWORD.KEYWORD, lineNum: int=-1) -> None:
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
            if keyword in KEYWORD._member_names_:
                self.keyword = KEYWORD[keyword]
                self.keyword_args = keyword_args
            else:
                self.keyword = KEYWORD.UNKNOWN

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
                    if currKeyword.keyword is KEYWORD.PART:
                        self._modesDict[currKeyword.keyword](self, partList, currKeyword.keyword_args)
                        partList.clear()

                    # Update mode
                    currKeyword = kline

                # Data line
                elif kline.keyword in self._modesDict:
                    # if keyword is PART, Add kline to partlist
                    if kline.keyword is KEYWORD.PART:
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
            eprint(f"Invalid {kline.keyword.name}: Repeated node; id: {id}, coord: {coord}")
        else:
            self.nodesDict[id] = Node(coord, kline.lineNum)


    def __ELEMENT__(self, kline: KLine, keyword_args) -> None:
        ''' Parse ELEMENT_SHELL line
        '''

        # Error Handling
        if len(kline.values) < 3:
            eprint(f"Invalid {kline.keyword.name}: too less arguments; args: {kline.values}")
            return

        if keyword_args[0] != 'SHELL':
            # Discrete element
            return

        try:
            kline.values = [int(n) for n in kline.values]
        except ValueError:
            # Check if the types are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {keyword_args}")
            return

        eid = kline.values[0]
        pid = kline.values[1]
        nodes = [nid for nid in kline.values[2:10] if nid != 0]

        # Check if id already exists
        if eid in self.elementDict:
            # NOTE: This is a repeated element, we will skip it (element_solid and element_shell might have the same eid)
            # eprint(f"Repeated Element id: {eid}, coord: {nodes}")
            pass
        else:
            element = Element(nodes, kline.lineNum)
            self.elementDict[eid] = element
            self.partsDict[pid].elements.append(element)


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
        KEYWORD.ELEMENT: __ELEMENT__,
        KEYWORD.END: __END__,
        KEYWORD.KEYWORD: __KEYWORD__,
        KEYWORD.NODE: __NODE__,
        KEYWORD.PART: __PART__,
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


    def getElement(self, eid: int, outputType: int=0):
        ''' Return the ELEMENT given its ID

        Use outputType as:
            0 = list of coordinates of the corresponding nodes
            1 = indices of the corresponding nodes in self.nodes (better compatibility with vedo's
            mesh constructor)
        '''
        if eid not in self.elementDict:
            eprint(f"Element_Shell id: {eid} not in elementShellDict")
            return None

        element = self.elementDict[eid]

        if outputType == 0:
            return [self.nodesDict[nid].getCoord() for nid in element.nodes]

        # elif outputType == 1:
        #     return [self.nodesDict[nid] for nid in nodeIds]
        else :
            return None


    def getPart(self, pid: int, outputType: int=0) -> Union[list[list[Tuple[float]]], list[list[int]]]:
        ''' Return the PART given its ID

        Use outputType as:
            0 = list of list of coordinates of the corresponding element shells.
                e.g. [[(x1,y1,z1),(x2,y2,z2),(x3,y3,z3)],[(x4,y4,z4)]] where p1,p2,p3 compose
                ELEMENT_SHELL1 and p4 composes ELEMENT_SHELL2
            1 = indices of the corresponding nodes in self.nodes (better compatibility with vedo's
                mesh constructor)
                e.g. [[n1_ind,n2_ind,n3_ind],[n4_ind]]
        '''
        if pid not in self.partsDict:
            eprint(f"Part id: {pid} not in partsDict")
            return None

        part = self.partsDict[pid]
        if outputType == 0:
            return part.getVerts(), part.getFaces()

        else:
            return None


    def getAllParts(self):
        verts = []
        faces = []
        for pid in self.partsDict:
            data = self.getPart(pid)
            verts.extend(data[0])
            faces.extend(np.array(data[1]) + len(verts))
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
    # verts, faces = k_parser.getAllParts()
    coord = k_parser.getNodesCoord([100000,100001])
    # coord = k_parser.getNode(100000)
    verts = k_parser.getElement(100005)
    # k_parser.getPart(20003)

    print("Displaying object with vedo...")
    print(coord)
    print(verts)
    # m = mesh.Mesh(verts).show()

