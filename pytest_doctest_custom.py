"""Py.test doctest custom plugin"""
# By Danilo J. S. Bellini
import sys, functools

def printer(value):
    """Prints the object representation using the given custom formatter."""
    if value is not None:
        print(printer.repr(value))

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
            result = func(*args, **kwargs)
            setattr(obj, attr_name, backup)
            return result
        return wrapper
    return decorator

def obj_by_module_attr_address(address):
    """
    Gets a "module.submodule.submodule:object.attribute.attribute" from this
    string-like address (with as many nesting levels as needed).
    """
    if ":" not in address:
        bname = "__builtin__" if sys.version_info[0] == 2 else "builtins"
        address = ":".join([bname, address])
    module_name, func_name = address.split(":", 1)
    module = __import__(module_name, fromlist=module_name.split(".")[:-1])
    return functools.reduce(getattr, func_name.split("."), module)

_help = {
  "plugin": "Customizing the display hook for doctests",
  "repr": "Address to a object representation callable as a "
          "'module:callable' string. Calling module.callable(obj) "
          "should format the doctest output obj. Common values would"
          "be IPython.lib.pretty:pretty, pprint:pformat, ascii.",
}

def pytest_addoption(parser):
    """Hook that adds the plugin option for customizing the plugin."""
    group = parser.getgroup("doctest_custom", _help["plugin"])
    group.addoption("--doctest-repr", action="store", dest="doctest_repr",
                    default="repr", help=_help["repr"])

def pytest_configure(config):
    """
    Hook for changing ``doctest.DocTestRunner.run`` method so that the
    ``sys.__displayhook__`` calls the given printer function while a doctest
    is running, restoring it back afterwards, and also to get the plugin
    options.
    """
    import doctest
    printer.repr = obj_by_module_attr_address(config.option.doctest_repr)
    enable_printer = temp_replace(sys, "__displayhook__", printer)
    doctest.DocTestRunner.run = enable_printer(doctest.DocTestRunner.run)
    # As the public method doctest.DocTestRunner.run replaces sys.displayhook
    # by sys.__displayhook__, we could also had changed "displayhook" on the
    # _DocTestRunner__run protected method
