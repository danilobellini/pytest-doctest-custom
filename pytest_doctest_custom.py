"""Py.test doctest custom plugin"""
# By Danilo J. S. Bellini
import sys, functools, pytest

__version__ = "1.0.0"

# Compatibility stuff
try:
    import builtins # Python 3
except ImportError:
    import __builtin__ as builtins
try:
    from importlib import import_module # Python 2.7+
except ImportError:
    def import_module(module_name):
        return __import__(module_name, fromlist=module_name.split(".")[:-1])

def printer(value):
    """Prints the object representation using the given custom formatter."""
    if value is not None:
        representation = printer.repr(value)
        if representation is not None: # Formatter or standard output printer?
            print(representation)

def temp_replace(obj, attr_name, value):
    """
    Returns a decorator that replaces obj.attr = value before calling the
    wrapped function and restores obj.attr afterwards.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            backup = getattr(obj, attr_name)
            setattr(obj, attr_name, value)
            try:
                result = func(*args, **kwargs)
            finally:
                setattr(obj, attr_name, backup)
            return result
        return wrapper
    return decorator

def replace_exception(raised, to_raise):
    """
    Parametrized decorator for replacing exception class or tuple of
    classes ``raised`` by ``to_raise`` called with the previously raised
    exception as its sole argument.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except raised as exc:
                raise to_raise(exc)
        return wrapper
    return decorator

class PluginError(pytest.UsageError):
    """General pytest-doctest-custom plugin usage/invocation error."""
    def __init__(self, exc):
        msg = "[{0}] {1}".format(type(exc).__name__, exc)
        super(PluginError, self).__init__(msg)

class StandardStreamProxy(object):
    """
    Proxy class that grants deferred access to stream objects like
    ``sys.stdout``, allowing the replacement of the underlying stream.
    """
    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr_name):
        return getattr(self.stream, attr_name)

    @property
    def _dname(self): # sys dunder name (fallback to avoid a recursion cycle)
        return self._name.join(["__"] * 2)

    @property
    def stream(self):
        obj = getattr(sys, self._name)
        return obj if obj is not self else getattr(sys, self._dname)

stdout_proxy = StandardStreamProxy("stdout")
stderr_proxy = StandardStreamProxy("stderr")

@temp_replace(sys, "stdout", stdout_proxy) # For import time assignments
@temp_replace(sys, "stderr", stderr_proxy)
@replace_exception((ImportError, AttributeError, ValueError), PluginError)
def parse_address(address):
    """
    Gets a "module.submodule.submodule:object.attribute.attribute" object
    from this string-like address (with as many nesting levels as needed).
    """
    if not address:
        raise ValueError("Empty doctest-repr address")
    if address.count(":") > 1:
        raise ValueError("Multiple colon in doctest-repr address")
    if ":" in address:
        module_name, func_name = address.split(":", 1)
        module = import_module(module_name)
    else:
        func_name = address
        module = builtins
    return functools.reduce(getattr, func_name.split("."), module)

HELP = {
  "plugin": "custom display hook for doctests",
  "repr": "MODULE:CALLABLE address to a representation formatter or printer "
          "(e.g. IPython.lib.pretty:pretty, pprint:pformat, ascii, repr)",
}

def pytest_addoption(parser):
    """Hook that adds the plugin option for customizing the plugin."""
    group = parser.getgroup("doctest_custom", HELP["plugin"])
    group.addoption("--doctest-repr", default=None, help=HELP["repr"])

def pytest_configure(config):
    """
    Config time (before session starts) hook that:

    1. Parses/validates the plugin options;

    2. Changes ``doctest.DocTestRunner.run`` method so that the
    ``sys.__displayhook__`` and ``sys.displayhook`` are the plugin printer
    function while a doctest is running, restoring them back afterwards.
    """
    doctest_repr = config.option.doctest_repr
    if doctest_repr is not None:
        import doctest
        printer.repr = parse_address(doctest_repr)
        enable_printer = temp_replace(sys, "__displayhook__", printer)
        doctest.DocTestRunner.run = enable_printer(doctest.DocTestRunner.run)
    # As the public method doctest.DocTestRunner.run replaces sys.displayhook
    # by sys.__displayhook__, that's enough. We could also had changed the
    # displayhook on the _DocTestRunner__run protected method leaving the
    # __displayhook__ as it is, for the sake of customizing doctests outputs
