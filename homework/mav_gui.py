# .. -*- coding: utf-8 -*-
#
# **********************************************************
# mav_gui.py - MAV recharging with a GUI, implemented in Qt.
# **********************************************************
#
# Imports
# =======
# Library
# -------
import sys
from os.path import dirname, join
from time import sleep
#
# Third-party
# -----------
# Use "Pythonic" (and PyQt5-compatible) `glue classes <http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html>`_.
# This must be done before importing from PyQt4.
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

from PyQt4.QtGui import QApplication, QDialog, QIntValidator, QDoubleValidator,QComboBox
from PyQt4.QtGui import QApplication, QDialog, QDoubleValidator
from PyQt4.QtGui import QGroupBox, QRadioButton, QVBoxLayout, QHBoxLayout
from PyQt4.QtCore import QTimer, QThread, QObject, pyqtSignal, pyqtSlot
from PyQt4 import uic
#
# Core code
# =========
# Overall flow between the Mav_ instances and the ChargingStation_:
#
# 1. ChargingStation_ constructs numMavs_, emitting the startMissions_ singal on each one.
# 2. Each MAV will emit a requestCharge_ signal to the ChargingStation_.
# 3. When both electrodes are available, the ChargingStation_ will emit an ownsElectrodes_ signal to that MAV.
# 4. The MAV charges. When done, it emits a finishedCharge_ signal to the ChargingStation_.
#
# Overall flow between the MavDialog_ and the Mav_ instances:
#
# * Changes to the fly time or charge time slider cause emission an updateFlyTimeSec_ or updateChargeTimeSec_ signal to the appropriate Mav_, based on the currently select Mav_ in the combo box.
# * Changes to Mav_ state cause emission of an updateMavState_ signal.
# * When the MavDialog_ is closed, it should terminate ChargingStation_, which should end the Mav_ threads.
#
# Enum
# ----
# A simple enumerate I like, taken from one of the snippet on `stackoverflow
# <http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python>`_.
# What I want: a set of unique identifiers that will be named nicely,
# rather than printed as a number. Really, just a way to create a class whose
# members contain a string representation of their name. Perhaps the best
# solution is `enum34 <https://pypi.python.org/pypi/enum34>`_, based on `PEP
# 0435 <https://www.python.org/dev/peps/pep-0435/>`_, but I don't want an extra
# dependency just for this.
class Enum(frozenset):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
#
# MAV_STATES
# ----------
_MAV_STATES = Enum( ('Flying', 'Waiting', 'Charging') )
#
# DummyWorker
# -----------
# An example of the use of threading. To use this:
#
# 1. Create a thread.
# 2. Create a worker, then move it to the thread.
# 3. Connect the worker's signal to the worker's routine to run.
# 4. Emit the signal to run the worker's routine.
class DummyWorker(QObject):
    # Define a signal used to invoke when_run.
    run = pyqtSignal(float)

    def __init__(self, parent):
        # First, let the QDialog initialize itself.
        super(DummyWorker, self).__init__()
        self.parent = parent

        # Prepare ``when_run`` to run in the parent's thread.
        self.moveToThread(self.parent._thread)
        self.run.connect(self.when_run)

    @pyqtSlot(float)
    def when_run(self, time_sec):
        print("sleeping for {} seconds.".format(time_sec))
        sleep(time_sec)
        self.parent.hsChargeTime.setValue(50)
#
# MavWorker
# ---------
# This object simulates a single MAV.
class MavWorker(QObject):
    # This causes the simulation to begin.
    run = pyqtSignal()

    def __init__(self,
      # The MyDialog which contains the GUI.
      parent,
      # The index of this MAV, for use in updating the GUI.
      index):

        self._parent = parent
        self._index = index

    # Fly a series of missions.
    def fly_mission(self):
        self._parent.update_state()
        sleep(self._fly_time_sec)

        self._state = _MAV_STATES.Waiting
        with self._left_electrode, self._right_electrode:
            self._state = _MAV_STATES.Charging
            sleep(self._charge_time_sec)
        self.run.emit()
