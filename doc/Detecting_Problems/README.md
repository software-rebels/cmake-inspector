## Detecting Cycles
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

## Empty Deliverables
You can use the `getFlattenedFilesForTarget` function and see if there exists a condition under which the list of
compiled files is empty.

## Assessing The Risk of a Change
The `getFlattenedFilesForTarget` function can be run on all targets in parallel. The output will be a list of files
and a list of targets under different configurations. A file that impacts many deliverables under different
configurations is riskier than others. 