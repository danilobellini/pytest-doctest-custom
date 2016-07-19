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
methods/functions instead of printing ones, as printer objects commonly
assigns themselves to ``sys.stdout`` on initialization and the doctest runner
collects printed data by shortly mocking such stream.

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

You can customize its parameters such as the ``max_width`` and
``max_seq_length`` by creating a custom function for your needs, e.g. by
adding this to the ``conftest.py`` module and calling py.test with
``--doctest-repr=conftest:doctest_pretty``:

.. code-block:: python

  # conftest.py
  from IPython.lib.pretty import pretty
  def doctest_pretty(value):
      return pretty(value, max_width=72)

This pretty printer sorts sets, frozensets and dicts (by keys), breaks lines
with fixed indentation, and has a consistent set/frozenset printing result for
testing on both Python 2 and 3 (CPython 2.7 and 3.3+). But it's not a Python
standard library, such printer need IPython as a requirement for running the
tests, which comes with much more stuff, not just the pretty printer.

In PyPy that representation printer shows any dict as a dictproxy (tested with
IPython 5.0.0, PyPy 5.3.1) because they're all the same and the dict printer
gets replaced, so a hack is required to ensure a common behavior between
CPython and PyPy. You can create a ``pytest_configure`` hook in the very same
``conftest.py`` either to monkeypatch to ``types.DictProxyType`` a dict
derivative like ``type("dictproxy", (dict,), {})`` reloading the
``IPython.lib.pretty`` module afterwards, or to rebuild the
``IPython.lib.pretty`` dict representation printer by assigning back its
``_dict_pprinter_factory("{", "}", dict)`` to its ``_type_pprinters[dict]``.

* *Python Standard Library Pretty Printer*

You can use the ``pprint.pformat`` function directly with
``--doctest-repr=ppretty:pformat``. You can't directly use the ``pprint``
method from ``pprint.PrettyPrinter`` objects.

To customize its parameters such as ``width`` and ``indent``, you can put a
``PrettyPrinter`` object in your code, for example:

.. code-block:: python

  # conftest.py
  import pprint
  doctest_pp = pprint.PrettyPrinter(width=72)

To run py.test with the ``pformat`` attribute of that ``PrettyPrinter``
instance, giving with ``--doctest-repr=conftest:doctest_pp.pformat`` shall be
enough.

The standard library pretty printer sorts dicts (by keys), breaks lines with a
custom indentation size, but several containers have a result that depends on
the Python version (e.g. empty set as ``"set()"`` in Python 2.6 and 3 but as
``set([])`` in Python 2.7, single item set as ``{item}`` in Python 3 but as
``set([item])`` in Python 2). On the other hand, this is a Python standard
library, there's no extra requirement for tests, and behaves in PyPy as it
does in CPython.


Installing
----------

You can either use pip::

  pip install pytest-doctest-custom

Or setup.py directly::

  python setup.py install


----

Copyright (C) 2016 Danilo de Jesus da Silva Bellini