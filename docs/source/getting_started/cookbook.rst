Cookbook
========================

.. note::
    The main purpose of the cookbook is to convey the idea of how to use omx, you may need to change 
    some node names or import relevant modules to make it work in your environment.

    The import statements are omitted from all the code snippets below.
    These are two typical module import statements you need:

    .. code:: python

        from AL import omx
        from maya.api import OpenMaya as om2

    In this cookbook, we always refer to ``maya.api.OpenMaya`` as ``om2``, and ``AL.omx`` as ``omx``. 

.. seealso::
    :ref:`immediate_mode`
        The execute mode of omx dictates whether you need to call :func:`AL.omx.doIt()` manually.
   

Create DagNode
---------------------------
Use :func:`AL.omx.createDagNode` and expect an ``XNode`` to be returned.

.. code:: python

    from AL import omx
    # create transform node and its shape:
    locatorTransform1 = omx.createDagNode("transform", nodeName="myLoc1")
    locatorShape1 = omx.createDagNode("locator", parent=locatorTransform1, nodeName="myLoc1Shape")

    # create shape and its parent transform in one go, by default parent transform will have a default name,
    # and here the function returns the shape only:
    locatorShape2 = omx.createDagNode("locator", nodeName="myLoc2Shape")

    # create shape and its parent transform in on go, but return [transform, shape]:
    locatorTransform3, locatorShape3 = omx.createDagNode("locator", nodeName="myLoc3Shape", returnAllCreated=True)

    omx.doIt() # optional in script editor


Create DGNode
---------------------------
Use :func:`AL.omx.createDGNode` and expect an ``XNode`` to be returned.

.. code:: python

    from AL import omx
    timeNode = omx.createDGNode("time", nodeName="myTime")
    omx.doIt() # optional in script editor


XNode from an existing node
---------------------------
You can use; node name/dag path, om2.MObject, om2.MFnBase or another XNode to construct an ``XNode``.
Refer to :class:`AL.omx.XNode` for more details.

.. code:: python

    from AL import omx
    import maya.api.OpenMaya as om2

    # from string:
    persp = omx.XNode("persp")
    mobj = persp.object()  # get MObject from XNode
    
    # construct XNode from MObject:
    persp = omx.XNode(mobj)

    # from MFn:
    fn = om2.MFnDependencyNode(mobj)
    xnode = omx.XNode(fn)

    # from another XNode:
    xnode = omx.XNode(persp)


Query XNode States
---------------------------
An ``XNode`` is not an ``om2.MObject``, instead it is a thin wrapper around it. However, all the methods available
in ``om2.MObject`` are also available in ``XNode``, plus more. Refer to :class:`AL.omx.XNode` for more details.

.. code:: python

    from AL import omx
    import maya.api.OpenMaya as om2
    
    # from string:
    persp = omx.XNode("perspShape")
    print("XNode is an om2.MObject:", isinstance(persp, om2.MObject))
    print("Camera api type: ", persp.apiType())
    print("Has camera functor: ", persp.hasFn(om2.MFn.kCamera))
    print("Camera is null: ", persp.isNull())
    print("Camera is valid: ", persp.isValid())
    print("Camera MObject: ", persp.object())


Access to Plug
---------------------------
One way is to get an ``XNode``, then you get access to the ``XPlug`` from it. Starting from `1.0.10`, you can also construct an ``XPlug`` directly from the `"node.attribute"` string.

.. code:: python

    from AL import omx
    persp = omx.XNode("persp")
    visXPlug = persp.visibility                                     # normal plug
    wmXPlug = persp.wm[0]                                           # array element by logical index
    bgColorRXPlug = persp.backgroundColorR                     # compound child
    bgColorGXPlug = persp.backgroundColor.child(1)             # compound child
    bgColorGXPlug = persp.backgroundColor['backgroundColorB']  # compound child

    focalLengthXPlug = omx.XPlug("perspShape.focalLength")          # directly from string


Get & Set Plug Value
---------------------------
An ``XPlug`` is actually an instance of ``om2.MPlug``, this means you have access to all of the ``om2.MPlug`` methods, 
and you can use ``XPlug`` whenever an ``om2.MPlug`` is needed. Refer to :class:`AL.omx.XPlug` for more details.

.. code:: python

    from AL import omx
    
    persp = omx.XNode("persp")
    print("World matrix:", persp.wm[0].get())
    persp.visibility.set(not persp.visibility.get())



Connection
---------------------------
The connection methods on ``XPlug`` will unlock the destination plug if it is locked, and disconnect it if it's already connected when the argument `force=True`.

