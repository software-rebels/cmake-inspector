from analyze import printFilesForATarget
from collections import defaultdict
import pickle

class GraphQuery:

    def __init__(self, vmodel, lookup):
        self._vmodel = vmodel
        self._lookup = lookup
        self._targets = []
        self.targetToFlatted = dict()

    def getFlattenForTargets(self):
        self._vmodel.findAndSetTargets()
        for idx, item in enumerate(self._vmodel.targets):
            self._targets.append(item.getValue())

        for target in self._targets:
            self.targetToFlatted[target] = printFilesForATarget(self._vmodel, self._lookup, target)


    def saveTheDict(self, projectName):
        with open(f'{projectName}_dict.pickle', 'wb') as handle:
            pickle.dump(self.targetToFlatted, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def flatAllAndSave(self, projectName):
        self.getFlattenForTargets()
        self.saveTheDict(projectName)

    def getImpactedTargets(self, changedFile):
        result = defaultdict(list)
        for target, flatted in self.targetToFlatted.items():
            for condition, files in flatted.items():
                if changedFile in files:
                    result[target].append(condition)
        return result
