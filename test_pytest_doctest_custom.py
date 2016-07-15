pytest_plugins = "pytester"  # Enables the testdir fixture

def test_help_message(testdir):
    result = testdir.runpytest('--help')
    from pytest_doctest_custom import _help
    result.stdout.fnmatch_lines([
      _help["plugin"] + ":",
      _help["repr"][:30].join("**"),
    ])