.. code:: python

    from AL import omx
    persp = omx.XNode("persp")
    side = omx.XNode("side")

    # connection
    persp.t.connectTo(side.t, force=True)
    side.r.connectFrom(persp.r)

    # disconnection
    side.r.disconnectFromSource()


Undo & Redo
---------------------------
Read the :doc:`../advanced/undoability` document to know how undo & redo actually works.

.. code:: python

    from AL import omx
    transform = omx.createDagNode("transform", nodeName="myLoc1")
    shape = omx.createDagNode("locator", parent=transform, nodeName="myLoc1Shape")
    omx.doIt() # optional in script editor

    # In immediate mode, undo and redo are automatically handled by Maya. But when you manage the 
    # undo and redo yourself by using omx.currentModifier(), you need to call these:
    omx.currentModifier().undoIt()
    omx.currentModifier().doIt()  # here calling omx.doIt() is the same.


Getting om2.MFn Functors
---------------------------
``XNode`` comes with convenience methods to get the basic or best ``om2.MFn`` functors. But since ``1.1``, using ``XFn`` is recommended.

.. code:: python

    from AL import omx
    # retrieve basic functor, om2.MFnDependencyNode for DG node and om2.MFnDagNode for DAG node:
    print("basic functor for dag:", omx.XNode("persp").basicFn())
    print("basic functor for dg:", omx.XNode("time1").basicFn())

    # retrieve the most type-specific functor:
    print("basic functor for transform:", omx.XNode("persp").bestFn())
    print("basic functor for camera:", omx.XNode("perspShape").bestFn())

    # retrieve the universal XFn, which gives you more convenience methods along with all the functionality of basic and best functors above.
    print("XFn for transform:", omx.XNode("persp").xFn())
    print("XFn for camera:", omx.XFn("perspShape"))


Stringification
-------------------
:class:`AL.omx.XNode` and :class:`AL.omx.XPlug` both support stringification, when used in ``print()`` or logger, it will be converted to a nice-formed string.

.. code:: python

    from AL import omx
    node = omx.XNode("persp")
    visPlug = node.visibility
    print("node:", node)        # the minimum dag path or dg name will be used.
    print("plug", visPlug)      # minimumDagPath.plugLongName will be used.


Iteration In Dag Hierarchy
---------------------------
With :class:`AL.omx.XFn`, you can iterate all the parents, children, ancestors, descendants and shapes of the node in the DAG hierarchy.

.. code:: python

    from AL import omx
    cameraFn = omx.XFn("perspShape")
    # Get parent at index 0 by default.
    parent = cameraFn.getParent()
    print("Parent for perspShape:", parent)

    # Get child by index:
    child = parent.xFn().getChild(0)
    print(f"Child of {parent}: {child}")

    # Iterate all children:
    for child in parent.xFn().iterChildren():
        print(f"Child of {parent}: {child}")

    # Iterate all ancestors:
    for ancestor in cameraFn.iterAncestors():
        print(f"Ancestor of {cameraFn.xnode()}: {ancestor}")

    # Iterate all descendants:
    for descendant in parent.xFn().iterDescendants():
        print(f"Descendant of {parent}: {descendant}")

    # Get shape:
    shape = parent.xFn().getShape()
    print(f"Shape of {parent}: {shape}")


Iteration Plugs on Node
---------------------------
Both :class:`AL.omx.XNode` and :class:`AL.omx.XFn` supports iteration over plugs that match certain criteria.

.. code:: python

    from AL import omx
    camera = omx.XNode("perspShape")

    # Iterate all plugs:
    for i, plug in enumerate(camera.iterXPlugs()):
        print(f"Plugs[{i}]: {plug}")
        
    # Iter all visible angle xplugs
    for p in camera.iterXPlugs(attrType=omx.XAttrType.ANGLE, states=omx.XPlugState.VISIBLE):
        print("Visible angle plug:", p)   


    # Iter all angle xplugs that are either connected as destination or locked
    for p in camera.iterXPlugs(attrType=omx.XAttrType.ANGLE|omx.XAttrType.DOUBLE, states=omx.XPlugState.DESTINATION|omx.XPlugState.LOCKED):
        print("Connected or locked angle or double plug:", p)   
        

    # Iter all dynamic or connected destination xplugs but they need to be visible:
    for p in camera.iterXPlugs(states=(omx.XPlugState.DYNAMIC|omx.XPlugState.DESTINATION, omx.XPlugState.VISIBLE)):
        print("Dynamic visible plug:", p)
        

    # Further predicate:
    predicate = lambda xplug : str(xplug).endswith("Aperture")
    for p in camera.iterXPlugs(states=omx.XPlugState.VISIBLE, predicate=predicate):
        print("Visible plug that related to aperture:", p)

