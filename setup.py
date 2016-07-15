#!/usr/bin/env python
import setuptools

metadata = {
  "name": "pytest-doctest-custom",
  "version": "0.1.0",
  "author": "Danilo J. S. Bellini",
  "author_email": "danilo.bellini.gmail.com",
  "url": "http://github.com/danilobellini/pytest-doctest-custom",
  "py_modules": ["pytest_doctest_custom"],
  "install_requires": ["pytest>=2.8.5"],
  "entry_points": {"pytest11": ["doctest_custom = pytest_doctest_custom"]},
  "description": "A py.test plugin to use a custom "
                 "printer/formatter for doctest results.",
}

metadata["classifiers"] = """
Development Status :: 2 - Pre-Alpha
Framework :: Pytest
Intended Audience :: Developers
Operating System :: POSIX :: Linux
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Testing
""".strip().splitlines()

setuptools.setup(**metadata)