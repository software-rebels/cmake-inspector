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
    os.chdir(directory)
    extract.initialize(directory, ".", False)
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
    global extension_type
    extension_type = "ECM"
    if len(argv) > 2:
        currentIndex = 2
        if argv[currentIndex] == 'find_package_dir':
            dirs = argv[currentIndex + 1].split(',')
            extract.find_package_lookup_directories.append(dirs)
            currentIndex += 2

        if argv[currentIndex] == 'version':
            cmake_version = argv[currentIndex + 1]
            for idx in range(len(extract.find_package_lookup_directories)):
                extract.find_package_lookup_directories[idx] = extract.find_package_lookup_directories[idx].replace(
                    ':version', cmake_version)
    getGraph(argv[1])
    extract.vmodel.export()


if __name__ == "__main__":
    main(sys.argv)
