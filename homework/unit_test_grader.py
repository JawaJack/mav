# .. -*- coding: utf-8 -*-
#
# Unit test grader
# ================
# By Bryan A. Jones.
#
# This function runs a series of pytest_ unit tests (by calling the ``run_tests()`` function of ``unit_tester_module_name``) on each file in the ``unit_testee_directory`` and reports its results in ``csv_file_name``. The files to be tested must be named ``stuff_userid_[stuff].py``.
#
# .. warning::
#
#    The ``orig_unit_testee_module_name`` *WILL BE OVERWRITTEN* by this routine.
#
# Setup
# -----
import os, shutil, xml.dom.minidom, csv, importlib, subprocess

def run_all_testees(
  # Specify the module which performs unit tests.
  unit_tester_module_name = 'mav_gui_test',
  # Specify the module tested by ``unit_test_module_name``.
  orig_unit_testee_module_name = 'mav_gui',
  # Specify the directory containing the testees (modules to on which unit tests in ``unit_tester_module_name`` will be run).
  unit_testee_directory = 'hw_grading',
  # Name of the .csv file to produce.
  csv_file_name = 'grades.csv'):

    # Open a ``.csv`` file to store results in and write the header.
    with open(csv_file_name, 'wb') as csvfile:
        grade_writer = csv.writer(csvfile)
        grade_writer.writerow(('Username', 'Homework 6 |267338'))
        #
        # Choose and copy a file to test
        # ------------------------------
        # Choose a file name to test from the ``unit_testee_directory`` and copy it to ``orig_unit_testee_module_name.py``.
        # Iterate through all files to be tested (see listdir_).
        for unit_testee_module_name in os.listdir(unit_testee_directory):
            # Skip any non-Python files.
            if not unit_testee_module_name.endswith('.py'):
                continue
            # Split_ out userid, based on a file name of ``userid-stuff.py``. Therefore, the desired userid is contained in first index of the list produced by splitting.
            userid = unit_testee_module_name.split('_')[1]
            # Copy_ this module to test to the module name expected by the unit tester, so that the unit the unit test module will import it and test it.
            unit_testee_module_path = os.path.join(unit_testee_directory, unit_testee_module_name)
            shutil.copy(unit_testee_module_path, orig_unit_testee_module_name + '.py')
            #
            # Run tests
            # ---------
            # Without this, Python re-imports the same testee module, instead of the newly copied version, probably because the .pyc files is check with a 1-second resolution (see `Stack Overflow question`_). So, remove_ the ``.pyc``. The tester bytecode remains the same, so it doesn't need removal. If the previous file tested had a syntax error, there's no .pyc to remove; use try/except to ignore this.
            try:
                os.remove(orig_unit_testee_module_name + '.pyc')
            except OSError as e:
                print(e)
            # Run the tests.
            print('\n\n\n\nRunning tests on ' + unit_testee_module_path)
            subprocess.call('py.test ' + unit_tester_module_name + '.py --junitxml=unit_test.xml', shell=True)
            #
            # Collect results
            # ---------------
            # Extract grade. The tester must use `pytest to produce XML output`_. Sample output::
            #
            #   <testsuite errors="0" failures="2" name="" skips="0" tests="9" time="0.037">
            #     <testcase classname="mav3d_simulation_test.TestFMav" name="test_shape_t" time="0.000999927520752"/>
            #     <testcase classname="mav3d_simulation_test.TestFMav" name="test_shape_m" time="0.00100016593933">
            #       <failure message="test failure">E   Failed: DID NOT RAISE</failure>
            #     </testcase>
            #   </testsuite>
            #
            # So, use the `XML parser`_ to read the file in.
            ut_xml = xml.dom.minidom.parse('unit_test.xml')
            # Per the sample above, it should produce a list with one element, the testsuite. For example, the above XML becomes ``[<DOM Element: testsuite at 0x4c3ce40>]``.
            testsuite = ut_xml.childNodes[0]
            assert testsuite.nodeName == 'testsuite'
            # Each testcase above reports attributes as a string. Convert them to a float for calculation.
            ts_ga = lambda attr_name : float(testsuite.getAttribute(attr_name))
            # Grade = sucessess/cases. Here, success = everthing but errors, failures, skips.
            grade = 1.0 - (ts_ga('errors') + ts_ga('failures') + ts_ga('skips'))/ts_ga('tests')
            grade_writer.writerow((userid, grade*100))

    # Show the results in Excel.
    os.system(csv_file_name)

if __name__ == '__main__':
    run_all_testees()

# .. _split: http://docs.python.org/2/library/stdtypes.html#str.split
# .. _copy: http://docs.python.org/2/library/shutil.html#directory-and-files-operations
# .. _XML parser: http://docs.python.org/2/library/xml.dom.minidom.html
# .. _pytest to produce XML output: http://pytest.org/latest/usage.html#creating-junitxml-format-files
# .. _listdir: http://docs.python.org/2/library/os.html#files-and-directories
# .. _Stack Overflow question: http://stackoverflow.com/questions/10561349/python-reload-module-does-not-take-effect-immediately
# .. _remove: http://docs.python.org/2/library/os.html#files-and-directories
# .. _pytest: http://pytest.org
