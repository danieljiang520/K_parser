# -----------------------------------------------------------
# Author: Daniel Jiang (danieldj@umich.edu)
# -----------------------------------------------------------

# %% standard lib imports
import argparse

# %% first party imports
from k_parser import *
from utils import *

# %% third party imports
from vedo import mesh

#===================================================================================================
# VedoViewer class
class VedoViewer(DynaModel):
    '''
    Class to display the model using vedo
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def showAll(self, verbose: bool=True) -> mesh.Mesh:
        verts, faces = self.getAllPartsData(verbose=verbose)
        if verbose:
            self.__debugInfo(verts, faces)
        print("Displaying object with vedo...")
        return mesh.Mesh([verts, faces]).show()


    def showPart(self, pid: Union[int, str], verbose: bool=True) -> mesh.Mesh:
        verts, faces = self.getPartData(pid)
        if verbose:
            self.__debugInfo(verts, faces)
        print("Displaying object with vedo...")
        return mesh.Mesh([verts, faces]).show()


    def __debugInfo(self, verts, faces):
        print(f"len(verts): {len(verts)}")
        print(f"len(faces): {len(faces)}")
        print(f"first vert: {verts[0]}")
        print(f"first face: {faces[0]}")
        print(f"last vert: {verts[-1]}")
        print(f"last face: {faces[-1]}")


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
        k_viewer = VedoViewer(args.filepaths)
    elif args.directory:
        args.directory = getAllKFilesInFolder(args.directory)
        k_viewer = VedoViewer(args.directory)
    else:
        eprint("No input filepaths or directory provided")
        exit(1)

    """
    Example: display a part using vedo
    python3 viewer.py -d data/UMTRI_M50
    python3 viewer.py -f data/UMTRI_M50/UMTRI_HBM_M50_V1.2_Mesh_Components.k data/UMTRI_M50/UMTRI_HBM_M50_V1.2_Nodes.k
    python3 viewer.py -f data/Manual-chair-geometry.k
    """

    # display the model
    k_viewer.showAll()