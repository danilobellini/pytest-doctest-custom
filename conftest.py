"""
Adds to old py.test versions resources used by test_pytest_docstring_custom.py
but not by the plugin itself.
"""
import pytest

# 2.8.0+ pytester plugin RunResult.assert_outcomes
if pytest.__version__ < "2.8":
    def assert_outcomes(self, **kwargs):
        for key in kwargs:
            assert kwargs[key] == self.parseoutcomes().get(key, 0)
    from _pytest import pytester
    pytester.RunResult.assert_outcomes = assert_outcomes

# 2.4.0+ pytest.mark.skipif with general expressions instead of strings
if pytest.__version__ < "2.4":
    skipif = pytest.mark.skipif
    pytest.mark.skipif = lambda cond, reason: skipif(str(cond), reason=reason)

# 2.3.0+ pytest.fixture
if pytest.__version__ < "2.3":
    def fixture(func):
        import inspect
        name = "pytest_funcarg__%s" % func.__name__
        inspect.currentframe().f_back.f_locals[name] = func
        return func
    pytest.fixture = fixture
