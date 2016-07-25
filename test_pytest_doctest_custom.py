"""Test suite for the pytest-doctest-custom plugin."""
import re, os, sys, pytest, pytest_doctest_custom

pytest_plugins = "pytester"  # Enables the testdir fixture

PYPY = any(k.startswith("pypy") for k in dir(sys))
PY2 = sys.version_info[0] == 2
SPLIT_DOCTEST = pytest.__version__ >= "2.4"


@pytest.fixture
def here(request):
    """
    Empty fixture to include the current dir to the system path,
    required for modules to be imported in testdir tests.
    """
    if sys.path[0] != "":
        old_sys_path = sys.path
        sys.path = [""] + old_sys_path # Adds the test dir to the path
        def finalizer():
            sys.path = old_sys_path
        request.addfinalizer(finalizer)


def join_lines(src, before, after, sep=" "):
    """
    Remove the newline and indent between a pair of lines where the first
    ends with ``before`` and the second starts with ``after``, replacing
    it by the ``sep``.
    """
    before_re = "][".join(before).join("[]")
    after_re = "][".join(after).join("[]")
    regex = "\n\\s*".join([before_re, after_re])
    return re.sub(regex, sep.join([before, after]), src)


class JoinedDescr(object):
    """Descriptor that performs a deferred call to join_lines."""
    def __init__(self, attr_name, **kwargs):
        self.attr_name = attr_name
        self.kwargs = kwargs
    def __get__(self, instance, owner):
        return join_lines(getattr(instance, self.attr_name), **self.kwargs)


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


# "Abstract" tests below are for pretty printers with some sort of multiline
# and/or sorted contents. Also tests single line behavior, for which a custom
# representation formatter object should be stored in conftest.py to ensure a
# larger width (150 is enough).

class ATestList(object):
    """
    Abstract attributes: args, args_conftest, src_conftest, args_mymodule,
                         src_mymodule
    """
    src_list = '''
        def one_to(n):
            """
            >>> [[a*b for a in one_to(4)] for b in one_to(9)]
            [[1, 2, 3, 4],
             [2, 4, 6, 8],
             [3, 6, 9, 12],
             [4, 8, 12, 16],
             [5, 10, 15, 20],
             [6, 12, 18, 24],
             [7, 14, 21, 28],
             [8, 16, 24, 32],
             [9, 18, 27, 36]]
            """
            return range(1, n + 1)
        def test_one_to(): # Meta-test
            assert list(one_to(0)) == []
            assert list(one_to(1)) == [1]
            assert list(one_to(2)) == [1, 2]
            assert list(one_to(3)) == [1, 2, 3]
    '''
    src_list_no_line_break = JoinedDescr("src_list", before=",", after="[")

    def test_list_pass(self, testdir):
        testdir.makepyfile(self.src_list)
        result = testdir.runpytest(*self.args)
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        dt_name = "test_list_pass.one_to" if SPLIT_DOCTEST else "doctest]"
        result.stdout.fnmatch_lines([
          "test_list_pass.py*%s PASSED" % dt_name,
          "test_list_pass.py*test_one_to PASSED",
        ])

    def test_list_fail(self, testdir):
        testdir.makepyfile(self.src_list_no_line_break)
        result = testdir.runpytest(*self.args)
        result.assert_outcomes(passed=1, skipped=0, failed=1)
        dt_name = "test_list_fail.one_to" if SPLIT_DOCTEST else "doctest]"
        result.stdout.fnmatch_lines([
          "test_list_fail.py*%s FAILED" % dt_name,
          "test_list_fail.py*test_one_to PASSED",
        ])

    def test_list_conftest_fix_width(self, testdir):
        testdir.makeconftest(self.src_conftest)
        testdir.makepyfile(self.src_list_no_line_break)
        result = testdir.runpytest(*self.args_conftest)
        if SPLIT_DOCTEST:
            result.assert_outcomes(passed=2, skipped=0, failed=0)
            dt_name = "test_list_conftest_fix_width.one_to"
        else:
            result.assert_outcomes(passed=3, skipped=0, failed=0)
            result.stdout.fnmatch_lines(["conftest.py*doctest] PASSED"])
            dt_name = "doctest]"
        result.stdout.fnmatch_lines([
          "test_list_conftest_fix_width.py*%s PASSED" % dt_name,
          "test_list_conftest_fix_width.py*test_one_to PASSED",
        ])

    def test_list_mymodule_fix_width(self, testdir, here):
        testdir.makepyfile(mymodule=self.src_mymodule)
        testdir.makepyfile(self.src_list_no_line_break)
        result = testdir.runpytest(*self.args_mymodule)
        if SPLIT_DOCTEST:
            result.assert_outcomes(passed=2, skipped=0, failed=0)
            dt_name = "test_list_mymodule_fix_width.one_to"
        else:
            result.assert_outcomes(passed=3, skipped=0, failed=0)
            result.stdout.fnmatch_lines(["mymodule.py*doctest] PASSED"])
            dt_name = "doctest]"
        result.stdout.fnmatch_lines([
          "test_list_mymodule_fix_width.py*%s PASSED" % dt_name,
          "test_list_mymodule_fix_width.py*test_one_to PASSED",
        ])


