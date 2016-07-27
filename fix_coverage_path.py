#!/usr/bin/env python
# By Danilo J. S. Bellini
"""
Script to update the file paths stored in a single coverage data file

Syntax: python fixpath.py DATA_FILE OLD_PATH NEW_PATH
"""
import sys, os
from coverage.data import CoverageData, PathAliases

coverage_file_name, old_path, new_path = sys.argv[1:]

pa = PathAliases()
pa.add(old_path, new_path)

old_cd = CoverageData()
old_cd.read_file(coverage_file_name)

new_cd = CoverageData()
try:
    new_cd.update(old_cd, pa)
except AttributeError: # Coverage 3.7.1 (CPython 3.2)
    namer = lambda f: os.path.abspath(os.path.expanduser(pa.map(f)))
    new_cd.lines = dict((namer(f), d) for f, d in old_cd.lines.items())
    new_cd.arcs = dict((namer(f), d) for f, d in old_cd.arcs.items())
new_cd.write_file(coverage_file_name)
