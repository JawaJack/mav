@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Welcome to MAV_control documentation!
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

Source code
===========
Tutorial
--------
Edit these files to interactively learn Python.

.. toctree::
   :maxdepth: 2

   tutorial/Python_tutorial.py
   tutorial/threading_demo.py

Homework
--------
These serve as the starting point for homework assignments.

.. toctree::
   :maxdepth: 2

   homework/pick_val.py
   homework/mav_recharging.py
   homework/mav_recharging_test.py
   homework/mav_gui.py
   homework/mav_gui_test.py
   homework/unit_test_grader.py

MAV control
-----------
These are files that you'll edit to make your MAV do neat things.

.. toctree::
   :maxdepth: 2

   src/mav_control.py

* :download:`src/mav_control.ui` -- Defines the GUI layout.
  Use the Qt Designer to modify this.

Library
-------
These files are used by ``mav_control.py`` above to
interface with the drone.

.. toctree::
   :maxdepth: 2

   src/mav_control_base.py
   src/webcam_find_car.py
   src/drone_controller.py
   src/drone_status.py

ROS
===
These files tell ROS about this program.

* :download:`CMakeLists.txt` -- How to build this ROS
  package.
* :download:`package.xml` -- The contents of this ROS
  package.
* :download:`launch/basic.launch` -- Run the MAV control
  program and the AR Drone drivers.

Scripts
-------
These scripts simplify common tasks.

.. toctree::
   :maxdepth: 2

   scripts/drone_install.sh
   scripts/rosrun_mavcontrol.sh

Documentation
=============
These files help generate this documentation.

.. toctree::
   :maxdepth: 2

   conf.py
   CodeChat.css

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