class ATestDict(object):
    """
    Abstract attributes: args, args_conftest, src_conftest, args_mymodule,
                         src_mymodule, set3repr
    """
    src_dict = '''
        """
        >>> {"hey": upper("Why?"),
        ...  "abcdefgh": set([3]),
        ...  "weird": 2,
        ...  "was": -5}
        {'abcdefgh': %s, 'hey': 'WHY?', 'was': -5, 'weird': 2}
        """
        def upper(anything):
            """
            >>> from string import ascii_lowercase as low
            >>> dict(zip(low[::-3], map(upper, low)))
            {'b': 'I',
             'e': 'H',
             'h': 'G',
             'k': 'F',
             'n': 'E',
             'q': 'D',
             't': 'C',
             'w': 'B',
             'z': 'A'}
            """
            return anything.upper()
    '''
    src_dict_no_line_break = JoinedDescr("src_dict", before=",", after="'")

    def test_sorted_dict_pass(self, testdir):
        testdir.makepyfile(self.src_dict % self.set3repr)
        result = testdir.runpytest(*self.args)
        if SPLIT_DOCTEST:
            result.assert_outcomes(passed=2, skipped=0, failed=0)
            result.stdout.fnmatch_lines([
              "*test_sorted_dict_pass PASSED",
              "*test_sorted_dict_pass.upper PASSED",
            ])
        else:
            result.assert_outcomes(passed=1, skipped=0, failed=0)
            result.stdout.fnmatch_lines(["*doctest] PASSED"])

    def test_sorted_dict_half_fail(self, testdir):
        testdir.makepyfile(self.src_dict_no_line_break % self.set3repr)
        result = testdir.runpytest(*self.args)
        if SPLIT_DOCTEST:
            result.assert_outcomes(passed=1, skipped=0, failed=1)
            result.stdout.fnmatch_lines([
              "*test_sorted_dict_half_fail PASSED",
              "*test_sorted_dict_half_fail.upper FAILED",
            ])
        else:
            result.assert_outcomes(passed=0, skipped=0, failed=1)
            result.stdout.fnmatch_lines(["*doctest] FAILED"])

    def test_sorted_dict_conftest_fix_width(self, testdir):
        testdir.makeconftest(self.src_conftest)
        testdir.makepyfile(self.src_dict_no_line_break % self.set3repr)
        result = testdir.runpytest(*self.args_conftest)
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_sorted_dict_conftest_fix_width PASSED",
          "*test_sorted_dict_conftest_fix_width.upper PASSED",
        ] if SPLIT_DOCTEST else [
          "*doctest] PASSED",
          "*doctest] PASSED",
        ])

    def test_sorted_dict_mymodule_fix_width(self, testdir, here):
        testdir.makepyfile(mymodule=self.src_mymodule)
        testdir.makepyfile(self.src_dict_no_line_break % self.set3repr)
        result = testdir.runpytest(*self.args_mymodule)
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_sorted_dict_mymodule_fix_width PASSED",
          "*test_sorted_dict_mymodule_fix_width.upper PASSED",
        ] if SPLIT_DOCTEST else [
          "*doctest] PASSED",
          "*doctest] PASSED",
        ])


