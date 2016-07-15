import os, sys, pytest

pytest_plugins = "pytester"  # Enables the testdir fixture

commonargs = "--verbose", "--doctest-modules"

class TestStrLowerAsRepr(object):
    src_pass = """
        '''
        >>> "This IS a TEsT! =D"
        this is a test! =d
        '''
    """
    src_fail = src_pass.replace("=d", "=D")

    def test_valid_src(self, testdir):
        pyfile = testdir.makepyfile(self.src_pass)
        result = testdir.runpytest("--doctest-repr", "str.lower", *commonargs)
        result.assert_outcomes(passed=1, skipped=0, failed=0)
        result.stdout.fnmatch_lines("test_valid_src.py*PASSED")

    def test_invalid_src(self, testdir):
        pyfile = testdir.makepyfile(self.src_fail)
        result = testdir.runpytest("--doctest-repr", "str.lower", *commonargs)
        result.assert_outcomes(passed=0, skipped=0, failed=1)
        result.stdout.fnmatch_lines("test_invalid_src.py*FAILED")

def test_help_message(testdir):
    result = testdir.runpytest('--help')
    from pytest_doctest_custom import _help
    result.stdout.fnmatch_lines([
      _help["plugin"].join("*:"),
      _help["repr"][:30].join("**"),
    ])

@pytest.mark.skipif("TOXENV" not in os.environ, reason="Not running with tox")
def test_tox_python_pytest_versions():
    """Meta-test to ensure Python and py.test versions are correct."""
    py_ver, pytest_ver = os.environ["TOXENV"].split("-")
    if any(k.startswith("pypy") for k in dir(sys)):
      assert py_ver == "pypy"
    else:
      assert py_ver == "py%d%d" % sys.version_info[:2]
    assert pytest_ver == "pytest" + pytest.__version__.replace(".", "")
