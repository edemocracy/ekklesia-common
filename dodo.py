"""
Task configuration file for doit, a task management & automation tool.

https://pydoit.org

Just run the `doit` command to compile translation files. This is the same as:

doit babel_compile css_compile

doit shows a dot before tasks that were executed and two dashes (--) if nothing changed.
"""
from pathlib import Path
import os

BASEDIR = Path('src/ekklesia_common')
TDIR = BASEDIR / 'translations'
POT_PATH = TDIR / 'messages.pot'
SRCS = ['concepts', 'templating.py', 'enums.py']
SRC_PATHS = " ".join([str(BASEDIR / src) for src in SRCS] + ["tests"])
PO_PATHS = [
    TDIR / "de" / "LC_MESSAGES" / "messages.po",
    TDIR / "en" / "LC_MESSAGES" / "messages.po"
]
MO_PATHS = [
    TDIR / "de" / "LC_MESSAGES" / "messages.mo",
    TDIR / "en" / "LC_MESSAGES" / "messages.mo",
]

DOIT_CONFIG = {
    "default_tasks": ["babel_compile"]
}

### default tasks

def task_babel_compile():
    return {
        "actions": [
            f"pybabel compile -d {TDIR}"
        ],
        "file_dep": PO_PATHS,
        "targets": MO_PATHS,
        "clean": True
    }

### aux tasks

def task_babel_show_paths():
    return {
        "actions": [
            f"echo translations dir: {TDIR}",
            f"echo src paths for string extraction: {SRC_PATHS}"
            f"echo pot file: {POT_PATH}"
            f"echo mo files: {MO_PATHS}"
            f"echo po files: {PO_PATHS}"
        ],
        "verbosity": 2
    }


def task_babel_init():
    return {
        "actions": [
            f"pybabel init -i {POT_PATH} -d {TDIR} -l %(lang)s"
        ],
        "params": [{
            "name": "lang",
            "default": "",
        }],
        "pos_arg": "lang"
    }


def task_babel_extract():
    return {
        "actions": [
            f"pybabel extract -F babel.cfg -o {POT_PATH} {SRC_PATHS}"
        ]
    }


def task_babel_extractupdate():
    return {
        "actions": [
            f"pybabel extract -F babel.cfg -o {POT_PATH} {SRC_PATHS}",
            f"pybabel update -d {TDIR} -i {POT_PATH}"
        ]
    }


def task_babel_update():
    return {
        "actions": [
            f"pybabel update -d {TDIR} -i {POT_PATH}"
        ]
    }