#
# SingleMavWidget
# ---------------
# A helper class to organize each MAV's status.
class SingleMavWidget(object):
    pass
#
# UncheckableRadioButton
# ----------------------
# A helper class to create an uncheckable radio button.
class UncheckableRadioButton(QRadioButton):
    def __init__(self, *args, **kwargs):
        super(UncheckableRadioButton, self).__init__(*args, **kwargs)
        self.setCheckable(False)
#
# Mav
# ---
# A class which simulates a single MAV. This should be run in a separate thread by the MyDialog class.
class Mav(QObject):
    # .. _startMissions:
    #
    # This signal tells the class to start flying missions.
    startMissions = pyqtSignal()

    # .. _updateFlyTimeSec:
    #
    # This signal updates the flyTimeSec for the MAV.
    updateFlyTimeSec = pyqtSignal(float)

    # .. _updateChargeTimeSec:
    #
    # This signal updates the chargeTimeSec for this MAV.
    updateChargeTimeSec = pyqtSignal(float)

    # .. _ownsElectrodes:
    #
    # This signal tells the MAV that it has exclusive access to both electrodes in order to charge           itself.
    ownsElectrodes = pyqtSignal()

    def __init__(self,
      # .. _flyTimeSec:
      #
      # Time spent flying on a mission, in seconds.
      flyTimeSec,
      # .. _chargeTimeSec:
      #
      # Time spent charging, in seconds.
      chargeTimeSec,
      # See mavIndex_.
      mavIndex,
      # The thread this object should be moved to.
      thread_,
      # See requestCharge_.
      requestCharge,
      # See finishedCharge_.
      finishedCharge):

        super(Mav, self).__init__()
        
        def _on_updateFlyTimeSec(self,value):
            self.flyTimeSec = value
            
        def _on_updateChargeTimeSec(self,value):
            self.chargeTimeSec = value


#
# MavDialog
# ---------
# A dialog box to operate the MAV GUI.
class MavDialog(QDialog):
    # .. _updateMavState:
    #
    # This signal, sent by a MAV, informs the GUI of the MAV's current state. It simply invokes _on_updateMavState.
    updateMavState = pyqtSignal(
      # See mavIndex_.
      int,
      # See MAV_STATES_.
      object)

    def __init__(self,
      # .. _numMavs:
      #
      # The number of MAVs in the simulation.
      numMavs,
      # See _flyTimeSec.
      flyTimeSec,
      # See _chargeTimeSec.
      chargeTimeSec):

        # First, let the QDialog initialize itself.
        super(MavDialog, self).__init__()

        # Create a ChargingStation to manage the MAVs.
        self._chargingStation = ChargingStation(self, numMavs, flyTimeSec,
                                                chargeTimeSec)

        # `Load <http://pyqt.sourceforge.net/Docs/PyQt4/designer.html#PyQt4.uic.loadUi>`_
        # in our UI. The secord parameter lods the resulting UI directly into
        # this class.
        uic.loadUi(join(dirname(__file__), 'mav_gui.ui'), self)

        # Only allow numbers between 0 and 99 for the line edits.
        flyTimeValidator = QDoubleValidator(0, 9.9, 1, self)
        flyTimeValidator.setNotation(0)

        flyTimeValidator = QDoubleValidator(0.0, 9.9, 1, self)
        flyTimeValidator.setNotation(QDoubleValidator.StandardNotation)
        self.leFlyTime.setValidator(flyTimeValidator)
        chargeTimeValidator = QDoubleValidator(0.0, 9.9, 1, self)
        chargeTimeValidator.setNotation(QDoubleValidator.StandardNotation)
        self.leChargeTime.setValidator(chargeTimeValidator)

        chargeTimeValidator = QDoubleValidator( 0, 9.9, 1, self)
        chargeTimeValidator.setNotation(0)
        self.leChargeTime.setValidator(chargeTimeValidator)
        
        # Combo box options
        self.cbSelectedMav.addItem('MAV 1')
        self.cbSelectedMav.addItem('MAV 2')
        self.cbSelectedMav.addItem('MAV 3')
        self.cbSelectedMav.addItem('MAV 4')

        # Example: create a separate thread
        self._thread = QThread(self)
        #self._thread.start()
        # Create a worker.
        self._worker = DummyWorker(self)

        # Timer examples
        # ^^^^^^^^^^^^^^
        # A single-shot timer. It can't be canceled.
        QTimer.singleShot(1500, self._onTimeout)
        # Another single-shot timer. Because it has a name, it can be canceled.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._onTimeout)
        self._timer.setSingleShot(True)
        self._timer.start(3000)
        
        # Set the initial value of the sliders
        self.hsFlyTime.setValue(int(float(flyTimeSec)*10))
        self.hsChargeTime.setValue(int(float(chargeTimeSec)*10))

        # Add in status info GUI for numMavs MAVs.
        hl = QHBoxLayout()
        self.wMavStatus.setLayout(hl)
        assert numMavs > 0
        self.numMavs = numMavs
        self.mavStatus = []
        self.electrodeStatus = []
        self._chargeTimeSec = [chargeTimeSec]*self.numMavs
        self._flyTimeSec = [flyTimeSec]*self.numMavs
        for index in range(self.numMavs):
            e = UncheckableRadioButton(self)
            self.electrodeStatus.append(e)
            hl.addWidget(e)

            # Add in a group box.
            smw = SingleMavWidget()
            mavName = 'MAV {}'.format(index + 1)
            smw.gb = QGroupBox(mavName, self.wMavStatus)
            vl = QVBoxLayout()
            smw.gb.setLayout(vl)
            smw.rbFlying = UncheckableRadioButton('Flying', smw.gb)
            smw.rbWaiting = UncheckableRadioButton('Waiting', smw.gb)
            smw.rbCharging = UncheckableRadioButton('Charging', smw.gb)
            vl.addWidget(smw.rbFlying)
            vl.addWidget(smw.rbWaiting)
            vl.addWidget(smw.rbCharging)
            self.mavStatus.append(smw)
            hl.addWidget(smw.gb)

            # Update the combo box.
            self.cbSelectedMav.insertItem(index, mavName)

        # Update GUI with parameters.
        self.on_cbSelectedMav_currentIndexChanged(0)

        self.updateMavState.connect(self._on_updateMavState)

    # .. _on_updateMavState:
    #
    # A standardized way for MAVs to update their status. Should be invoked
    @pyqtSlot(int, object)
    def _on_updateMavState(self,
      # See mavIndex_.
      mavIndex,
      # See MAV_STATES_.
      mavState):

        if mavIndex == 0:
            pass
        elif mavIndex == 1:
            pass
        elif mavIndex == 2:
            pass
        elif mavIndex == 3:
            pass
        pass
    
        # Make only one of the radio buttons checkable, so that the user can't check a different one.
        ms = self.mavStatus[mavIndex]
        if mavState == _MAV_STATES.Waiting:
            ms.rbWaiting.setCheckable(True)
            ms.rbFlying.setCheckable(False)
            ms.rbCharging.setCheckable(False)
            ms.rbWaiting.setChecked(True)
        elif mavState == _MAV_STATES.Flying:
            ms.rbWaiting.setCheckable(False)
            ms.rbFlying.setCheckable(True)
            ms.rbCharging.setCheckable(False)
            self.mavStatus[mavIndex].rbFlying.setChecked(True)
        elif mavState == _MAV_STATES.Charging:
            ms.rbWaiting.setCheckable(False)
            ms.rbFlying.setCheckable(False)
            ms.rbCharging.setCheckable(True)
            self.mavStatus[mavIndex].rbCharging.setChecked(True)
        else:
            assert False

    @pyqtSlot()
    def _onTimeout(self):
        self.hsFlyTime.setValue(50)

    @pyqtSlot(int)
    def on_hsFlyTime_valueChanged(self, value):

        self.leFlyTime.setText(str(float(value)/10))
        Mav.updateChargeTimeSec(float(value)/10)

        flyTimeSec = value/10.0
        self._chargingStation._mav[self.cbSelectedMav.currentIndex()].updateFlyTimeSec.emit(flyTimeSec)
        self.leFlyTime.setText(str(flyTimeSec))
        self._flyTimeSec[self.cbSelectedMav.currentIndex()] = flyTimeSec

        self._worker.run.emit(1.5)

    @pyqtSlot()
    def on_leFlyTime_editingFinished(self):

        self.hsFlyTime.setValue(int(float(self.leFlyTime.text())*10))

    @pyqtSlot()
    def on_leChargeTime_editingFinished(self):
        self.hsChargeTime.setValue(int(float(self.leChargeTime.text())*10))

    @pyqtSlot(int)
    def on_hsChargeTime_valueChanged(self, value):
        self.leChargeTime.setText(str(float(value)/10))
        Mav.updateChargeTimeSec(float(value)/10)
        self._worker.run.emit(1.5)

        self.hsFlyTime.setValue(float(self.leFlyTime.text())*10.0)

    @pyqtSlot(int)
    def on_hsChargeTime_valueChanged(self, value):
        chargeTimeSec = value/10.0
        self._chargingStation._mav[self.cbSelectedMav.currentIndex()].updateChargeTimeSec.emit(chargeTimeSec)
        self.leChargeTime.setText(str(chargeTimeSec))
        self._chargeTimeSec[self.cbSelectedMav.currentIndex()] = chargeTimeSec
        self._worker.run.emit(1.5)

    @pyqtSlot()
    def on_leChargeTime_editingFinished(self):
        self.hsChargeTime.setValue(float(self.leChargeTime.text())*10.0)

    @pyqtSlot(int)
    def on_cbSelectedMav_currentIndexChanged(self, index):
        self.hsChargeTime.setValue(self._chargeTimeSec[index]*10)
        self.hsFlyTime.setValue(self._flyTimeSec[index]*10)


    # Free all resources used by this class.
    def terminate(self):
        self._thread.quit()
        self._thread.wait()
        self._timer.stop()
        
