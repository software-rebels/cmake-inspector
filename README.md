# DiPiDi

## Requirements

#### Known Compatibilities
*DiPiDi has been tested on the following Python and OS versions:*
- Python 3.8 & 3.9 (64-bit)

OS versions:
- macOS Big Sur *(including the macOS-11.4-arm64-arm-64bit version)*
- Ubuntu 16, 18, & 20
- Windows Subsystem for Linux  (wsl2)

#### Installing required Python packages
Use the following command with the requirements.txt file in the main repository folder.

- make sure Python 3 and `pip` are installed and currently in your PATH variables
- `cd` to the directory where `requirements.txt` is located
- run: `pip install -r requirements.txt` in your shell

#### GraphViz is required to export viewable graphs
 `GraphViz` can be installed from https://graphviz.org/


## Running DiPiDi

Once the required packages are installed most of the useful functionality can be found in the `extract.py` file:

The `getGraph(directory)` method can be used on a directory with a CMakeLists.txt file to parse a projects dependencies.
  e.g.,
~~~
>>> import extract
>>> getGraph("cmake-inspector/test/")
~~~
Once the directory has been parsed, some prebuild methods can be used, for example the method
`getTargets()` can be used to print Targets
  e.g.,
~~~
>>> import extract
>>> extract.getGraph("cmake-inspector/test/")
>>> extract.getTargets()
0. exec_2
1. lib_2
~~~
These targets can then be used as strings on which `getFlattenedFilesForTarget(target)` can be called.
  e.g.,
~~~
  >>> import extract
  >>> extract.getGraph("cmake-inspector/test/")
  >>> getFlattenedFilesForTarget("exec_2")
  defaultdict(<class 'set'>, {...})
~~~
`getFlattenedFilesForTarget(target)` will print directly to the console/terminal.

If you want to save to a csv, this can be done by calling  `exportFlattenedListToCSV(flattened: Dict, fileName: str)` with `getFlattenedFilesForTarget(target)` as a parameter.
e.g.,
~~~
>>> import extract
>>> extract.getGraph("cmake-inspector/test/")
>>> extract.getTargets()
0. exec_2
1. lib_2
>>> extract.exportFlattenedListToCSV(extract.getFlattenedFilesForTarget("exec_2"), "outputFile.csv")
~~~
## Test cases

Test cases for various scenarios can be found in `cmake-inspector/test/condition_test.py` & `cmake-inspector/test/variable_test.py`
The test cases can be modified to output graphs by adding the `self.vmodel.export()`
