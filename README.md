# K_parser
## Usage
```
usage: k_parser.py [-h] -f FILEPATHS [FILEPATHS ...]

optional arguments:
  -h, --help            show this help message and exit
  -f FILEPATHS [FILEPATHS ...], --filepaths FILEPATHS [FILEPATHS ...]
                        Input k files' ABSOLUTE filepaths
```
Example:
```
% python3 k_parser.py -f /Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k /Users/danieljiang/Documents/UMTRI/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k
```

## Structure
Reference from https://canvas.kth.se/courses/6376/files/1398637/download?verifier=vKYrSZc7FmwSxnsJbH6QYX0fb8lTc2UXjszIKX6I&wrap=1

- Part
  -  Element_Shell
      - Node

## Functions & Examples
### getNode
```
def getNode(self, nid: int) -> list
```
Returns [x,y,z]

### getNodes
```
def getNodes(self, nids: list[int]=[], display: bool=False) -> pointcloud.Points
```
Returns a pointcloud.Points object containing all nodes

Example:
```
k_parser.getNodes([100000,100001], display=True)
```
<img width="859" alt="Screen Shot 2022-10-20 at 09 27 34" src="https://user-images.githubusercontent.com/71047773/196961597-4642c149-d19c-450b-8b7c-707636ddeea5.png">

### getElementShell
```
def getElementShell(self, eid: int, display: bool=False) -> mesh.Mesh
```
Returns a mesh object containing the element

Example:
```
k_parser.getElementShell(100005, display=True)
```
<img width="859" alt="Screen Shot 2022-10-20 at 09 31 22" src="https://user-images.githubusercontent.com/71047773/196962490-a613c2c8-f2a7-4da7-9d7c-1e72b2027fc9.png">

### getPart
```
def getPart(self, pid: int, display: bool=False) -> mesh.Mesh
```
Returns a mesh object representing the part

Example:
```
k_parser.getPart(10003, display=True)
```
<img width="859" alt="Screen Shot 2022-10-20 at 09 32 29" src="https://user-images.githubusercontent.com/71047773/196962773-27be71fe-6f92-4848-9bf9-4dc77406dde0.png">
