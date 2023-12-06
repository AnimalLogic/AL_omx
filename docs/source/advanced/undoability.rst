Undoability
========================

.. _undoability:

Automatic Undo & Manual Undo
--------------------------------------------
There are two types of undoability in omx: 

**1. Automatic Undo:**
When using omx for scripting, e.g. creating nodes using ``omx.create*Node``, calling methods from :class:`AL.omx.XNode`
, :class:`AL.omx.XPlug` or call :class:`AL.omx.XModifier` method from :func:`AL.omx.currentModifier()` instead of :func:`AL.omx.newModifier()`
for editing, one execution will be one undo item in Maya. 

After execution, you simply use `ctrl+Z` and `shift+Z` to undo and redo.

**2. Manual Undo:**
When using omx within your tools or framework, where you want to manage undo and redo yourself, you will need
to ensure you are using non-immediate :class:`AL.omx.XModifier`, and call :func:`AL.omx.XModifier.doIt()`, :func:`AL.omx.XModifier.undoIt()`
manually in the proper places.


.. _mix_cmds_omx:

Mixing maya.cmds & AL.omx calls
--------------------------------------------
Mixing ``om2`` (maya.api.OpenMaya) and ``cmds`` in your code is a wrong choice generally. 
The rule of thumb is to try to use ``om2`` as much as you can as it brings you the best performance in Python, 
and use ``om1`` (maya.OpenMaya) if the feature is not available in ``om2``, and use ``cmds``
only for queries. When you have to use ``cmds`` with ``om2`` for editing, wrap it with ``om2.MDGModifier.pythonCommandToExecute()``.

The reason for these head-ups is the undo problems caused by mixed-use. When you undo in Maya, edit by ``cmds``
will be undone but edits by ``om2`` will not, thus the broken states in the scene.

When it comes to mixing ``maya.cmds`` and ``omx`` calls, that depends.
If you ensure ``omx`` calls all using immediate mode XModifier ( check :ref:`immediate_mode` ), it is fine to mix it with maya.cmds:

.. code:: python

    from AL import omx
    from maya.api import OpenMaya as om2

    # reminder: create a new scene to ensure we are using the immediate mode of xmodifier.

    # cmds calls:
    transformName1, shapeName1 = cmds.polyCube()

    # omx calls:
    transform1 = omx.XNode(transformName1)
    transform1.t.set((2,3,4))

    # cmds calls:
    transformName2, = cmds.spaceLocator()
    # omx calls:
    transform2 = omx.XNode(transformName2)
    transform2.t.connectFrom(transform1.t)

    # cmds calls:
    cmds.polySphere()

    # the undo/redo will work.

If you use omx in some production code where you manage undo & redo yourself, mixing ``cmds`` with ``omx`` calls is the same
as mixing ``cmds`` with om2. You will have undo issues.


Mixing om2 Modifier and omx.XModifier
--------------------------------------------
This is a bad idea. 
If you use omx.XModifier, it is better and safer to only use omx.XModifier, to ensure the undo is done in a sequential way, 
use :func:`AL.omx.newModifier` to create separate XModifier if you need it.
Alternatively, use omx.XModifiers and om2.MDagModifier, but stick to native API modifier's for the edits, do not use omx API for editing.

Undo with XPlug States Change
--------------------------------------------
When you need to set XPlug state, ``isLocked``, ``isKeyable``, ``isChannelBox``, etc, you have two options, take ``isLocked`` for example:
``omx.XPlug.setLocked(bool)`` and ``omx.XPlug.isLocked = bool``. 
The difference between the two is ``setLocked()`` is undoable with :class:`omx.XModifier`, but you pay more performance cost while the 
``isLocked`` approach is not undoable and will be likely to ruin the surrounding undo states, but it is faster than ``setLocked()``.
As a rule of thumb, use ``omx.XPlug.isLocked = bool`` when you don't need to undo the state change, use ``setLocked()`` if the undoability 
matters. The same rule applies to other state edits like ``isKeyable`` and ``isChannelBox``.