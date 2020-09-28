import logging
import pickle

from datastructs import VModel, Lookup, RefNode, TargetNode, LiteralNode, CustomCommandNode, \
    flattenAlgorithmWithConditions, FinalTarget, FinalSelectNode, Node, recursivelyResolveReference
from pydriller import RepositoryMining
import itertools
import glob
from collections import defaultdict
import pprint
import json
import csv


# import matplotlib.pyplot as plt


def printInputVariablesAndOptions(vmodel: VModel, lookup: Lookup):
    print("#### Input variables are:")
    for item in vmodel.getNodeSet():
        if isinstance(item, RefNode):
            if not item.getChildren():
                print(item.getName())
    print("#### Input options are:")
    for option in vmodel.options:
        print(option)


def printSourceFiles(vmodel: VModel, lookup: Lookup):
    targets = extractTargets(lookup)

    print("### PRINTING TARGETS:")
    for t in targets:
        print(t.getName())

    visitedNodes = set()
    for t in targets:
        assert isinstance(t, TargetNode)
        visitedNodes.add(t)
        targetChildren = VModel.getNodeChildren(t.sources)
        print("### Source files for {}:".format(t.getName()))
        sourceFiles = []
        for item in targetChildren:
            if isinstance(item, LiteralNode):  # or item.getChildren() is None:
                if '*' in item.getName():
                    sourceFiles += glob.glob(item.getName())
                else:
                    sourceFiles.append(item.getName())
            if isinstance(item, CustomCommandNode):  # This could be a file command, thus we may have to evaluate it
                command_result = item.evaluate()
                if command_result:
                    sourceFiles += command_result
        print(sourceFiles)


def extractTargets(lookup):
    targets = []
    for scope in lookup.items:
        for k in scope:
            if isinstance(scope.get(k), TargetNode):
                targets.append(scope.get(k))
    return targets


def checkForCyclesAndPrint(vmodel: VModel, lookup: Lookup, node: Node, visited=[], recStack=[]) -> bool:
    visited.append(node)
    recStack.append(node)

    children = node.getChildren()
    if isinstance(node, TargetNode):
        for item in node.linkLibrariesConditions.keys():
            children.append(item)

    for child in children:
        if child not in visited:
            if checkForCyclesAndPrint(vmodel, lookup, child, visited, recStack):
                return True
            elif child in recStack:
                return True

    recStack.remove(node)
    return False


def printFilesForATarget(vmodel: VModel, lookup: Lookup, target: str, output=False):
    logging.info("##### Start printing files for target " + target)
    targetNode = lookup.getKey("t:{}".format(target))
    assert isinstance(targetNode, TargetNode)
    flattenedFiles = flattenAlgorithmWithConditions(targetNode.sources)
    for library, conditions in targetNode.linkLibrariesConditions.items():
        flattenedFiles += flattenAlgorithmWithConditions(library, conditions)

    # Now we should expand the cached results
    finalFlattenList = []
    for item in flattenedFiles:
        if isinstance(item[0], Node):
            finalFlattenList += recursivelyResolveReference(item[0], item[1])
        else:
            finalFlattenList.append(item)

    result = defaultdict(set)
    for item in finalFlattenList:
        test_cond = set()
        for cond in item[1]:
            # TODO: For some reason
            if cond[0] is None:
                continue
            test_cond.add("{}:{}".format(cond[0].getValue(), str(cond[1])))
        if test_cond:
            result[" && ".join(sorted(test_cond))].add(item[0])
        elif item[0]:
            result[""].add(item[0])

    # Post-processing
    # 1. Resolve wildcard path
    for key in list(result):
        for item in list(result[key]):
            if '*' in item:
                result[key].update(set(glob.glob(item)))
                result[key].remove(item)
    # 2. Find a file which appears in all the paths
    files = set.intersection(*list(result.values()))
    if files:
        for key in list(result):
            result[key] = result[key] - files
            if not result[key]:
                del result[key]
        result['NO_MATTER_WHAT'].update(files)

    # json.dumps does not work on set. Using this function, we convert set to a list.
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError

    if output:
        print(json.dumps(result, default=set_default, sort_keys=True, indent=4))

    with open('result.pkl', 'wb') as f:
        pickle.dump(result, f, pickle.HIGHEST_PROTOCOL)
    with open('result.json', 'w') as f:
        json.dump(result, f, default=set_default, sort_keys=True, indent=4)
    return result


