# -*- coding: utf-8 -*-
config_version = 0

name = "AL_omx"

uuid = "5e1153b0-6735-11ee-b706-78ac445c0b95"

version = "1.0.0"

description = """
    A thin wrapper around Maya OM2 which makes OM2 more user-friendly but still retains the API's performance.
"""

authors = [
    "Aloys Baillet",
    "Miguel Gao",
    "Valerie Bernard",
    "James Dunlop",
    "Daniel Springall",
]

private_build_requires = [
    "cmake-3",
    "AL_CMakeLibALPythonLibs-3.7+<4",
]

requires = ["demandimport-0", "enum34", "maya-2020+", "python-3.7+<4"]


def commands():
    prependenv(
        "PYTHONPATH", "{root}/AL_maya2-${REZ_AL_MAYA2_VERSION}-none-any.whl",
    )
    prependenv("MAYA_PLUG_IN_PATH", "{root}/maya")


tests = {
    "maya": {
        "command": "run_maya_nose2 AL.omx.tests",
        "requires": [
            "nose2",
            "python-3",
            "AL_CMakeLibPython-6.9+<7",
            "maya-2022",
            "mayaLoadVersionedTool",
            "AL_maya_rig_nodes_reparent",
            "AL_maya_math_nodes",
        ],
    },
    "black": {
        "command": "black . --check",
        "run_in_root": True,
        "requires": ["black-19"],
    },
}
