Update on Project Governance and Contributions
=================================================
As of May 11 2026, the AL_omx project is updating its contribution process.

What is Changing?
---------------------
Retirement of Formal CLAs: We no longer require contributors to sign and email a PDF of the Individual or Corporate Contributor License Agreement.
By submitting a contribution to this project, you represent that you are entitled to grant the relevant licenses for your contribution. All contributions are now governed strictly by the Apache License, Version 2.0 included in this repository.
If you or your corporation have already signed a CLA for the AL_omx project, those agreements remain on file as a historical record of the intellectual property permissions granted for previous versions of the software.


Contribution Workflow
=====================================
Before you begin working on a bug fix or new feature, please post an issue on GitHub to let everyone know about the feature you want to implement, or the bug that you found and intend to fix.
 
When you do begin your work, create a fork into your own private repository and work from there.

Your development should be based on `develop` (and not on `main`).

Here is an example (linux):

.. code:: shell

    git clone https://github.com/AnimalLogic/AL_omx.git
    cd AL_omx

    # Add the original repository as a remote
    git remote add al_origin https://github.com/AnimalLogic/AL_omx.git

    git fetch al_origin

    git checkout -b my_feature al_origin/develop


Before submitting the pull request, make sure `my_feature` branch contains the relevant
commits only (rebasing and/or squashing your work if needed).

Also make sure to go through the checklist described in the pull request's template.

Note that once your PR has been approved, it might take some time before we merge it.


Coding Conventions
=====================================
Please follow the existing coding conventions and style in each file and in each library when adding new files.
For the python source code in AL/omx folder, here are code of conduct:

- Use camel case in your code.
- Use expressive variable names and function names.
- Document your new function/method/class/arguments.
- Before code submission, please run ``./reformat.sh`` or ``reformat.bat`` to make sure the header is correct, and the code is formatted with black-25. So you will need to be in an environment that version 25 is used when running command `black`.
