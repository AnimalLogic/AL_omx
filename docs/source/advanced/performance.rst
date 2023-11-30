Performance Tips
========================

Use Non-Immediate Mode
-------------------------
As shown in :doc:`../introduction/perf_compare`, `immediate mode` does bring quite a performance penalty. 
Only use `immediate mode` for interactive scripting or quick code testing, use `non-immediate` mode for production code.

Check here for more information on :ref:`immediate_mode`.


Journal
-------------------------
|project| supports a journal for all creation and edit operations. 
Enabling the journal comes with quite a performance penalty, not as much as `immediate mode` but still a significant enough impact to warrant mentioning. 
In the 10000+ nodes performance test, it was roughly 6~8 seconds difference.

There is API :func:`AL.omx.setJournalToggle` to turn on the journal globally, but it is strongly not suggested.
You can use :func:`AL.omx.isJournalOn` to check if the journal is actually turned on.
If you want to turn on the journal temporarily, the suggested way is to wrap your code within :class:`JournalContext`:

.. code:: python

    with omx.JournalContext():
        ...

To query journal:

.. code:: python

    # note that if the xmodifier is in immediate mode, the journal will be cleaned after each execution.
    # so you won't see any records.
    print(omx.currentModifier().journal())


Plug Setting
---------------------------
:class:`AL.omx.XPlug` comes with many set methods for plug value setting. 
The :func:`AL.omx.XPlug.set` is the simplest way to do it, but not the fastest in performance. Internally it does many checks 
and sets the value using different ways based on attribute type. 
If you know what type of plug you are setting, then use the type-specific set method instead.

There is one thing also worth noticing is setting plug states, like `isLocked`, `isKeyable`, `isChannelbox`.
Take `isLocked` for example, performance-wise, using ``omx.XPlug.isLocked = bool`` is preferable than 
``omx.XPlug.setLocked(bool)``, because the ``setLocked()`` come with extra costs. 
For undoability, ``omx.XPlug.setLocked(True)`` is fully undoable; However, ``omx.XPlug.isLocked = bool`` is not, so you are
only able to use it when you don't care about undoability, or the node or plug was created within that same modifier, where
the undoability of plug state change does not matter.

The same rule applies to all the other plug states.