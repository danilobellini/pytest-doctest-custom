pytest-doctest-custom
=====================

A py.test plugin for customizing string representations of doctest results.


What does it do?
----------------

Change the display hook used by doctest to render the object representations.
Tested on CPython 2.6+, 3.3+ and PyPy, using py.test 2.1+.

For a given code with doctests, you can run::

  py.test --doctest-modules --doctest-repr=IPython.lib.pretty:pretty

That will run the doctest examples as usual, but the results won't be printed
by calling a ``__repr__`` method directly, but by calling the given function
with the resulting value as its single parameter.

To do that, it just needs a representation formatting callable that given an
object, returns a string with its representation. It should be passed as the
``--doctest-repr`` command line option addressed as ``module:object``, with
dots for nested modules/objects. For built-ins like the ``ascii`` function,
you can just remove the ``module:`` prefix.


Common representation formatters/printers
-----------------------------------------

Be careful with the default "printers", you should always use the formatting
methods/functions instead of printing ones, as printer objects like the
``pprint.PrettyPrinter`` assigns themselves to ``sys.stdout`` before it was
mocked by the doctest internals.

* *IPython Pretty Printer* (for output, without the "Out[#]:" prefix)

To use this one, you need to have IPython installed on the testing
environment (e.g. including ``ipython`` in the tox deps list). A possible
tox.ini file for running toctests on a project would be::

  [tox]
  envlist = py{35,34,27}

  [testenv]
  deps = ipython
  commands = py.test {posargs}

  [pytest]
  addopts = --doctest-modules
            --doctest-glob=test_*.rst
            --doctest-repr=IPython.lib.pretty:pretty
            --ignore setup.py

* *Python Standard Library Pretty Printer*

You can use the ``pprint.pformat`` function directly with
``--doctest-repr=ppretty:pformat``.


Installing
----------

You can either use pip::

  pip install pytest-doctest-custom

Or setup.py directly::

  python setup.py install


----

Copyright (C) 2016 Danilo de Jesus da Silva Bellini
