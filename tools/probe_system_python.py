"""Report a shared interpreter's version without importing app dependencies.

Run with -I: ignores PYTHONPATH and user site packages. Does not change Python.
A virtual environment is deliberately not accepted as the system interpreter.
"""
import sys

if sys.prefix == sys.base_prefix:
    print("%d.%d" % sys.version_info[:2])
else:
    print("virtual")
