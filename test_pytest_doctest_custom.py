import os, sys, pytest, pytest_doctest_custom

pytest_plugins = "pytester"  # Enables the testdir fixture

PYPY = any(k.startswith("pypy") for k in dir(sys))

class TestStrLowerAsRepr(object):
    src_pass = """
        '''
        >>> "This IS a TEsT! =D"
        this is a test! =d
        '''
    """
    src_fail = src_pass.replace("=d", "=D")
    args = "--doctest-repr", "str.lower", "--verbose", "--doctest-modules"

    def test_valid_src(self, testdir):
        testdir.makepyfile(self.src_pass)
        result = testdir.runpytest(*self.args)
        result.assert_outcomes(passed=1, skipped=0, failed=0)
        result.stdout.fnmatch_lines("test_valid_src.py*PASSED")

    def test_invalid_src(self, testdir):
        testdir.makepyfile(self.src_fail)
        result = testdir.runpytest(*self.args)
        result.assert_outcomes(passed=0, skipped=0, failed=1)
        result.stdout.fnmatch_lines("test_invalid_src.py*FAILED")


def test_help_message(testdir):
    testdir.runpytest("--help").stdout.fnmatch_lines([
      pytest_doctest_custom.HELP["plugin"].join("*:"),
      pytest_doctest_custom.HELP["repr"][:30].join("**"),
    ])


@pytest.mark.skipif("TOXENV" not in os.environ, reason="Not running with tox")
def test_tox_python_pytest_versions():
    """Meta-test to ensure Python and py.test versions are correct."""
    py_ver, pytest_ver = os.environ["TOXENV"].split("-")
    assert py_ver == "pypy" if PYPY else "py%d%d" % sys.version_info[:2]
    assert pytest_ver == "pytest" + pytest.__version__.replace(".", "")
