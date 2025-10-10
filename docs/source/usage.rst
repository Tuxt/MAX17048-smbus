=====
Usage
=====

A simple example of how to use the library:

.. code-block:: python

    from max1704x_smbus import MAX17048

    sensor = MAX17048()
    print("Cell voltage:", sensor.cell_voltage, "V")
