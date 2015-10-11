# .. -*- coding: utf-8 -*-
#
# *****************************
# mav_gui_test.py - Unit tests.
# *****************************
# .. note::
#
#    The environment variable ``PYTEST_QT_API`` must be set to ``pyqt4v2`` (see the `requirements <https://pytest-qt.readthedocs.org/en/1.7.0/intro.html#requirements>`_) to runs these tests. For example, ``export PYTEST_QT_API=pyqt4v2`` in Linux.
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
from mav_gui import MavDialog, _MAV_STATES
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
def mavDialog(qtbot, request):
    # Setup.
    md = MavDialog(4, 0.5, 1.5)
    md.show()
    qtbot.addWidget(md)

    # Teardown.
    request.addfinalizer(md.terminate)

    return md
#
# TestMavGui
# ----------
class TestMavGui(object):
    # Check that fly time slider changes update the text box.
    def test_1(self, mavDialog):
        mavDialog.hsFlyTime.setValue(15)
        assert float(mavDialog.leFlyTime.text()) == 1.5

    # Check that fly time text box changes update the slider.
    def test_2(self, mavDialog, qtbot):
        mavDialog.leFlyTime.setText('2.5')
        # Bug: On Windows, qtbot.keyClicks(mavDialog.leFlyTime, '\n') crashes.
        qtbot.keyClick(mavDialog.leFlyTime, Qt.Key_Enter)
        assert mavDialog.hsFlyTime.value() == 25

    # Check that charge time slider changes update the text box.
    def test_3(self, mavDialog):
        mavDialog.hsChargeTime.setValue(35)
        assert float(mavDialog.leChargeTime.text()) == 3.5

    # Check that charge time text box changes update the slider.
    def test_4(self, myDialog, qtbot):
        myDialog.leChargeTime.setText('20')
        # Bug: On Windows, qtbot.keyClicks(myDialog.leFlyTime, '\n') crashes.
        qtbot.keyClick(myDialog.leChargeTime, Qt.Key_Enter)
        assert myDialog.hsChargeTime.value() == 20

    def test_4(self, mavDialog, qtbot):
        mavDialog.leChargeTime.setText('4.5')
        qtbot.keyClick(mavDialog.leChargeTime, Qt.Key_Enter)
        assert mavDialog.hsChargeTime.value() == 45

    # Check that invalid strings aren't allowed in the fly time edit boxe.
    def test_5(self, mavDialog, qtbot):
        mavDialog.leFlyTime.setText('5.5')
        qtbot.keyClicks(mavDialog.leFlyTime, 'hello')
        assert mavDialog.leFlyTime.text() == '5.5'

        # Must clear the text before trying to type more text.
        mavDialog.leFlyTime.setText('')
        qtbot.keyClicks(mavDialog.leFlyTime, '999')
        assert float(mavDialog.leFlyTime.text()) == 9.0

    # Check that invalid strings aren't allowed in the edit boxes.
    def test_6(self, mavDialog, qtbot):
        mavDialog.leChargeTime.setText('6.5')
        qtbot.keyClicks(mavDialog.leChargeTime, 'hello')
        assert mavDialog.leChargeTime.text() == '6.5'

        # Must clear the text before trying to type more text.
        mavDialog.leChargeTime.setText('')
        qtbot.keyClicks(mavDialog.leChargeTime, '999')
        assert float(mavDialog.leChargeTime.text()) == 9.0
#
# TestMavGui1
# -----------
class TestMavGui1(object):
    # Check that the GUI emits signals to the MAVs.
    def test_1(self, mavDialog, qtbot):
        for index in range(4):
            self.helpTest_1(mavDialog, qtbot, index)

    # A helper function to test a given MAV index.
    def helpTest_1(self, mavDialog, qtbot, index):
        mavDialog.cbSelectedMav.setCurrentIndex(index)
        with qtbot.waitSignal(mavDialog._chargingStation._mav[index].updateFlyTimeSec,
                              raising=True):
            mavDialog.hsFlyTime.setValue(mavDialog.hsFlyTime.value() + 1)

        with qtbot.waitSignal(mavDialog._chargingStation._mav[index].updateChargeTimeSec,
                              raising=True):
            mavDialog.hsChargeTime.setValue(mavDialog.hsChargeTime.value() + 1)

    # Test that slider values stay consistent.
    def test_2(self, mavDialog, qtbot):
        # Check initial values set by mavDialog fixture.
        assert mavDialog.hsFlyTime.value() == 5
        assert mavDialog.hsChargeTime.value() == 15

        # Set some new values.
        mavDialog.hsFlyTime.setValue(15)
        mavDialog.hsChargeTime.setValue(25)

        # Check and set values on another MAV.
        mavDialog.cbSelectedMav.setCurrentIndex(1)
        assert mavDialog.hsFlyTime.value() == 5
        assert mavDialog.hsChargeTime.value() == 15
        mavDialog.hsFlyTime.setValue(35)
        mavDialog.hsChargeTime.setValue(45)

        # Check previous values.
        mavDialog.cbSelectedMav.setCurrentIndex(0)
        assert mavDialog.hsFlyTime.value() == 15
        assert mavDialog.hsChargeTime.value() == 25

    # Test that updateMavState emissions update the GUI.
    def test_3(self, mavDialog, qtbot):
        for index in range(4):
            self.helpTest_3(mavDialog, qtbot)

    def helpTest_3(self, mavDialog, qtbot):
        index = 0
        mavDialog.updateMavState.emit(index, _MAV_STATES.Charging)
        assert mavDialog.mavStatus[index].rbCharging.isChecked()

        mavDialog.updateMavState.emit(index, _MAV_STATES.Waiting)
        assert mavDialog.mavStatus[index].rbWaiting.isChecked()

        mavDialog.updateMavState.emit(index, _MAV_STATES.Flying)
        assert mavDialog.mavStatus[index].rbFlying.isChecked()
        
        