def buildRuntimeGraph(vmodel: VModel, lookup: Lookup):
    targets = extractTargets(lookup)
    for target in targets:
        flattenedFiles = flattenAlgorithmWithConditions(target.sources)
        finalTarget = FinalTarget("{}::final".format(target.getName()))
        fileSelectNode = FinalSelectNode("{}::Select::FILES".format(target.getName()))
        finalTarget.files = fileSelectNode
        for item in flattenedFiles:
            literalNode = LiteralNode(item[0])
            test_cond = set()
            for cond in item[1]:
                test_cond.add("{}:{}".format(cond[0].getValue(), str(cond[1])))
            fileSelectNode.addChild((literalNode, ",".join(test_cond)))

        vmodel.nodes.append(finalTarget)
        vmodel.export()


def doChangeAnalysis(fileNode):
    vmodel = VModel.getInstance()
    unitTestsName = set()
    for testTarget in vmodel.testTargets:
        if vmodel.pathWithCondition(testTarget, fileNode):
            unitTestsName.add(testTarget.getName())
    print("Impacted unit tests: {}".format(unitTestsName))


def doGitAnalysis(repoPath):
    csvHeader = ['hash', 'filename']
    rows = []

    vmodel = VModel.getInstance()
    founded = set()
    notFounded = set()
    extension = {}

    # Generate all possible combinations for True, False
    l = [False, True]
    possibleAssignments = list(itertools.product(l, repeat=len(vmodel.options)))
    for assigment in possibleAssignments:
        csvHeader.append(str(assigment))

    totalNumberOfTargets = len(vmodel.targets)
    changedTargets = set()
    changedTargetsForEachCommit = {}

    foundedModification = 0
    notFoundedModification = 0
    for index, commit in enumerate(RepositoryMining(
            # We are interested in commits after bc7e017112bb8e37a3103879148be718a48f5023 in zlib project
            repoPath, from_commit="a2d71e8e66530c325bfce936f3805ccff5831b62").traverse_commits()):
        # repoPath, from_commit="7707894d4857e2524ed9c48d972aa321dee850f8").traverse_commits()):
        if index > 100:
            break
        changedTargetsForEachCommit[commit.hash] = set()
        print("Analyze Commit ID: {}".format(commit.hash))
        for modification in commit.modifications:

            node = vmodel.findNode(modification.filename) or \
                   vmodel.findNode(modification.old_path) or \
                   vmodel.findNode(modification.new_path)

            if not node:
                notFounded.add(modification.filename)
                notFoundedModification += 1
                fileExt = modification.filename.split(".")[-1]
                if fileExt in extension:
                    extension[fileExt] += 1
                else:
                    extension[fileExt] = 0
            else:
                print("Changed file: {}".format(modification.filename))
                newRow = [commit.hash, modification.filename]
                # doChangeAnalysis(node)
                founded.add(modification.filename)
                foundedModification += 1
                for assignment in possibleAssignments:
                    conditions = {}
                    impactedTargets = set()
                    for keyIndex, key in enumerate(vmodel.options.keys()):
                        conditions[key] = assignment[keyIndex]
                    # print("Conditions are: {}".format(conditions))
                    for target in vmodel.targets:
                        if vmodel.pathWithCondition(target, node, **conditions):
                            impactedTargets.add(target.getName())
                    # print("Impacted targets are:{}".format(impactedTargets))
                    newRow.append(len(impactedTargets))
                rows.append(newRow)
                # for target in vmodel.targets:
                #     # TODO: We should use our new path finder function
                #     if node in vmodel.getNodeChildren(target):
                #         changedTargets.add(target)
                #         changedTargetsForEachCommit[commit.hash].add(target)
    print("Founded files:{}, not founded files:{} and founded modify:{}, not founded modify:{}"
          .format(len(founded), len(notFounded), foundedModification, notFoundedModification))
    # with open('csvResult.csv', 'w') as csvFile:
    #     csvWriter = csv.writer(csvFile)
    #     csvWriter.writerow(csvHeader)
    #     csvWriter.writerows(rows)
    # for key in extension:
    #     print("Extension: {}, freq: {}".format(key, extension[key]))
    lists = sorted(extension.items(), key=lambda item: item[1], reverse=True)
    x, y = zip(*lists)
    plt.bar(x, y)
    plt.xticks(rotation=90)
    plt.savefig("plot.pdf")
