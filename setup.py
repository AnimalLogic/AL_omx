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
# limitations under the License.


import re
from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


_VERSION_RETRIEVE_PATTERN = None


def version():
    global _VERSION_RETRIEVE_PATTERN
    if _VERSION_RETRIEVE_PATTERN is None:
        _VERSION_RETRIEVE_PATTERN = re.compile("[0-9\.]+")

    with open("docs/source/changes.rst") as f:
        for line in f:
            content = line.strip()
            if _VERSION_RETRIEVE_PATTERN.fullmatch(content):
                return content


setup(
    name="AL_OMX",
    version=version(),
    description="A fast and user-friendly library built on top of Autodesk Maya's OpenMaya library.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/animallogic/AL_omx",
    author="Animal Logic",
    author_email="",
    license="Apache License, Version 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache License, Version 2.0",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development",
        "Topic :: Software Development :: DCC",
        "Intended Audience :: Developers",
    ],
    packages=[
        "AL",
        "AL.omx",
        "AL.omx.plugin",
        "AL.omx.tests",
        "AL.omx.tests.utils",
        "AL.omx.utils",
    ],
    include_package_data=True,
    install_requires=[],
    extras_require={},
)
