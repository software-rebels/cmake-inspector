import understand

UND_DB_PATH = "/Users/mehranmeidani/uWaterloo/Research/etlegacy/etlegacy.und"

db = understand.open(UND_DB_PATH)
funcs = db.ents("function ~unresolved ~volatile")


def getHashKey(funcName, fileName):
    return f"{fileName},{funcName}"


class FuncEntity:
    lookup = dict()

    def __init__(self, name, fileName):
        self.name = name
        self.fileName = fileName
        self.dependsBy = set()

    @classmethod
    def get(cls, funcName, fileName):
        return cls.lookup[getHashKey(funcName, fileName)]

    @classmethod
    def getOrCreate(cls, funcName, fileName):
        if not getHashKey(funcName, fileName) in cls.lookup:
            cls.lookup[getHashKey(funcName, fileName)] = FuncEntity(funcName, fileName)
        return cls.get(funcName, fileName)

    def addDependBy(self, fEntity):
        self.dependsBy.add(fEntity)

    def getDependsBy(self):
        return self.dependsBy

    def __repr__(self):
        return getHashKey(self.name, self.fileName)

    def __hash__(self):
        return hash(repr(self))


def getFileName(ent):
    while ent.kindname() != "File":
        ent = ent.parent()
    return ent.longname()


for func in funcs:
    entity = FuncEntity.getOrCreate(func.name(), getFileName(func))
    for depend in func.refs("Call", "function ~unresolved ~unknown", True):
        dependEntity = FuncEntity.getOrCreate(depend.ent().name(), getFileName(depend.ent()))
        dependEntity.addDependBy(entity)
        # dependName = depend.ent().name()
        # graph[dependName].add(func.name())


def dfs(node: FuncEntity, seen=None):
    if seen is None:
        seen = set()
    answer = set()
    answer.add(node)
    for child in node.getDependsBy():
        if child not in seen:
            seen.add(child)
            answer.update(dfs(child, seen))
    return answer


def findImpactedFiles(node: FuncEntity):
    impactedEntities = dfs(node)
    impactedFiles = set()
    for ent in impactedEntities:
        impactedFiles.add(ent.fileName)
    return impactedFiles
