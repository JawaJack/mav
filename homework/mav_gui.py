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
    # This signal tells the MAV that it has exclusive access to both electrodes in order to charge itself.
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
        self.leFlyTime.setValidator(flyTimeValidator)

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
        self._thread.start()
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
    

    
    @pyqtSlot()
    def _onTimeout(self):
        self.hsFlyTime.setValue(50)

    @pyqtSlot(int)
    def on_hsFlyTime_valueChanged(self, value):
        self.leFlyTime.setText(str(float(value)/10))
        Mav.updateChargeTimeSec(float(value)/10)
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
    md = MavDialog(4, 0.5, 1.5)
    # The UI is hidden while it's being set up. Now that it's ready, it must be
    # manually shown.
    md.show()

    # Main loop.
    qa.exec_()

    # Terminate.
    md.terminate()

if __name__ == '__main__':
    main()