class ATestSet(object):
    """
    Abstract attributes: args, args_conftest, src_conftest, args_mymodule,
                         src_mymodule
    """
    src_set = '''
        """
        >>> import string
        >>> set(string.digits)
        {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        """
        from functools import reduce
        def union(*args):
            """
            >>> union([5734500, 545312, 50200], range(50198,50208), [50205])
            {50198,
             50199,
             50200,
             50201,
             50202,
             50203,
             50204,
             50205,
             50206,
             50207,
             545312,
             5734500}
            """
            return reduce(set.union, map(set, args))
    '''
    src_set_no_line_break = JoinedDescr("src_set", before=",", after="5")

    def test_sorted_set_pass(self, testdir):
        testdir.makepyfile(self.src_set)
        result = testdir.runpytest(*self.args)
        if SPLIT_DOCTEST:
            result.assert_outcomes(passed=2, skipped=0, failed=0)
            result.stdout.fnmatch_lines([
              "*test_sorted_set_pass PASSED",
              "*test_sorted_set_pass.union PASSED",
            ])
        else:
            result.assert_outcomes(passed=1, skipped=0, failed=0)
            result.stdout.fnmatch_lines(["*doctest] PASSED"])

    def test_sorted_set_half_fail(self, testdir):
        testdir.makepyfile(self.src_set_no_line_break)
        result = testdir.runpytest(*self.args)
        if SPLIT_DOCTEST:
            result.assert_outcomes(passed=1, skipped=0, failed=1)
            result.stdout.fnmatch_lines([
              "*test_sorted_set_half_fail PASSED",
              "*test_sorted_set_half_fail.union FAILED",
            ])
        else:
            result.assert_outcomes(passed=0, skipped=0, failed=1)
            result.stdout.fnmatch_lines(["*doctest] FAILED"])

    def test_sorted_set_conftest_fix_width(self, testdir):
        testdir.makeconftest(self.src_conftest)
        testdir.makepyfile(self.src_set_no_line_break)
        result = testdir.runpytest(*self.args_conftest)
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_sorted_set_conftest_fix_width PASSED",
          "*test_sorted_set_conftest_fix_width.union PASSED",
        ] if SPLIT_DOCTEST else [
          "*doctest] PASSED",
          "*doctest] PASSED",
        ])

    def test_sorted_set_mymodule_fix_width(self, testdir, here):
        testdir.makepyfile(mymodule=self.src_mymodule)
        testdir.makepyfile(self.src_set_no_line_break)
        result = testdir.runpytest(*self.args_mymodule)
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_sorted_set_mymodule_fix_width PASSED",
          "*test_sorted_set_mymodule_fix_width.union PASSED",
        ] if SPLIT_DOCTEST else [
          "*doctest] PASSED",
          "*doctest] PASSED",
        ])


class ATestPPrint(ATestList, ATestDict):
    set3repr = "set([3])" if PY2 else "{3}"


class TestPPrintPFormatAsRepr(ATestPPrint):
    args = "--doctest-repr=pprint:pformat", "--verbose", "--doctest-modules"

    args_conftest = ("--doctest-repr", "conftest:doctest_pp.pformat",
                     "--verbose", "--doctest-modules")

    args_mymodule = ("--doctest-repr", "mymodule:doctest_pp.pformat",
                     "--verbose", "--doctest-modules")

    src_conftest = src_mymodule = '''
        import pprint
        doctest_pp = pprint.PrettyPrinter(width=150)
    '''


class TestPPrintPPrintAsRepr(ATestPPrint):
    args = "--doctest-repr=pprint:pprint", "--verbose", "--doctest-modules"

    args_conftest = ("--doctest-repr", "conftest:doctest_pp.pprint",
                     "--verbose", "--doctest-modules")

    args_mymodule = ("--doctest-repr", "mymodule:doctest_pp.pprint",
                     "--verbose", "--doctest-modules")

    src_conftest = '''
        import pprint
        from pytest_doctest_custom import stdout_proxy
        doctest_pp = pprint.PrettyPrinter(width=150, stream=stdout_proxy)
    '''

    src_mymodule = TestPPrintPFormatAsRepr.src_mymodule


