import pathlib, argparse
from collections import defaultdict
from sys import stderr
from vedo import pointcloud, mesh
from typing import NamedTuple


#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

class Part(NamedTuple):
    header: str
    secid: int
    mid: int
    eosid: int
    hgid: int
    grav: int
    adpopt: int
    timid: int


def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

class K_Parser:
    ''' Parser for reading LS-DYNA k files
    '''

    def __init__(self, args: argparse.ArgumentParser) -> None:
        '''
        '''
        self.elementShellDict = defaultdict(list[int]) # {eid1: [nid1, nid2, nid3, nid4]}
        self.nodes = pointcloud.Points()
        self.nodesIndDict = defaultdict(int)
        self.partsDict = defaultdict(list[int]) # {pid: [eid, eid, eid]}
        self.partsInfo = defaultdict(Part)

        for filename in args.filepaths:
            self.readFile(filename)

        print("Finished Reading kfiles!")
        print(f"Total nodes: {len(self.nodesIndDict)}")
        print(f"Total elements_shells: {len(self.elementShellDict)}")
        print(f"Total parts: {len(self.partsDict)}")


    def readFile(self, filename: str) -> None:
        '''
        '''

        # Keyword mode
        mode = "*KEYWORD"
        listOfLines = []

        with open(filename) as reader:
            # Read the entire file line by line
            for line in reader:

                # Skip comment
                if line[0] == '$' or line == '':
                    continue

                # Change mode
                elif line[0] == '*':
                    # Execute previous mode
                    if mode in self.modesDict:
                        self.modesDict[mode](self, listOfLines)

                    # Update mode
                    listOfLines.clear()
                    mode = line.split()[0]

                # Append line to listOFLines
                else:
                    listOfLines.append(line.strip().split())


    def NODE(self, listOfLines: list[list[str]]) -> None:
        '''
        '''

        numNodes = len(listOfLines)
        nodesList = [None] * numNodes # Reserve space for optimization

        for i, line in enumerate(listOfLines):
            id = int(line[0])
            pos = (float(line[1]), float(line[2]), float(line[3]))

            # Check if id already exists
            if id in self.nodesIndDict:
                eprint(f"Repeated Node id: {id}, coord: {pos}")
            else:
                self.nodesIndDict[id] = i
                nodesList[i] = pos

        self.nodes = pointcloud.Points(inputobj=nodesList + list(self.nodes.points()))


    def ELEMENT_SHELL(self, listOfLines: list[list[str]]) -> None:
        '''
        '''

        for line in listOfLines:
            line = [int(n) for n in line]
            eid = line[0]
            pid = line[1]
            nodes = [n for n in line[2:] if n > 0]

            # Check if id already exists
            if eid in self.elementShellDict:
                eprint(f"Repeated Element id: {eid}, coord: {nodes}")
            else:
                self.elementShellDict[eid] = nodes
                self.partsDict[pid].append(eid)


    def PART(self, listOfLines: list[list[str]]) -> None:
        ''' NOTE: Only reading the basic information of Part
        '''

        if len(listOfLines) < 2:
            return

        header = listOfLines[0][0]
        args = [int(i) for i in listOfLines[1]]
        pid = args[0]
        secid = args[1]
        mid = args[2]
        eosid = args[3]
        hgid = args[4]
        grav = args[5]
        adpopt = args[6]
        timid = args[7]

        self.partsInfo[pid] = Part(header, secid, mid, eosid, hgid, grav, adpopt, timid)


    def KEYWORD(self, listOfLines: list[list[str]]):
        pass


    def END(self, listOfLines: list[list[str]]):
        pass


    modesDict = {
        "*ELEMENT_SHELL": ELEMENT_SHELL,
        # "*ELEMENT_SOLID": ELEMENT_SHELL, # Use same function as ELEMENT_SHELL
        "*END": END,
        "*KEYWORD": KEYWORD,
        "*NODE": NODE,
        "*PART": PART,
    }


#   ------------------------------------------------------------------------------------------------

    def getNode(self, nid: int) -> list:
        if nid in self.nodesIndDict:
            return list(self.nodes.points()[self.nodesIndDict[nid]])
        return []


    def getNodes(self, nids: list[int]=[], display: bool=False) -> pointcloud.Points:
        nodes = [self.getNode(nid) for nid in nids]
        pts = pointcloud.Points(nodes)

        if display:
            pts.show()

        return pts


    def getElementShell(self, eid: int, display: bool=False) -> mesh.Mesh:
        if eid not in self.elementShellDict:
            eprint(f"Element_Shell id: {eid} not in elementShellDict")
            m = mesh.Mesh()
        else:
            nodeIds = self.elementShellDict[eid]
            verts = list(self.nodes.points())
            faces = [[self.nodesIndDict[nid] for nid in nodeIds ]]
            m = mesh.Mesh([verts, faces])

        if display:
            m.backColor('violet').lineColor('tomato').lineWidth(2).show()

        return m


    def getPart(self, pid: int, display: bool=False) -> mesh.Mesh:
        if pid not in self.partsDict:
            eprint(f"Part id: {pid} not in partsDict")
            m = mesh.Mesh()

        else:
            elementShellIds = self.partsDict[pid]
            verts = list(self.nodes.points())
            faces = []
            for eid in elementShellIds:
                if eid in self.elementShellDict:
                    nodeIds = self.elementShellDict[eid]
                    faces.append([self.nodesIndDict[nid] for nid in nodeIds])

            m = mesh.Mesh([verts, faces])

            if display:
                m.show()

        return m


    def showAll(self) -> None:
        print(len(self.partsDict))
        parts = []
        for pid in self.partsDict:
            parts.append(self.getPart(pid))

        mesh.merge(parts).show()





#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

# parser = K_Parser([r'/Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k',
#           r'/Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k'])
# p = parser.getNode(100000)
# print(p)
# p = parser.getNodes([100000,100001])
# p.show()
# parser.getElementShell(100005)
# parser.getPart(10003, display=True)
# parser.showAll()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f','--filepaths', nargs='+', help='Input k files\' filepaths', required=True)
    args = argparser.parse_args()
    k_parser = K_Parser(args)
    k_parser.getPart(10003, display=True)