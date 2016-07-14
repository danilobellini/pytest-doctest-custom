"""Py.test doctest custom plugin"""
# By Danilo J. S. Bellini
import sys, functools

def printer(value):
    """Prints the object representation using the given custom formatter."""
    if value is not None:
        print(printer.repr(value)) # This attribute has to be set elsewhere

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

def pytest_configure(config):
    """
    Hook for changing ``doctest.DocTestRunner.run`` method so that the
    ``sys.__displayhook__`` calls the given printer function while a doctest
    is running.
    """
    import doctest
    enable_printer = temp_replace(sys, "__displayhook__", printer)
    doctest.DocTestRunner.run = enable_printer(doctest.DocTestRunner.run)
    # As the public method doctest.DocTestRunner.run replaces sys.displayhook
    # by sys.__displayhook__, we could also had changed "displayhook" on the
    # _DocTestRunner__run protected method
