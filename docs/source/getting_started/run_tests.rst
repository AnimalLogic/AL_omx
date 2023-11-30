Running All |project| Tests 
============================================

Each |project| distribution comes with full test suites. 

**Run Tests in Maya Standalone**

1. Make sure you install the |project| for that Maya version, check out :doc:`installation`.

2. Run tests using mayapy:

.. code:: shell
    
    path/to/mayapy -m AL.omx.tests.runall


**Run Tests in Maya Interactive Mode**

1. Make sure you install the |project| for that Maya version, check out :doc:`installation`.

2. Run Python command in Maya's script editor:

.. code:: python
    
    from AL.omx.tests import runall
    runall.runAllOMXTests()
