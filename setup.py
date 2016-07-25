#!/usr/bin/env python
import os, setuptools, itertools, ast

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"

PKG_DIR = os.path.dirname(__file__)
MODULE_FILE = os.path.join(PKG_DIR, "pytest_doctest_custom.py")

with open(os.path.join(PKG_DIR, "README.rst"), "r") as f:
    README = f.read().splitlines()

def not_eq(value):
    return lambda el: el != value

def get_block(name, data):
    lines = itertools.dropwhile(not_eq(BLOCK_START % name), data)
    next(lines) # Skip the start line, raise an error if there's no start line
    return "\n".join(itertools.takewhile(not_eq(BLOCK_END % name), lines))

def all_but_block(name, data, remove_empty_next=True):
    it = iter(data)
    before = list(itertools.takewhile(not_eq(BLOCK_START % name), it))
    after = list(itertools.dropwhile(not_eq(BLOCK_END % name), it))[1:]
    if remove_empty_next and after and after[0].strip() == "":
        return "\n".join(before + after[1:])
    return "\n".join(before + after)

def single_line(data):
    return data.strip().replace("\n", " ")

def get_assignment(fname, varname):
    with open(fname, "r") as f:
        for n in ast.parse(f.read(), filename=fname).body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                                         and n.targets[0].id == varname:
                return eval(compile(ast.Expression(n.value), fname, "eval"))

metadata = {
  "name": "pytest-doctest-custom",
  "version": get_assignment(MODULE_FILE, "__version__"),
  "author": "Danilo J. S. Bellini",
  "author_email": "danilo.bellini.gmail.com",
  "url": "http://github.com/danilobellini/pytest-doctest-custom",
  "description": single_line(get_block("summary", README)),
  "long_description": all_but_block("summary", README),
  "license": "MIT",
  "py_modules": ["pytest_doctest_custom"],
  "install_requires": ["pytest>=2.1"],
  "entry_points": {"pytest11": ["doctest_custom = pytest_doctest_custom"]},
}

metadata["classifiers"] = """
Development Status :: 2 - Pre-Alpha
Framework :: Pytest
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Operating System :: POSIX :: Linux
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Testing
""".strip().splitlines()

setuptools.setup(**metadata)
