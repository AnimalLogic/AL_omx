Private APIs
=====================================

.. warning::

    The classes or functions documented here are all for internal use only! Do not use them in your code!
    This document is only here to help you understand them better.

AL.omx._xcommand
-------------------------------

.. automodule:: AL.omx._xcommand
    :members:
    :undoc-members:
    :show-inheritance:


AL.omx.plugin.AL_OMXCommand
-------------------------------
This module contains the method to load/unload the omx mpx plug-in. 
When the plug-in is loaded, several callbacks are registered and they will be unloaded when the plug-in is unloaded.
The callbacks are used to clean up omx modifier stacks on events like scene new, scene open and Maya quit.

.. automodule:: AL.omx.plugin.AL_OMXCommand
    :members:
    :undoc-members:
    :show-inheritance:
