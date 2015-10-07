# .. -*- coding: utf-8 -*-
#
# *****************************
# mav_gui_test.py - Unit tests.
# *****************************
#
# Imports
# =======
# Library
# -------
import sys
from os.path import dirname, join
#
# Third-party
# -----------
import pytest
from PyQt4.QtCore import Qt
#
# Local
# -----
from mav_gui import MyDialog
#
#
# Testing
# =======
# Use a `fixture <https://pytest.org/latest/fixture.html>`_ to:
#
# 1. Set up for a test, by contructing ``md``.
# 2. Tear down after a test using a `request <https://pytest.org/latest/fixture.html#fixture-finalization-executing-teardown-code>`_
#    object.
# 3. Use the function scope to run setup/teardown around every test.
@pytest.fixture(scope='function')
def myDialog(qtbot, request):
    # Setup.
    md = MyDialog()
    md.show()
    qtbot.addWidget(md)

    # Teardown.
    request.addfinalizer(md.terminate)

    return md

# TestMavGui
# ----------
class TestMavGui(object):
    # Check that fly time slider changes update the text box.
    def test_1(self, myDialog):
        myDialog.hsFlyTime.setValue(10)
        assert myDialog.leFlyTime.text() == '10'

    # Check that fly time text box changes update the slider.
    def test_2(self, myDialog, qtbot):
        myDialog.leFlyTime.setText('20')
        # Bug: On Windows, qtbot.keyClicks(myDialog.leFlyTime, '\n') crashes.
        qtbot.keyClick(myDialog.leFlyTime, Qt.Key_Enter)
        assert myDialog.hsFlyTime.value() == 20

    # Check that charge time slider changes update the text box.
    def test_3(self, myDialog):
        myDialog.hsChargeTime.setValue(10)
        assert myDialog.leChargeTime.text() == '10'

    # Check that charge time text box changes update the slider.
    def test_4(self, myDialog, qtbot):
        myDialog.leChargeTime.setText('20')
        # Bug: On Windows, qtbot.keyClicks(myDialog.leFlyTime, '\n') crashes.
        qtbot.keyClick(myDialog.leChargeTime, Qt.Key_Enter)
        assert myDialog.hsChargeTime.value() == 20

    # Check that invalid strings aren't allowed in the edit boxes.
    def test_5(self, myDialog, qtbot):
        myDialog.leFlyTime.setText('30')
        qtbot.keyClicks(myDialog.leFlyTime, 'hello')
        assert myDialog.leFlyTime.text() == '30'

        # Must clear the text before trying to type more text.
        myDialog.leFlyTime.setText('')
        qtbot.keyClicks(myDialog.leFlyTime, '999')
        assert myDialog.leFlyTime.text() == '99'


    def test_6(self, qtbot):
        assert False
        
        
