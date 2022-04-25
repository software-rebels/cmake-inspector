import csv
import sys
import os

from z3.z3 import Goal, Solver
from typing import Dict

from algorithms import extract
from algorithms.analyze import printDefinitionsForATarget, printFilesForATarget
from data_model.datastructs import LiteralNode, Lookup
from algorithms.utils import util_create_and_add_refNode_for_variable
from data_model.vmodel import VModel


def getGraph(directory):
    VModel.clearInstance()
    Lookup.clearInstance()
    os.chdir(directory)
    extract.initialize(directory, ".", False)
    extract.vmodel.findAndSetTargets()
    extract.linkDirectory()
    return extract.vmodel, extract.lookupTable


def getFlattenedDefinitionsForTarget(target: str, raw: bool = False):
    return printDefinitionsForATarget(extract.vmodel, extract.lookupTable, target, raw)


def getFlattenedFilesForTarget(target: str, raw: bool = False):
    return printFilesForATarget(extract.vmodel, extract.lookupTable, target, raw)


def getTargets():
    extract.vmodel.findAndSetTargets()
    for idx, item in enumerate(extract.vmodel.targets):
        print(f'{idx}. {item.getValue()}')


def exportFlattenedListToCSV(flattened: Dict, fileName: str):
    CSV_HEADERS = ['file', 'condition']
    with open(fileName, 'w') as csv_out:
        writer = csv.DictWriter(csv_out, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for key in flattened.keys():
            writer.writerow({
                'file': flattened[key],
                'condition': key
            })


# def main(argv):
#     global extension_type
#     extension_type = "ECM"
#     if len(argv) > 2:
#         currentIndex = 2
#         if argv[currentIndex] == 'find_package_dir':
#             dirs = argv[currentIndex + 1].split(',')
#             extract.find_package_lookup_directories.append(dirs)
#             currentIndex += 2

#         if argv[currentIndex] == 'version':
#             cmake_version = argv[currentIndex + 1]
#             for idx in range(len(extract.find_package_lookup_directories)):
#                 extract.find_package_lookup_directories[idx] = extract.find_package_lookup_directories[idx].replace(
#                     ':version', cmake_version)
#     getGraph(argv[1])
#     extract.vmodel.export()


# more restrictions!
# 1) only care about boolrefs
# 2) recursively retrieve all children primitives
# 3) build a set of primitive elements

def main(argv):
    vmodel, lookuptable = getGraph(argv[1])
    s = Solver()
    for target in vmodel.targets:
        if target.definitions is not None:
            definitions = getFlattenedDefinitionsForTarget(target.getValue(), True)
            print(f"Vmodel sources for target {target.getValue()}:", getFlattenedFilesForTarget(target.getValue(), True))        
            print(f"Vmodel definitions for target {target.getValue()}:", definitions)
            
            for cond, def_set in definitions.items():
                print(f"type(cond): {type(cond[0])}", cond, type(cond[0].children()[0]) if len(cond[0].children()) > 0 else True, cond[0].num_args())
                print(f"definitions: {def_set}")

if __name__ == "__main__":
    main(sys.argv)
