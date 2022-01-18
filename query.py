import time
import pickle
from analyze import getFilesForATarget
from z3 import *
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

    def __init__(self, vmodel, lookup):
        self._vmodel = vmodel
        self._lookup = lookup
        self._targets = []
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

    def serializeConditionList(self, conditions):
        result = set()
        for condition in conditions:
            result.add(self.SerializedCondition(str(condition), condition.__class__.__name__))
        return frozenset(result)

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
                    result[target] = list(self.serializeConditionList(condition))

        return result

    def getImpactedTargetsByFileAndCondition(self, changedFile, requestedConditions):
        result = defaultdict(list)
        for target, flatted in self.targetToFlatted.items():
            for condition, files in flatted.items():
                if changedFile in files:
                    solver = Solver()
                    solver.add(condition)
                    solver.add(requestedConditions)
                    if solver.check() == sat:
                        result[target] = list(self.serializeConditionList(condition))
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

            server.register_function(get_file_lists)
            server.register_function(get_impact)
            server.register_function(get_impact_by_file_condition)

            # Run the server's main loop
            server.serve_forever()