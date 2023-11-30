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

   In this cookbook, we always refer ``maya.api.OpenMaya`` as ``om2``, and ``AL.omx`` as ``omx``.

   .. seealso::
      :ref:`immediate_mode`
         The execute mode of omx dictates whether you need to call :func:`AL.omx.doIt()` manually.
   

Create DagNode
---------------------------
Use :func:`AL.omx.createDagNode` and expect an ``XNode`` to be returned.

.. code:: python

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

    timeNode = omx.createDGNode("time", nodeName="myTime")
    omx.doIt() # optional in script editor


XNode from an existing node
---------------------------
You can use; node name/dag path, om2.MObject, om2.MFnBase or another XNode to construct an ``XNode``.
Refer to :class:`AL.omx.XNode` for more details.

.. code:: python

    # from string:
    persp = omx.XNode("persp")
    
    # construct XNode from MObject:
    persp = omx.XNode(SOME_MOBJECT)

    # from MFn:
    fn = om2.MFnDependencyNode(SOME_MOBJECT)
    xnode = omx.XNode(fn)

    # from another XNode:
    xnode = omx.XNode(persp)


Query XNode States
---------------------------
An ``XNode`` is not an ``om2.MObject``, instead it is a thin wrapper around it. However, all the methods available
in ``om2.MObject`` are also available in ``XNode``, plus more. Refer to :class:`AL.omx.XNode` for more details.

.. code:: python

    # from string:
    perspShape = omx.XNode("perspShape")
    print("XNode is an om2.MObject:", isinstance(perspShape, om2.MObject))
    print("Camera api type: ", perspShape.apiType())
    print("Has camera functor: ", perspShape.hasFn(om2.MFn.kCamera))
    print("Camera is null: ", perspShape.isNull())
    print("Camera is valid: ", perspShape.isValid())
    print("Camera MObject: ", perspShape.object())


Access to Plug
---------------------------
You first need to get an ``XNode``, then you can get access to the ``XPlug`` from it.

.. code:: python

    persp = omx.XNode("persp")
    visXPlug = persp.visibility                                     # normal plug
    wmXPlug = persp.wm[0]                                           # array element by logical index
    bgColorRXPlug = perspShape.backgroundColorR                     # compound child
    bgColorGXPlug = perspShape.backgroundColor.child(1)             # compound child
    bgColorGXPlug = perspShape.backgroundColor['backgroundColorB']  # compound child



Get & Set Plug Value
---------------------------
An ``XPlug`` is actually an instance of ``om2.MPlug``, this means you have access to all of the ``om2.MPlug`` methods, 
and you can use ``XPlug`` whenever an ``om2.MPlug`` is needed. Refer to :class:`AL.omx.XPlug` for more details.

.. code:: python

    persp = omx.XNode("persp")
    worldMatrix = persp.wm[0].get()
    vis = persp.visibility.get()

    visPlug.set(not vis)


Connection
---------------------------
.. code:: python

    persp = omx.XNode("persp")
    side = omx.XNode("side")
    
    # connection
    persp.t.connectTo(side.t)
    side.r.connectFrom(persp.r)

    # disconnection
    side.r.disconnectFromSource()


Undo & Redo
---------------------------
Read the :doc:`../advanced/undoability` document to know how undo & redo actually works.

.. code:: python

    transform = omx.createDagNode("transform", nodeName="myLoc1")
    shape = omx.createDagNode("locator", parent=transform, nodeName="myLoc1Shape")
    omx.doIt() # optional in script editor

    omx.currentModifier().undoIt()
    omx.currentModifier().doIt()  # here calling omx.doIt() is the same.


Getting om2.MFn Functors
---------------------------
.. code:: python

    # retrieve basic functor, om2.MFnDependencyNode for DG node and om2.MFnDagNode for DAG node:
    print("basic functor for dag:", omx.XNode("persp").basicFn())
    print("basic functor for dg:", omx.XNode("time1").basicFn())

    # retrieve the most type-specific functor:
    print("basic functor for transform:", omx.XNode("persp").bestFn())
    print("basic functor for camera:", omx.XNode("perspShape").bestFn())


Stringfication
-------------------
:class:`AL.omx.XNode` and :class:`AL.omx.XPlug` both support stringfication, when used in ``print()`` or logger, it will be converted to a nice-formed string.

.. code:: python

    node = omx.XNode("persp")
    visPlug = node.visibility
    print("node:", node)        # the minimum dag path or dg name will be used.
    print("plug", visPlug)      # minimumDagPath.plugLongName will be used.
