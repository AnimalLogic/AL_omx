# AL_omx

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![PyPi](https://img.shields.io/pypi/v/AL_omx)
![PythonVersion](https://img.shields.io/pypi/pyversions/AL_omx)

`AL_omx` is an open-source library that provides a thin wrapper around Maya OM2 which makes it easy to manipulate nodes, attributes and connections while retaining the API's performance:  
- User-friendly entry point into Maya’s native [om2 (maya.api.OpenMaya)](https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_html) API .
- Simple explicit code. [Cookbook](https://animallogic.github.io/AL_omx/getting_started/cookbook.html).
- Closer to Maya’s om2 API’s performance over other libraries. [Performance Comparison](https://animallogic.github.io/AL_omx/introduction/perf_compare.html).
- Built-in [Undoability](https://animallogic.github.io/AL_omx/advanced/undoability.html).


## QuickStart

Install `AL_omx` using `mayapy -m pip install AL_omx`, or by adding the root directory to `sys.path`. The url for `PyPi` package is [here](https://pypi.org/project/AL_omx/).

For more information on the installation, check out [here](https://animallogic.github.io/AL_omx/getting_started/installation.html).

The requirements of `AL_omx`:

| Python | Maya  |
|--------|-------|
| 3.7+   | 2022+ 



## Syntax
`AL_omx` uses object-oriented syntax:

```Python
    from AL import omx

    transform, locator = omx.createDagNode(
        "locator", nodeName="myLocShape", returnAllCreated=True
    )
    omx.createDGNode("time", nodeName="myTime")
    persp = omx.XNode("persp")
    perspShape = omx.XNode("perspShape")

    persp.visibility.setLocked(True)
    transform.t.set([2.0, 2.0, 2.0])
    print(f"locator worldMatrix: {transform.wm[0].get()}")
    locator.overrideEnabled.set(True)
    locator.overrideColor.set(14)

    persp.r.connectTo(transform.r)
    transform.sx.connectFrom(omx.XNode("time1").outTime)
    transform.r.disconnectFromSource()

    # ctrl+Z/shift+Z to undo & redo
```


## Documentation

The full document source is available in the `docs` folder, you can generate the document yourself using `sphinx`, check out [here](https://animallogic.github.io/AL_omx/getting_started/gen_docs.html) for how to do it.

The full online documentation can be found at https://animallogic.github.io/AL_omx/

Here are some convenient entries:
- [Cookbook Style Snippets](https://animallogic.github.io/AL_omx/getting_started/cookbook.html)
- [Public API Reference](https://animallogic.github.io/AL_omx/api/public.html)
- [Running Tests](https://animallogic.github.io/AL_omx/getting_started/run_tests.html)
- [Changes Log](https://animallogic.github.io/AL_omx/changes.html)

## Contribution & Feedback
For how to contribute to `AL_omx`, check out [here](https://animallogic.github.io/AL_omx/feedback/contributing.html).
If you have any issues or feature suggestions, please feel free to submit a ticket in [GitHub Issues](https://github.com/AnimalLogic/AL_omx/issues).