Install |project| In Maya
================================

Install With Pip and mayapy
---------------------------------
|project| is available in `PyPi <https://pypi.org/>`__, that means you can easily install in Maya using ``pip install``.
`mayapy` is an executable to bootstrap the process to start Maya's bundled Python interpreter, it is available on each distribution of Maya.

To install |project| with pip, you first need to ensure pip is already installed for your ``mayapy``, try running the script below in the console:

.. code:: shell
    
    /path/to/mayapy -m pip --version

If this prints out the version correctly, means pip has already been installed and is available. 
Otherwise, refer to `this <https://pip.pypa.io/en/stable/installation/>`_ for how to install pip within ``mayapy``, keep in mind that 
instead of calling ``python``, you need to call ``/actual/path/to/mayapy`` instead. 

Now to install |project| with pip in Windows, you just do:

.. code:: shell

    mayapy -m pip install AL_omx

In Linux and macOS:

.. code:: shell

    sudo ./mayapy -m pip install AL_omx

To uninstall, do this in Windows:

.. code:: console

    mayapy -m pip uninstall AL_omx

In Linux and macOS:

.. code:: shell

    sudo ./mayapy -m pip uninstall AL_omx


.. note::

    You will need to have administrator privilege to install/uninstall pip and |project| in this way.


Install Manually by PYTHONPATH
------------------------------------------------
Alternatively, you can download |project| from `PyPi <https://pypi.org>`__ or from `Github <https://github.com/animallogic/AL_omx>`_, extract files to wherever
you want, and add the root directory that contains ``AL`` to your ``PYTHONPATH``. 
This can be done by adding the directory to ``PYTHONPATH`` global environment variable setting in your OS, or by python script.

At the moment, |project| does not contain external pip dependency, so directly using it by adding it to ``PYTHONPATH`` is feasible.
The upside is you don't need administrator privileges to install this way.


Verify the Installation 
------------------------------------------------
After the installation, you can lunch the relevant version of Maya and start using |project|. 
Try this in Maya's script editor to see if things are installed correctly:

.. code:: python

    from AL import omx

For the first run, Maya will pop up dialog, confirming that if you want to load the AL_OMXCommand.py plugin. 
You need to allow it for the undo/redo works for edits made by |project|. Then if you exit Maya normally, the next time you 
do `from AL import omx` it won't ask you again.


Supported Environment
------------------------------------
+------------+------------+
|  Python    |    Maya    |
+============+============+
|    3.7+    |    2022+   |
+------------+------------+

|project| might still work in earlier Maya version, but Maya 2022 and later versions are the ones that we heavily tested upon.