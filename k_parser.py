# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# -----------------------------------------------------------

# %% standard lib imports
from collections import defaultdict
from typing import Union
import argparse, fileinput, re

# %% first party imports
from utils import *

# %% third party imports
from vedo import mesh

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

    def __init__(self, line: str='*KEYWORD', currKeyword: KEYWORD_TYPE=KEYWORD_TYPE.KEYWORD, lineNum: int=None, fileInd: int=None) -> None:
        ''' Initialize KLine
        '''

        # split line by space, comma, and fixed-width whitespace (multiple spaces are treated as one space).
        line = re.findall(r'[^,\s]+', line)

        # Empty line
        if len(line) == 0:
            self.isValid = False
            return

        firstItem = line[0]

        # Initialize attributes
        self.isValid = False
        self.lineNum = lineNum
        self.fileInd = fileInd
        self.I10 = False

        # Comment or empty line (technically empty line is invalid in a k file, but we will allow it)
        if firstItem[0] == '$' or not line:
            return

        # Keyword line
        elif firstItem[0] == '*':
            self.isValid = True
            self.isKeyword = True

            firstUnderscoreIndex = firstItem.find('_')
            # keyword is string up until the first underscore
            keyword = firstItem[1:firstUnderscoreIndex].upper() if firstUnderscoreIndex != -1 else firstItem[1:].upper()
            # sub keyword category is string after the first underscore of the first word (if it exists)
            keywordSubtype = firstItem[firstUnderscoreIndex+1:] if firstUnderscoreIndex != -1 else None

            # if keyword is not defined, set keyword to UNKNOWN; otherwise, set keyword
            if keyword in KEYWORD_TYPE._member_names_:
                self.keyword = KEYWORD_TYPE[keyword]
                self.keywordSubtype = keywordSubtype
                self.__readKeywordArgs(line[1:])
            else:
                self.keyword = KEYWORD_TYPE.UNKNOWN

        # Everything else
        else:
            # If the current line is a Part header
            if currKeyword is KEYWORD_TYPE.PART and len(line) == 1 and isinstance(line[0], str):
                self.isPartHeader = True
            else:
                self.isPartHeader = False

            self.isValid = True
            self.isKeyword = False
            self.keyword = currKeyword
            self.values = line

    def __readKeywordArgs(self, keywordArgs:list[str]) -> None:
        ''' Read the arguments of a keyword
        '''
        for arg in keywordArgs:
            temp = arg.split('=')
            argName = temp[0].upper()
            argValue = temp[1] if len(temp) > 1 else None

            if argName == "I10":
                self.I10 = True if argValue == 'Y' else False






#===================================================================================================
# Dyna Model Definition
class DynaModel:
    ''' Parser for reading LS-DYNA k files
    '''

    # Spacing/Separator for printing (default to CSV format). Can be updated to match the input file
    nodesSeparator = ", "
    elementsSeparator = ", "
    partsSeparator = ", "

    def __init__(self, args: Union[list[str],  str]) -> None:
        ''' Initialize DynaModel

        nodesDict: dict[int, Node] - dictionary of nodes with node id as key.
                   Value can be None if not defined in the k file but referenced in the element
        elementDict: dict[int, Element] - dictionary of elements with element id as key.
        partsDict: dict[int, Part] - dictionary of parts with part id as key.
        '''

        # NOTE: in the future, we should use a local database (such as SQLite) to store the data for better performance
        self.nodesDict = defaultdict(Node)
        self.elementDict = defaultdict(Element)
        self.partsDict = defaultdict(Part)

        # Ls-dyna allows duplicated element IDs, as long as they are in different element types (e.g. beam, shell, solid, etc.).
        # e.g., an element_solid and element_shell might have the same eid
        self._negEid = -1

        self.filepaths = []
        if is_list_of_strings(args):
            self.filepaths = args
            for fileInd, filename in enumerate(args):
                self.__readFile(filename, fileInd)
        elif isinstance(args, str):
            self.filepaths = [args]
            self.__readFile(args)
        else:
            eprint("unknown argument: ", args)
            return

        print("Finished Reading kfiles!")
        print(f"Total nodes: {len(self.nodesDict)}")
        print(f"Total elements: {len(self.elementDict)}")
        print(f"Total parts: {len(self.partsDict)}")


    def __readFile(self, filename: str, fileInd: int=0) -> None:
        ''' Read a k file
        '''

        # Keyword mode
        currKeywordLine = KLine()
        partList = []

        with open(filename, "rt") as reader:
            # Read the entire file line by line
            for i, line in enumerate(reader):
                kline = KLine(line, currKeywordLine.keyword, i, fileInd)

                # Skip comment or empty line
                if not kline.isValid:
                    continue

                # Keyword line
                elif kline.isKeyword:
                    # Execute part
                    # NOTE: PART has multiple lines of data, therefore we record all the lines and
                    # process them at the end of the section
                    if currKeywordLine.keyword is KEYWORD_TYPE.PART:
                        self._modesDict[currKeywordLine.keyword](self, partList, currKeywordLine)
                        partList.clear()

                    # Update mode
                    currKeywordLine = kline

                # Data line
                elif kline.keyword in self._modesDict:
                    # if keyword is PART, Add kline to partlist
                    if kline.keyword is KEYWORD_TYPE.PART:
                        # if the current line is a part header, execute the previous part
                        if kline.isPartHeader and len(partList) > 0:
                            self._modesDict[kline.keyword](self, partList, currKeywordLine)
                            partList = [kline]
                        else:
                            partList.append(kline)

                    # Execute line
                    else:
                        self._modesDict[kline.keyword](self, kline, currKeywordLine)


    def __NODE__(self, kline: KLine, currKeywordLine: KLine) -> None:
        ''' Parse NODE line
        '''

        # Error Handling
        if len(kline.values) < 4:
            eprint(f"Invalid {kline.keyword.name}: too less arguments; args: {kline.values}")
            return

        # NOTE: might not need to use and try and except block since make3d will check for this
        try:
            nid = int(kline.values[0])
            coord = (float(kline.values[1]), float(kline.values[2]), float(kline.values[3]))
        except ValueError:
            # Check if the types of id and pos are correct
            eprint(f"Invalid {kline.keyword.name}: bad type; args: {kline.values}")
            return

        # Check if id already exists
        if nid in self.nodesDict:
            node = self.nodesDict[nid]
            if node.source is not None:
                eprint(f"Invalid {kline.keyword.name}: Repeated node; id: {nid}, coord: {coord}")
                return
            else:
                # Update node
                # NOTE: by specifying _coord and _source, we are updating the node quietly (without marking modified)
                self.nodesDict[nid]._coord = coord
                self.nodesDict[nid]._source = (kline.fileInd, kline.lineNum)
        else:
            # Add node to dictionary
            self.nodesDict[nid] = Node(nid, coord, (kline.fileInd, kline.lineNum))


    def __ELEMENT__(self, kline: KLine, currKeywordLine: KLine) -> None:
        ''' Parse ELEMENT line
        '''

        # Element type specific settings
        elementType = ELEMENT_TYPE[currKeywordLine.keywordSubtype] if currKeywordLine.keywordSubtype in ELEMENT_TYPE._member_names_ else ELEMENT_TYPE.UNKNOWN
        numNodes = 0
        if elementType == ELEMENT_TYPE.UNKNOWN:
            # Disregard unknown element type
            # eprint(f"Invalid {kline.keyword.name}: unknown element type; args: {kline.values}")
            return
        elif elementType == ELEMENT_TYPE.BEAM:
            numNodes = 3
        elif elementType == ELEMENT_TYPE.DISCRETE:
            numNodes = 2
        elif elementType == ELEMENT_TYPE.SHELL:
            numNodes = 8 # or 4
        elif elementType == ELEMENT_TYPE.SOLID:
            numNodes = 8

        # Error Handling: number of arguments
        '''
        Fixed-length format
        default: 8 characters per field
        I10 (*KEYWORD I10=Y or *ELEMENT_SHELL %): 10 characters per field

        e.g.,
        *ELEMENT_SHELL
        880880238800011488159065881792458817920788179207
        '''
        try:
            if len(kline.values) == 1: # Fixed-length format
                if currKeywordLine.I10: # 10 characters per field
                    kline.values = [kline.values[0][i:i+10] for i in range(0, len(kline.values[0]), 10)]
                else: # 8 characters per field
                    kline.values = [kline.values[0][i:i+8] for i in range(0, len(kline.values[0]), 8)]

            eid = int(kline.values[0])
            pid = int(kline.values[1])

            nodes = []
            for nid in map(int, kline.values[2:2+numNodes]):
                # 0 is an invalid node id
                if nid == 0:
                    continue

                if nid not in self.nodesDict:
                    # Add node to dictionary
                    self.nodesDict[nid] = Node(nid=nid)
                nodes.append(self.nodesDict[nid])

            if len(nodes) != numNodes and (elementType == ELEMENT_TYPE.SHELL and len(nodes) != 4):
                eprint(f"Invalid {kline.keyword.name}_{currKeywordLine.keywordSubtype}: expected {numNodes} nodes, received {len(nodes)} nodes; args (eid, pid, nid1, nid2...): {kline.values}")
                return

        except ValueError:
            # Check if the types are correct
            eprint(f"Invalid {kline.keyword.name}_{currKeywordLine.keywordSubtype}: bad type; args: {kline.values}")
            return

        # This is a repeated element with the same id and type!
        if eid in self.elementDict:
            if self.elementDict[eid].type == elementType:
                eprint(f"Repeated element: eid: {eid}, pid: {pid}, elementType: {elementType}")
                return
            else:
                newElement = Element(eid=self._negEid, nodes=nodes, type=elementType, source=(kline.fileInd, kline.lineNum), priorEid=eid)
                self.elementDict[self._negEid] = newElement
                self._negEid -= 1
        else:
            newElement = Element(eid=eid, nodes=nodes, type=elementType, source=(kline.fileInd, kline.lineNum), priorEid=eid)
            self.elementDict[eid] = newElement

        # Check if Part exists and Part's element type matches (each Part can only have one type of elements)
        if pid not in self.partsDict:
            # Specify element type
            self.partsDict[pid] = Part(pid=pid, elementType=elementType)

        else:
            # Check if element type matches
            if len(self.partsDict[pid].elements) == 0:
                self.partsDict[pid]._elementType = elementType

            elif self.partsDict[pid].elementType != elementType:
                eprint(f"Invalid {kline.keyword.name}_{currKeywordLine.keywordSubtype}: Part's element type mismatch; pid: {pid}, Part's element type: {self.partsDict[pid]._elementType}, element type: {elementType}")
                return

        # Add element to Part
        self.partsDict[pid].elements.add(newElement)


    def __PART__(self, klineList: list[KLine], keywordSubtype: str) -> None:
        ''' NOTE: Only reading the basic information of Part
        '''

        if len(klineList) < 2:
            eprint(f"Invalid PART: too less lines: {len(klineList)}")
            return

        header = klineList[0].values[0]

        # Must have at least one argument: pid
        # NOTE: in the DYNA datasheet, it has pid, secid, mid, eosid, hgid, grav, adpopt, tmid listed as required arguments
        # However, in some files, there are only pid, secid, and mid. Therefore, we only check for pid
        if len(klineList[1].values) < 1:
            eprint(f"Invalid PART: too less arguments: {klineList[1].values}")
            return

        vals = [int(i) for i in klineList[1].values] + [0] * (8 - len(klineList[1].values))
        pid, secid, mid, eosid, hgid, grav, adpopt, tmid = vals

        # Check duplicate Part
        if pid in self.partsDict:
            if self.partsDict[pid].source is not None:
                eprint(f"Repeated Part: pid: {pid}")
                return
            else:
                # Update Part
                self.partsDict[pid]._source = (klineList[0].fileInd, klineList[0].lineNum, klineList[-1].lineNum)

                self.partsDict[pid]._header = header
                self.partsDict[pid]._secid = secid
                self.partsDict[pid]._mid = mid
                self.partsDict[pid]._eosid = eosid
                self.partsDict[pid]._hgid = hgid
                self.partsDict[pid]._grav = grav
                self.partsDict[pid]._adpopt = adpopt
                self.partsDict[pid]._tmid = tmid
        else:
            # Add Part to dictionary
            self.partsDict[pid] = Part(pid=pid, source=(klineList[0].fileInd, klineList[0].lineNum, klineList[-1].lineNum), header=header, secid=secid, mid=mid, eosid=eosid, hgid=hgid, grav=grav, adpopt=adpopt, tmid=tmid)


    def __KEYWORD__(self, kline: KLine):
        pass


    def __END__(self, kline: KLine):
        pass


    def __createModifiedList(self):
        ''' Create a list of the sources of modified nodes, elements and parts
        '''
        # Create a list of dictionaries
        # NOTE: it is perhaps better to use a list of sorted lists
        modifiedLists = [{} for _ in range(len(self.filepaths))]

        for node in self.nodesDict.values():
            if node.modified:
                modifiedLists[node.source[0]][node.source[1]] = (node.source[1], node)

        for element in self.elementDict.values():
            if element.modified:
                modifiedLists[element.source[0]][element.source[1]] = (element.source[1], element, self.__findElementPartCorrespondences(element))
                # modifiedElements.add(element)

        for part in self.partsDict.values():
            if part.modified:
                modifiedLists[part.source[0]][part.source[1]] = (part.source[2], part)

        return modifiedLists

    def __findElementPartCorrespondences(self, element: Element):
        ''' Find the parts that the element belongs to
        '''
        for part in self.partsDict.values():
            if part.elementType != element.type:
                continue

            if element in part.elements:
                return part.pid

        return None


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
        return [self.nodesDict[nid].coord() for nid in nids]


    def getAllNodesCoord(self) -> list[Node]:
        return [node.getCoord() for node in self.nodesDict]


    def getElement(self, eid: int) -> Element:
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

        return [node.coord() for node in element.nodes]


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

        return part.getPartData()


    def getAllPartsData(self, verbose: bool=False):
        # Create a set of the vertices that only appear in the part
        verts = list({v.coord for part in self.partsDict.values() for element in part.elements for v in element.nodes})
        elements = {element for part in self.partsDict.values() for element in part.elements}

        if verbose:
            print(f"Unreferenced nodes: {len(self.nodesDict) - len(verts)}")
            print(f"Unreferenced elements: {len(self.elementDict) - len(elements)}")

        # Create a mapping from the new vertex list to the new index
        vert_map = dict(zip(verts, range(len(verts))))

        # Iterate over the reduced vertex list and update the face indices
        faces = [[vert_map[v.coord] for v in element.nodes] for element in elements]
        return verts, faces


    def saveFile(self):
        ''' Save the parsed file to a new file
        '''
        modifiedLists = self.__createModifiedList()
        print(f"Modified list: {modifiedLists}")

        for i, modifiedList in enumerate(modifiedLists):
            if len(modifiedList) == 0:
                continue

            prevEnd = -1

            # The fileinput.input function is used to read the contents of the file and replace the lines in place.
            # The inplace=True argument ensures that the changes are written back to the file.
            with fileinput.input(self.filepaths[i], inplace=True) as file:
                for lineNum, line in enumerate(file):
                    if lineNum <= prevEnd:
                        continue

                    if lineNum in modifiedList:

                        obj = modifiedList[lineNum][1]
                        # NOTE: using default separator (CSV) for now. Plan to dynamically change this to match the input file in the future
                        if isinstance(obj, Element):
                            print(obj.toK(pid=modifiedList[lineNum][2], sep=', '), end='\n')
                            prevEnd = modifiedList[lineNum][0]
                        elif isinstance(obj, Node) or isinstance(obj, Part):
                            print(obj.toK(sep=', '), end='\n')
                            prevEnd = modifiedList[lineNum][0]
                        else:
                            eprint(f"Object type not recognized: {type(obj)}")
                    else:
                        print(line, end='')


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
        k_viewer = DynaModel(args=args.filepaths)
    elif args.directory:
        args.directory = getAllKFilesInFolder(args.directory)
        k_viewer = DynaModel(args=args.directory)
    else:
        eprint("No input filepaths or directory provided")
        exit(1)

    """
    Example: display a part using vedo
    python3 k_parser.py -d data/UMTRI_M50
    python3 k_parser.py -f data/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k data/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k
    python3 k_parser.py -f data/Manual-chair-geometry.k
    """

    print("starting...")
    # Examples for M50
    # coords = k_parser.getAllNodesCoord()
    verts, faces = k_viewer.getAllPartsData(verbose=True)
    # verts, faces = k_parser.getPartData(20003) # M50
    # coord = k_parser.getNodesCoord([100000,100001]) # M50
    # node = k_parser.getNode(100000) # M50
    # element = k_parser.getElement(204116) # M50
    # part = k_parser.getPart(20003) # M50

    # Examples for Manual-chair
    # verts, faces = k_parser.getAllPartsData(verbose=True)
    # verts, faces = k_parser.getPartData(250004) # Manual-chair
    # node = k_parser.getNode(2112223) # Manual-chair
    # element = k_parser.getElement(2110001) # Manual-chair
    # part = k_parser.getPart(210002) # Manual-chair

    # Examples for modifying the Manual-chair file
    # node.coord = (0,0,0)
    # element.nodes = [node, node, node, node]
    # part.header = "PART NEW HEADER"
    # k_parser.saveFile()

    print("Displaying object with vedo...")
    m = mesh.Mesh([verts, faces]).show()

