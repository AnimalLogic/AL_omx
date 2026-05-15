Change Logs
================
1.1.0
--------------
Fixes
    - Fix the argument error on XFn.iterXPlugs().

Improvements:
    - Update documentation and push all the changes to opensource.


1.0.13
--------------
Features
    - Add XNode.iterXPlugs() and XFn.iterXPlugs() to iter all the matched xplugs on a node, with the ability to filter by attribute type, plug states and custom predicate.


1.0.12
--------------
Features
    - Add has* query methods for XFn to check if the node got parent/child etc before accessing them.


1.0.11
--------------
Improvements
    - Update to black-25.


1.0.10
--------------
Features
    - Add XFn for universal FunctionSet access.


1.0.9
--------------
Improvements
    - Move to new vfx_cxx-2023 platform.


1.0.8
--------------
Fixes
    - Fixes compound angle attributes such as ".rotate" resulting in radians rather than degrees when using a tuple and setting asDegrees to "True".


1.0.7
--------------
Fixes
    - Fix the rare crash caused by disconnecting an array element plug from its old source and reconnecting it to a new source, the element plug somehow become invalid thus crashes during the reconnection.


1.0.6
--------------
Fixes
    - Fix the commandModifierContext for ALCommand so that it does not break during the context due to potential exception, and make sure the exception is reraised.


1.0.5
--------------
Fixes
    - Use os.sep for omx plugin env separator.
    
Improvements
    - Use MDagPath to construct Maya function set object for XNode.basicFn() and XNode.bestFn() as much as possible.


1.0.4
--------------
Fixes
    - Fix issues caused by omx import in non-Maya environment.
    
Improvements
    - Update Contribution and Feedback section for documentation.
    - More contents added to README.md.


1.0.3
--------------
Fixes
    - Fix the MagicMock import issue which only happens in interactive Maya during startup.


1.0.2
--------------
Features
    - Add git action to sync between private repo and public repo.
    - Fix api documentation build error by introducing stubs for importing AL.omx in non-Maya environment.
    - Add reformat script to ensure copyright header comment and black formating.
    - Add runall module to run pyunit tests.
    - Add documentation for doc generation and tests running.

1.0.1
--------------
Features
    - Build up opensource facility.
    - Write user documentation. 
