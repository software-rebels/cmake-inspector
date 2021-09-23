## Visualization

### Exporting the BDG
Once the directory has been parsed, an instance of the build dependency graph will be returned. You can export the
graph in both `dot` file format or `Neo4j` database.
```python
# Export to dot file format and generate a PDF file
vmodel.export(writeToNeo=False, writeDotFile=True)
# Write to Neo4j database and generate dot file
vmodel.export(writeToNeo=True, writeDotFile=True)
```


### Exporting Source Files and Conditions
For each deliverable, you can find which source file will be included in the compilation path under different build
time configurations. You can pass a target name as strings to `getFlattenedFilesForTarget(target)` function which
returns a dictionary of <[list of files], configuration>.
  e.g.,
```python
import extract
extract.getGraph("cmake-inspector/test/")
getFlattenedFilesForTarget("exec_2")
defaultdict(<class 'set'>, {...})
```
`getFlattenedFilesForTarget(target)` will print directly to the console/terminal.

If you want to save to a csv, this can be done by calling  `exportFlattenedListToCSV(flattened: Dict, fileName: str)` 
with `getFlattenedFilesForTarget(target)` as a parameter.
e.g.,
```python
import extract
extract.getGraph("cmake-inspector/test/")
extract.getTargets()
# 0. exec_2
# 1. lib_2
extract.exportFlattenedListToCSV(extract.getFlattenedFilesForTarget("exec_2"), "outputFile.csv")
```

### Useful Neo4j Queries
#### Files that will be compiled in all paths
```
match p=(t:Target {name: "Tutorial"})-[*0..]->(:Literal)
with nodes(p) as ns
where NONE(node in ns where node:Select)
return ns
```

#### Files that will be compiled if USE_MYMATH is true
```
match p=(t:Target {name: "Tutorial"})-[*0..]->(:Select {condition: "(USE_MYMATH)"})-[:TRUE]->()-[*0..]->(:Literal)
return p
```

#### Files that will be compiled if USE_MYMATH is false
```
match p=(t:Target {name: "Tutorial"})-[*0..]->(:Select {condition: "(USE_MYMATH)"})-[:FALSE]->()-[*0..]->(:Literal)
return p
```

#### Conditions and their values which contain MakeTable.cxx file, starting from a target named Tutorial
```
match (:Target {name: "Tutorial"})-[*0..]->(s:Select)-[r]->()-[*0..]->(l:Literal {name: "MakeTable.cxx"})
return s.condition,type(r)
```