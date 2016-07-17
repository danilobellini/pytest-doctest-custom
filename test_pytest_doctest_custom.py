import re, os, sys, pytest, pytest_doctest_custom

pytest_plugins = "pytester"  # Enables the testdir fixture

PYPY = any(k.startswith("pypy") for k in dir(sys))
PY2 = sys.version_info[0] == 2
SPLIT_DOCTEST = pytest.__version__ >= "2.4"

def join_lines(before, after, src):
    """
    Remove the newline and indent between a pair of lines where the first
    ends with ``before`` and the second starts with ``after``
    """
    before_re = "][".join(before).join("[]")
    after_re = "][".join(after).join("[]")
    regex = "\n\\s*".join([before_re, after_re])
    return re.sub(regex, " ".join([before, after]), src)


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


class TestPPrintAsRepr(object):
    args = "--doctest-repr=pprint:pformat", "--verbose", "--doctest-modules"

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
        src_fail = join_lines(",", "[", self.src_list)
        testdir.makepyfile(src_fail)
        result = testdir.runpytest(*self.args)
        result.assert_outcomes(passed=1, skipped=0, failed=1)
        dt_name = "test_list_fail.one_to" if SPLIT_DOCTEST else "doctest]"
        result.stdout.fnmatch_lines([
          "test_list_fail.py*%s FAILED" % dt_name,
          "test_list_fail.py*test_one_to PASSED",
        ])

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
    ''' % ("set([3])" if PY2 else "{3}")

    def test_sorted_dict_pass(self, testdir):
        testdir.makepyfile(self.src_dict)
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
        src_fail = join_lines(",", "'", self.src_dict)
        testdir.makepyfile(src_fail)
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
        keys = locals()
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
