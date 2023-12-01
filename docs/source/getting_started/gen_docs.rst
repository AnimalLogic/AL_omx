Generate |project| Documentation Locally 
============================================

The |project| `online documentation <https://animallogic.github.io/AL_omx/>`_ is always available.

The documentation source files are also included with each distribution, which means you can generate HTML documentation from them yourself locally.

**To generate the document:**

1. Install Sphinx, check out here for `more information <https://www.sphinx-doc.org/en/master/usage/installation.html>`_. 
Install using pip is suggested, but keep in mind that you can not use mayapy for the pip install, you will need the native pip to do that, or pip in a virtual env.

2. After installation, use this to verify it is installed correctly:

.. code:: shell
    
    sphinx-build --version

3. Install the required Sphinx theme and extension:

.. code:: shell
    
    pip install sphinx_rtd_theme
    pip install sphinx-copybutton

4. Add the root directory of |project| in your ``PYTHONPATH`` so that the document generator can import ``AL.omx`` for API documentation auto-generation.
You can simply append the root directory of |project| to the environment variable ``PYTHONPATH``:

For Linux and MacOSX:

.. code:: shell
    
    export PYTHONPATH="$PYTHONPATH:path/to/omxRootDir"

For Windows:

.. code:: batch

    set PYTHONPATH=%PYTHONPATH%;path/to/omxRootDir


5. Run make in the doc folder:

.. code:: shell
    
    cd path/to/omxRootDir/docs

    # for Linux and MacOSX:
    make html

    # for Windows:
    make.bat html

6. The generated documentation will be in ``path/to/omxRootDir/docs/build`` folder. Load the ``index.html`` in your web browser
to use the documentation. 