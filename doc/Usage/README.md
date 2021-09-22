## Running DiPiDi

Once the required packages are installed most of the useful functionality can be found in the `api.py` file:

The `getGraph(directory)` method can be used on a directory with a CMakeLists.txt file to parse a projects dependencies.
  e.g.,
```python
from api import getGraph
vmodel, lookupTable = getGraph("cmake-inspector/test/")
```
Once the directory has been parsed, an instance of the build dependency graph will be returned. You can export the
graph in both `dot` file format or `Neo4j` database.
```python
# Export to dot file format and generate a PDF file
vmodel.export(writeToNeo=False, writeDotFile=True)
# Write to Neo4j database and generate dot file
vmodel.export(writeToNeo=True, writeDotFile=True)
```

Additionally, some prebuild methods can be used after the graph generation phase, for example the method
`getTargets()` can be used to print Targets
  e.g.,
```python
from api import getGraph, getTargets
vmodel, lookupTable = getGraph("cmake-inspector/test/")
print(getTargets())
# 0. exec_2
# 1. lib_2
```
These targets can then be used as strings on which `getFlattenedFilesForTarget(target)` can be called.
  e.g.,
```python
import extract
extract.getGraph("cmake-inspector/test/")
getFlattenedFilesForTarget("exec_2")
defaultdict(<class 'set'>, {...})
```
`getFlattenedFilesForTarget(target)` will print directly to the console/terminal.

If you want to save to a csv, this can be done by calling  `exportFlattenedListToCSV(flattened: Dict, fileName: str)` with `getFlattenedFilesForTarget(target)` as a parameter.
e.g.,
```python
import extract
extract.getGraph("cmake-inspector/test/")
extract.getTargets()
# 0. exec_2
# 1. lib_2
extract.exportFlattenedListToCSV(extract.getFlattenedFilesForTarget("exec_2"), "outputFile.csv")
```

### Detecting Cycles
The `getFlattenedFilesForTarget` API will raise an error if it detects acyclic dependency for the target. As an example,
you can run the DiPiDi on the project provided in the `sample_projects/cycle` folder to see this functionality.
```python
from api import getGraph, getFlattenedFilesForTarget
vmodel, lookuptable = getGraph('./sample_projects/cycle')
getFlattenedFilesForTarget('openssl')
# raise CycleDetectedException('We have a cycle here!!')
# Conditions: {BUILD_CURL}
# 0: target_link_libraries(openssl_2 curl_2)
# 1: target_link_libraries(openssl_2 curl_2)
# 2: if(${BUILD_CURL})
# 3: if(${BUILD_CURL})
# 4: target_link_libraries(curl_2 openssl_2)
```

### Test cases

Test cases for various scenarios can be found in `cmake-inspector/test/condition_test.py` & `cmake-inspector/test/variable_test.py`
The test cases can be modified to output graphs by adding the `self.vmodel.export()`