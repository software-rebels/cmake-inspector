## Running DiPiDi

Once the required packages are installed most of the useful functionality can be found in the `api.py` file:

The `getGraph(directory)` method can be used on a directory with a CMakeLists.txt file to parse a projects dependencies.
  e.g.,
```python
from api import getGraph
vmodel, lookupTable = getGraph("cmake-inspector/test/")
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

## Running Test Cases

Test cases for various scenarios can be found in `test/condition_test.py` & `test/variable_test.py`. You can run
the test cases using the following command:
```bash
python -m unittest test/variable_test.py
```