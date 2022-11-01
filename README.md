# K_parser
## Usage
```
usage: k_parser.py [-h] -f FILEPATHS [FILEPATHS ...]

optional arguments:
  -h, --help            show this help message and exit
  -f FILEPATHS [FILEPATHS ...], --filepaths FILEPATHS [FILEPATHS ...]
                        Input k files' ABSOLUTE filepaths
```
Example for two k_files:
```
% python3 k_parser.py -f /Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k /Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k
```

## Structure
References:
- https://canvas.kth.se/courses/6376/files/1398637/download?verifier=vKYrSZc7FmwSxnsJbH6QYX0fb8lTc2UXjszIKX6I&wrap=1
- https://supunsetunga.medium.com/writing-a-parser-getting-started-44ba70bb6cc9


- Part
  -  Element_Shell
      - Node

## Functions & Examples
### getNode
```
def getNode(self, nid: int) -> Tuple[float]
```
Returns (x,y,z)

### getNodes
```
def getNodes(self, nids: list[int]=[]) -> list[Tuple[float]]:
```
Returns a list of coordinants

Example:
```
k_parser.getNodes([100000,100001])
```
<img width="859" alt="Screen Shot 2022-10-20 at 09 27 34" src="https://user-images.githubusercontent.com/71047773/196961597-4642c149-d19c-450b-8b7c-707636ddeea5.png">

### getAllNodes
returns all nodes

Example:

<img width="859" alt="Screen Shot 2022-10-20 at 16 10 59" src="https://user-images.githubusercontent.com/71047773/197048423-84a6f3d9-dfe3-4b81-99a2-34f10db5e4dd.png">

### getElementShell
```
def getElementShell(self, eid: int, outputType: int=0) -> Union[list[Tuple[float]], list[int]]:
    ''' Return the ELEMENT_SHELL given its ID

    Use outputType as:
        0 = list of coordinantes of the corresponding nodes
        1 = indices of the cooresponding nodes in self.nodes (better compatibility with vedo's
        mesh constructor)
    '''
```
Returns the ELEMENT_SHELL with different format options

Example:
```
k_parser.getElementShell(100005)
```
<img width="859" alt="Screen Shot 2022-10-20 at 09 31 22" src="https://user-images.githubusercontent.com/71047773/196962490-a613c2c8-f2a7-4da7-9d7c-1e72b2027fc9.png">

### getPart
```
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
```
Returns the part with different format options

Example:
```
k_parser.getPart(10003)
```
<img width="859" alt="Screen Shot 2022-10-20 at 09 32 29" src="https://user-images.githubusercontent.com/71047773/196962773-27be71fe-6f92-4848-9bf9-4dc77406dde0.png">

### getAllPart
Get all parts

<img width="859" alt="Screen Shot 2022-10-20 at 09 35 35" src="https://user-images.githubusercontent.com/71047773/196963449-29b726a8-bc85-4166-af22-5683e831073f.png">
