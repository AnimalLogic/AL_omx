# Copyright © 2026 Netflix, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os

_DEPRECATED_COPYRIGHT_HEADER = """\
# Copyright © 2023 Animal Logic. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License."""


def _copyrightHeaderComments():
    copyRightLines = []
    with open(__file__, "r") as f:
        for l in f:
            if l.startswith("#"):
                copyRightLines.append(str(l))
            else:
                break

    return copyRightLines


def _iterAllPythonSourceFiles(rootdir):
    # for py-2 compatibility we cannot use glob.iglob or os.scandir.
    for root, directories, files in os.walk(rootdir):
        for f in files:
            if f.endswith(".py") and f != "package.py":
                yield os.path.join(root, f)


def prepandCopyrightComment():
    copyRightLines = _copyrightHeaderComments()
    copyRightStr = "".join(copyRightLines)
    rootdir = os.path.dirname(__file__)

    docFolder = os.path.join(rootdir, "docs")
    buildFolder = os.path.join("", "build", "")

    for filename in _iterAllPythonSourceFiles(rootdir):
        if filename == __file__:
            continue

        if filename.startswith(docFolder):
            continue

        if buildFolder in filename:
            continue

        with open(filename, "r") as f:
            data = f.read()

        # We need to update the deprecated copyright instead of prepending.
        if data.startswith(_DEPRECATED_COPYRIGHT_HEADER):
            data = data.replace(_DEPRECATED_COPYRIGHT_HEADER, copyRightStr, 1)
            with open(filename, "w") as f:
                f.write(data)
                print("Updated copyright comment: {}".format(filename))

            continue

        if data.startswith(copyRightLines[0]):
            continue

        # Prepend the new copyright header if the file doesn't already have it.
        with open(filename, "w") as f:
            f.write(copyRightStr + os.linesep + os.linesep + data)
            print("Prepend copyright comment: {}".format(filename))


if __name__ == "__main__":
    prepandCopyrightComment()