class ATestIPython(ATestList, ATestDict, ATestSet):
    set3repr = "{3}"
    if PYPY: # Fix the undesired IPython replacement of the dict
             # representation printer by the dictproxy one in PyPy, using the
             # IPython dict pretty printer factory itself for such.
        src_dict = ATestDict.src_dict + '''
        from IPython.lib.pretty import _type_pprinters, _dict_pprinter_factory
        _type_pprinters[dict] = _dict_pprinter_factory("{", "}", dict)
        '''


class TestIPythonPrettyAsRepr(ATestIPython):
    args = ("--doctest-repr=IPython.lib.pretty:pretty",
            "--verbose", "--doctest-modules")

    args_conftest = ("--doctest-repr", "conftest:doctest_pretty",
                     "--verbose", "--doctest-modules")

    args_mymodule = ("--doctest-repr", "mymodule:doctest_pretty",
                     "--verbose", "--doctest-modules")

    src_conftest = src_mymodule = '''
        from IPython.lib.pretty import pretty
        def doctest_pretty(value):
            return pretty(value, max_width=150)
    '''


class TestIPythonPPrintAsRepr(ATestIPython):
    args = ("--doctest-repr=IPython.lib.pretty:pprint",
            "--verbose", "--doctest-modules")

    args_conftest = ("--doctest-repr", "conftest:doctest_pprint",
                     "--verbose", "--doctest-modules")

    args_mymodule = ("--doctest-repr", "mymodule:doctest_pprint",
                     "--verbose", "--doctest-modules")

    src_conftest = src_mymodule = '''
        from IPython.lib.pretty import pprint
        def doctest_pprint(value):
            return pprint(value, max_width=150)
    '''


class TestReprAddress(object):
    msg_import = "ERROR: *ImportError* No module named *{module}*"
    msg_attr = "ERROR: *AttributeError* *{obj}* has no attribute '{attr}'"

    def run_and_assert_stderr_msg_stout_empty(self, td, msg, address, **kws):
        args = "--doctest-repr=" + address, "--verbose", "--doctest-modules"
        address_split = address.split(":")
        attr_raw_split = address_split.pop().split(".")
        module = address_split.pop() if address_split else ""
        attr = attr_raw_split.pop()
        obj = attr_raw_split.pop() if attr_raw_split else "module"
        keys = {"module": module, "obj": obj, "attr": attr}
        keys.update(kws)

        result = td.runpytest(*args)
        result.stderr.fnmatch_lines(msg.format(**keys))
        assert "\n" not in result.stderr.str().strip() # Only one stderr line
        assert result.stdout.str().strip() == ""

    def test_import_error_not_nested(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_import,
            address = "areallybadnameunavailable_____this_shouldnt_exist:obj")

    def test_import_error_nested_first(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_import,
            address = "areallybadnameunavailable_____this_isnt.something:yet",
            module = "areallybadnameunavailable_____this_isnt")

    def test_import_error_nested_middle(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_import,
            address = "sys.blablablablablah_blhaah.meeeh:obj",
            module = "blablablablablah_blhaah")

    def test_import_error_nested_last(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_import,
            address = "os.path.heeeeeey:data",
            module = "heeeeeey")

    def test_attribute_error_builtin_not_nested(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_attr,
            address = "some_builtin_objThatDoesntExist_atAll")

    def test_attribute_error_builtin_nested(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_attr,
            address = "str.fakyjoint")

    def test_attribute_error_not_nested(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_attr,
            address = "os.path:oh_i_dont_likeIT")

    def test_attribute_error_nested(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir, self.msg_attr,
            address = "itertools:chain.from_iterable.myself",
            obj = "function" if PYPY else "builtin_function_or_method")

    def test_empty(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir,
            msg = "ERROR: *ValueError* Empty doctest-repr address",
            address = "")

    def test_multiple_colon(self, testdir):
        self.run_and_assert_stderr_msg_stout_empty(testdir,
            msg = "ERROR: *ValueError* Multiple colon in doctest-repr address",
            address = "os:sys:version")


