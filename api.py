import csv
import sys
import os

from typing import Dict
from analyze import printDefinitionsForATarget, printFilesForATarget
from datastructs import LiteralNode, Lookup
from utils import util_create_and_add_refNode_for_variable
import extract
from vmodel import VModel


def getGraph(directory):
    VModel.clearInstance()
    Lookup.clearInstance()
    extract.initialize()
    extract.project_dir = directory
    util_create_and_add_refNode_for_variable('CMAKE_CURRENT_SOURCE_DIR', LiteralNode(extract.project_dir, extract.project_dir))
    util_create_and_add_refNode_for_variable('CMAKE_SOURCE_DIR', LiteralNode(extract.project_dir, extract.project_dir))
    extract.parseFile(os.path.join(extract.project_dir, 'CMakeLists.txt'))
    extract.vmodel.findAndSetTargets()
    extract.linkDirectory()
    return extract.vmodel, extract.lookupTable


def getFlattenedDefintionsForTarget(target: str):
    return printDefinitionsForATarget(extract.vmodel, extract.lookupTable, target)


def getFlattenedFilesForTarget(target: str):
    return printFilesForATarget(extract.vmodel, extract.lookupTable, target)


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


def main(argv):
    getGraph(argv[1])
    extract.vmodel.export()
    # vmodel.checkIntegrity()
    # vmodel.findAndSetTargets()
    # doGitAnalysis(project_dir)
    # code.interact(local=dict(globals(), **locals()))
    # printInputVariablesAndOptions(vmodel, lookupTable)
    # printSourceFiles(vmodel, lookupTable)
    # testNode = vmodel.findNode('${CLIENT_LIBRARIES}_662')
    # flattenAlgorithmWithConditions(testNode)
    files = printFilesForATarget(extract.vmodel, extract.lookupTable, argv[2], True)
    print(files)


if __name__ == "__main__":
    main(sys.argv)
