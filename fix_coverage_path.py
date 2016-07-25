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
new_cd.update(old_cd, pa)
new_cd.write_file(coverage_file_name)
