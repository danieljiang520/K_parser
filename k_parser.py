import argparse
from collections import defaultdict
from sys import stderr
from typing import NamedTuple, Union
from vedo import mesh, pointcloud


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

class DynaModel:
    ''' Parser for reading LS-DYNA k files
    '''

    def __init__(self, args: Union[argparse.ArgumentParser, list[str],  str]) -> None:
        '''
        '''
        self.elementShellDict = defaultdict(list[int]) # {eid1: [nid1, nid2, nid3, nid4]}
        self.nodes = pointcloud.Points()
        self.nodesIndDict = defaultdict(int)
        self.partsDict = defaultdict(list[int]) # {pid: [eid, eid, eid]}
        self.partsInfo = defaultdict(Part)

        if type(args) == argparse.ArgumentParser:

            for filename in args.filepaths:
                self.readFile(filename)

        elif type(args) == list:
            for filename in args:
                self.readFile(filename)

        elif type(args) == str:
            self.readFile(args)

        else:
            print("unknown argument: ", args)
            return


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
                line = line.strip()

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

                # Append line to listOfLines
                else:
                    listOfLines.append(line.split())


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
            return self.nodes.points()[self.nodesIndDict[nid]]
        return []


    def getNodes(self, nids: list[int]=[], display: bool=False) -> pointcloud.Points:
        nodes = [self.getNode(nid) for nid in nids]
        pts = pointcloud.Points(nodes)

        if display:
            pts.ps(10).show()

        return pts


    def getElementShell(self, eid: int, display: bool=False) -> mesh.Mesh:
        if eid not in self.elementShellDict:
            eprint(f"Element_Shell id: {eid} not in elementShellDict")
            m = mesh.Mesh()
        else:
            nodeIds = self.elementShellDict[eid]
            verts = self.nodes.points()
            faces = [[self.nodesIndDict[nid] for nid in nodeIds ]]
            m = mesh.Mesh([verts, faces])

        if display:
            m.show()

        return m


    def getPart(self, pid: int, display: bool=False) -> mesh.Mesh:
        if pid not in self.partsDict:
            eprint(f"Part id: {pid} not in partsDict")
            m = mesh.Mesh()

        else:
            elementShellIds = self.partsDict[pid]
            verts = self.nodes.points()
            faces = []
            for eid in elementShellIds:
                nodeIds = self.elementShellDict[eid]
                faces.append([self.nodesIndDict[nid] for nid in nodeIds])

            m = mesh.Mesh([verts, faces])

            if display:
                m.show()

        return m


    def showAll(self) -> mesh.Mesh:
        '''
        NOTE: Previous use mesh.merge on the mesh of every part obtained from getPart. However,
        iterating to get all faces is faster and more efficient
        '''

        verts = self.nodes.points()
        faces = []
        for pid in self.partsDict:
            elementShellIds = self.partsDict[pid]
            for eid in elementShellIds:
                nodeIds = self.elementShellDict[eid]
                faces.append([self.nodesIndDict[nid] for nid in nodeIds])

        m = mesh.Mesh([verts, faces]).show()
        return m


    def showAllNodes(self) -> pointcloud.Points:
        self.nodes.show()
        return self.nodes






#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f','--filepaths', nargs='+', help='Input k files\' filepaths', required=True)
    args = argparser.parse_args()
    k_parser = DynaModel(args)

    # k_parser.getNodes([100000,100001], display=True)
    # k_parser.getElementShell(100005, display=True)
    k_parser.getPart(20003, display=True)
    # k_parser.showAll()
    # k_parser.showAllNodes()