class TestPluginEnabled(object):
    src = '''
        """
        >>> getattr(pytest_doctest_custom.printer, "repr", None) is repr
        False
        >>> sys.displayhook is pytest_doctest_custom.printer
        False
        """
        import pytest_doctest_custom, sys
        def test_displayhook():
            assert sys.displayhook is not pytest_doctest_custom.printer
        test_displayhook() # Tests for import time AssertionError
    '''

    def test_disabled(self, testdir):
        testdir.makepyfile(self.src)
        result = testdir.runpytest("--verbose", "--doctest-modules")
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_disabled PASSED",
          "*test_disabled*test_displayhook PASSED",
        ] if SPLIT_DOCTEST else [
          "*doctest] PASSED",
          "*test_disabled*test_displayhook PASSED",
        ])

    def test_repr(self, testdir):
        args = "--verbose", "--doctest-modules", "--doctest-repr=repr"
        testdir.makepyfile(self.src.replace("False", "True"))
        result = testdir.runpytest(*args)
        result.assert_outcomes(passed=2, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_repr PASSED",
          "*test_repr*test_displayhook PASSED",
        ] if SPLIT_DOCTEST else [
          "*doctest] PASSED",
          "*test_repr*test_displayhook PASSED",
        ])

    def test_print(self, testdir, here):
        if PY2:
            testdir.makepyfile(p="def p(value): print(value)")
            args = "--verbose", "--doctest-modules", "--doctest-repr=p:p"
            extra = [] if SPLIT_DOCTEST else ["*doctest] PASSED"]
            passed = 3 - SPLIT_DOCTEST
        else:
            args = "--verbose", "--doctest-modules", "--doctest-repr=print"
            extra = []
            passed = 2
        testdir.makepyfile("True".join(self.src.rpartition("False")[::2]))
        result = testdir.runpytest(*args)
        result.assert_outcomes(passed=passed, skipped=0, failed=0)
        result.stdout.fnmatch_lines(extra + [
          "*test_print PASSED" if SPLIT_DOCTEST else "*doctest] PASSED",
          "*test_print*test_displayhook PASSED",
        ])

    def test_none(self, testdir):
        args = "--verbose", "--doctest-modules", "--doctest-repr=None"
        exc_msg = "*TypeError*'NoneType' object is not callable*"
        testdir.makepyfile(self.src)
        result = testdir.runpytest(*args)
        result.assert_outcomes(passed=1, skipped=0, failed=1)
        result.stdout.fnmatch_lines([
          "*test_none FAILED" if SPLIT_DOCTEST else "*doctest] FAILED",
          "*test_none*test_displayhook PASSED",
          "*FAILURES*",
          "*doctest*",
          "*" + self.src[:self.src.find("\n")].strip(), # 1st src line
          "UNEXPECTED EXCEPTION*" + exc_msg,
          exc_msg,
        ])
        assert result.stderr.str().strip() == ""


class TestDoctestOutputsNone(object):
    src = '''
        """
        >>> None
        >>> 2 + 2
        4
        >>> print("Returns None")
        Returns None
        """
        from __future__ import print_function
        print = print
    '''

    def test_print_as_repr(self, testdir, here):
        testdir.makepyfile(self.src)
        arg = "test_print_as_repr:print" if PY2 else "print"
        result = testdir.runpytest("--verbose", "--doctest-modules",
                                   "--doctest-repr", arg)
        result.assert_outcomes(passed=1, skipped=0, failed=0)
        result.stdout.fnmatch_lines([
          "*test_print_as_repr PASSED"
          if SPLIT_DOCTEST else
          "*doctest] PASSED",
        ])


def test_help_message(testdir):
    testdir.runpytest("--help").stdout.fnmatch_lines([
      pytest_doctest_custom.HELP["plugin"].join("*:"),
      pytest_doctest_custom.HELP["repr"][:30].join("**"),
    ])


@pytest.mark.skipif("TOXENV" not in os.environ, reason="Not running with tox")
def test_tox_python_pytest_versions():
    """Meta-test to ensure Python and py.test versions are correct."""
    py_ver, pytest_ver = os.environ["TOXENV"].split("-")[:2]
    assert py_ver == ("pypy" if PYPY else ("py%d%d" % sys.version_info[:2]))
    assert pytest_ver == "pytest" + pytest.__version__.replace(".", "")
