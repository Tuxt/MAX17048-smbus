=====
Usage
=====

Basic Usage
===========

Getting started with the MAX17048 is straightforward:

.. code-block:: python

   from max1704x_smbus import MAX17048

   sensor = MAX17048()
   print(f"Battery: {sensor.cell_voltage}V ({sensor.cell_percent}%)")

Typical Workflow
================

1. **Initialize the sensor** with your I2C bus configuration
2. **Configure alerts** if you need threshold notifications
3. **Read battery status** using the core properties
4. **Handle alert flags** when thresholds are exceeded

Example: Battery Monitoring Application
---------------------------------------

.. code-block:: python

   from max1704x_smbus import MAX17048
   import time

   sensor = MAX17048()
   
   # Configure low battery alert
   sensor.alert_soc_low_threshold = 10  # Alert at 10%
   
   while True:
       voltage = sensor.cell_voltage
       percent = sensor.cell_percent
       
       print(f"Battery: {voltage}V ({percent}%)")
       
       if sensor.alert_soc_low_flag:
           print("⚠️ Low battery!")
           sensor.alert_soc_low_flag_clear()
       
       time.sleep(5)