#
# ChargingStation
# ---------------
# This object manages MAV construction and charging.
class ChargingStation(QObject):
    # .. _requestCharge:
    #
    # This signal, sent by a MAV, requests exclusive access to that MAV's charging electrodes.
    requestCharge = pyqtSignal(
      # .. _mavIndex:
      #
      # The index of the requesting MAV, from 0 to numMavs - 1.
      int)

    # .. _finishedCharge:
    #
    # This signal, sent by a MAV, releases exclusive access to that MAV's charging electrodes.
    finishedCharge = pyqtSignal(
      # See mavIndex_.
      int)
    chargeTimeSec = pyqtSignal()
    
    def __init__(self,
      # The parent of this object.
      parent,
      # See _numMavs.
      numMavs,
      # See _flyTimeSec.
      flyTimeSec,
      # See _chargeTimeSec.
      chargeTimeSec):

        super(ChargingStation, self).__init__(parent)

        self._mav = []
        self._thread = []
        for index in range(numMavs):
            self._thread.append(QThread(self))
            self._mav.append(Mav(flyTimeSec, chargeTimeSec, index, self._thread[-1],
                                 self.requestCharge, self.finishedCharge))
#
# Main
# ====
def main():
    # Initialize the program. A `QApplication <http://doc.qt.io/qt-4.8/qapplication.html>`_
    # must always be created.
    qa = QApplication(sys.argv)
    # Construct the UI: either a `QDialog <http://doc.qt.io/qt-4.8/qdialog.html>`_
    # or a `QMainWindow <http://doc.qt.io/qt-4.8/qmainwindow.html>`_.
    md = MavDialog(int(sys.argv[1]), 0.5, 1.5)
    # The UI is hidden while it's being set up. Now that it's ready, it must be
    # manually shown.
    md.show()

    # Main loop.
    qa.exec_()

    # Terminate.
    md.terminate()

if __name__ == '__main__':
    main()
