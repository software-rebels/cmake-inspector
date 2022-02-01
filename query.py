import time
import pickle
from analyze import getFilesForATarget
from z3 import *
from pydriller import Git
from collections import defaultdict
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler


class GraphQuery:

    class SerializedCondition:
        def __init__(self, name, refType):
            self._name = name
            self._type = refType

        def deserialize(self):
            if self._type == "BoolRef":
                return Bool(self._name)
            if self._type == "ArithRef":
                return Int(self._name)
            if self._type == "SeqRef":
                return String(self._name)
            raise "NotImplemented!"

        def __hash__(self):
            return hash(self._name)

    def __init__(self, vmodel, lookup, projectPath=None):
        self._vmodel = vmodel
        self._lookup = lookup
        self._targets = []
        self._path = projectPath
        self.targetToFlatted = dict()
        self.setOfFiles = set()

    def getFlattenForTargets(self):
        self._vmodel.findAndSetTargets()
        for idx, item in enumerate(self._vmodel.targets):
            self._targets.append(item.getValue())

        for target in self._targets:
            self.targetToFlatted[target] = getFilesForATarget(self._vmodel, self._lookup, target)

        for target, flatted in self.targetToFlatted.items():
            for condition, files in flatted.items():
                self.setOfFiles.update(files)

        # timestr = time.strftime("%Y%m%d-%H%M%S")
        # self.saveTheDict(timestr)

    def serializeConditionList(self, condition):
        return self.SerializedCondition(str(condition), condition.__class__.__name__)

    def saveTheDict(self, projectName):
        dictToSave = dict()
        for target, flatted in self.targetToFlatted.items():
            dictToSave[target] = dict()
            for condition, files in flatted.items():
                key = self.serializeConditionList(condition)
                dictToSave[target][key] = files
        with open(f'{projectName}_dict.pickle', 'wb') as handle:
            pickle.dump(dictToSave, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def getImpactedTargets(self, changedFile):
        result = defaultdict(list)
        for target, flatted in self.targetToFlatted.items():
            for condition, files in flatted.items():
                if changedFile in files:
                    result[target].append(self.serializeConditionList(condition))

        return result

    def getImpactedTargetsByFileAndCondition(self, changedFile, requestedConditions, result=None):
        if result is None:
            result = defaultdict(list)
        for target, flatted in self.targetToFlatted.items():
            for condition, files in flatted.items():
                if changedFile in files:
                    solver = Solver()
                    solver.add(condition)
                    solver.add(requestedConditions)
                    if solver.check() == sat:
                        serialized = self.serializeConditionList(condition)
                        if serialized not in result[target]:
                            result[target].append(self.serializeConditionList(condition))
        return result

    def getImpactedTargetsByCommitAndCondition(self, commit_id, requestedConditions):
        gr = Git(self._path)
        commit = gr.get_commit(commit_id)
        result = defaultdict(list)
        for modified_file in commit.modified_files:
            self.getImpactedTargetsByFileAndCondition(modified_file.old_path or modified_file.new_path,
                                                      requestedConditions,
                                                      result)
        return result

    def startRPCServer(self):
        # Restrict to a particular path.
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        # Create server
        with SimpleXMLRPCServer(('localhost', 8008),
                                requestHandler=RequestHandler) as server:
            server.register_introspection_functions()

            def get_file_lists():
                return list(self.setOfFiles)

            def get_impact(filename):
                return dict(self.getImpactedTargets(filename))

            def get_impact_by_file_condition(filename, conditions):
                g = Goal()
                for condition in conditions:
                    serializedCondition = self.SerializedCondition(condition['_name'],
                                                                   condition['_type'])
                    g.add(serializedCondition.deserialize() == condition['value'])
                return dict(self.getImpactedTargetsByFileAndCondition(filename, g))

            def get_impacted_by_commit_condition(commit_id, conditions):
                g = Goal()
                for condition in conditions:
                    serializedCondition = self.SerializedCondition(condition['_name'],
                                                                   condition['_type'])
                    g.add(serializedCondition.deserialize() == condition['value'])
                return dict(self.getImpactedTargetsByCommitAndCondition(commit_id, g))

            server.register_function(get_file_lists)
            server.register_function(get_impact)
            server.register_function(get_impact_by_file_condition)
            server.register_function(get_impacted_by_commit_condition)

            # Run the server's main loop
            server.serve_forever()
