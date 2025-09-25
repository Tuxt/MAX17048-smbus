"""
Core driver for the MAX17048 fuel gauge.

This module defines the :class:`MAX17048` driver class, along with
constants for interpreting alert flags from the device.
"""

from .i2c_device import I2CDevice
from .register import (
    USED_BYTES_BOTH,
    USED_BYTES_LSB,
    USED_BYTES_MSB,
    RegisterField,
    ROBit,
    RORegister,
    RWBit,
    RWRegister,
)

MAX1704X_I2CADDR_DEFAULT = 0x36

_MAX1704X_VCELL_REG = 0x02
_MAX1704X_SOC_REG = 0x04
_MAX1704X_MODE_REG = 0x06
_MAX1704X_VERSION_REG = 0x08
_MAX1704X_HIBRT_REG = 0x0A
_MAX1704X_CONFIG_REG = 0x0C
_MAX1704X_VALERT_REG = 0x14
_MAX1704X_CRATE_REG = 0x16
_MAX1704X_VRESET_ID_REG = 0x18
_MAX1704X_STATUS_REG = 0x1A
_MAX1704X_CMD_REG = 0xFE

ALERTFLAG_SOC_CHANGE = 0x20
ALERTFLAG_SOC_LOW = 0x10
ALERTFLAG_VOLTAGE_RESET = 0x08
ALERTFLAG_VOLTAGE_LOW = 0x04
ALERTFLAG_VOLTAGE_HIGH = 0x02
ALERTFLAG_RESET_INDICATOR = 0x01


# TODO: Reorder attributes and methods by functional groups
# TODO: Add See Also sections to group related hibernation and alert properties
# TODO: Review/Rename attribute/property naming for consistency
class MAX17048:
    """
    Interface for the MAX17048 fuel gauge.

    High-level interface to the Maxim MAX17048/MAX17049 battery fuel gauge
    IC. The class exposes commonly used readings (voltage, SOC, charge rate),
    alert configuration and handling, and hibernation controls via an
    attribute-like API.

    Attributes
    ----------
    cell_voltage : float
        Current cell voltage in volts (read-only).
    cell_percent : float
        State-of-charge (SOC) as a percentage (read-only).
    hibernating : bool
        ``1`` when the device is currently in hibernation, ``0`` otherwise. (read-only).
    enable_sleep : bool
        Enable or disable the device sleep mode (read/write).
    chip_version : int
        Raw chip version register (read-only).
    hibernation_threshold : float
        Threshold (in %/hour) below which the device may enter hibernation
        (read-write).
    activity_threshold : float
        Voltage change threshold to exit hibernation mode (read-write).
    rcomp : int
        RCOMP configuration to tune compensation for different battery types
        (read-write).
    sleep : bool
        Forces the IC in or out of sleep mode (if `enable_sleep`) (read-write)
    active_alert : bool
        ``True`` if any alert is currently active, ``False`` otherwise
        (read-only).
    voltage_alert_min : float
        Lower voltage threshold that triggers a voltage alert (read-write).
    charge_rate : float
        Estimated charge/discharge rate in percent per hour (read-only).
    reset_voltage : float
        Voltage threshold used to detect battery removal / reinsertion
        (read-write).
    comparator_disabled : bool
        Disable the analog comparator while in hibernation (read-write).
    chip_id : int
        Chip ID register (read-only).
    alert_reason : int
        Bitmask of currently active alert causes (read-only).
    reset_indicator : bool
        Reset alert flag (read-only).
    voltage_reset_alert : bool
        Voltage-reset alert flag (read-only).
    enable_voltage_reset_alert : bool
        Enable/disable voltage reset alerts (read-write).
    alert_soc_change_enable : bool
        Enable/disable SOC change alerts (≥1% variation) (read-write).
    alert_soc_change_flag : bool
        SOC-change alert flag (read-only).
    alert_soc_low_threshold : int
        SOC percentage threshold that triggers a low-SOC alert (read-write).
    alert_soc_low_flag : bool
        SOC-low alert flag (read-only).
    alert_voltage_high_threshold : float
        Upper voltage threshold that triggers a voltage alert (read-write).
    alert_voltage_high_flag : bool
        Voltage-high alert flag (read-only).
    alert_voltage_low_flag : bool
        Voltage-low alert flag (read-only).

    Methods
    -------
    reset() -> None
        Issue a soft reset to the device.
    clear_alert() -> None
        Clear the global alert flag (and deassert the ALRT pin).
    clear_voltage_reset_alert() -> None
        Clear the voltage reset (VR) flag in the ``STATUS`` register.
    clear_reset_indicator() -> None
        Clear the reset indicator (RI) flag in the ``STATUS`` register.
    quick_start() -> None
        Trigger a quick-start estimation of OCV/SOC.
    hibernate() -> None
        Force the device into hibernation mode immediately.
    wake() -> None
        Wake the device from hibernation mode immediately.
    alert_soc_change_flag_clear() -> None
        Clear the SOC change (SC) flag in the ``STATUS`` register.
    alert_soc_low_flag_clear() -> None
        Clear the SOC low (HD) flag in the ``STATUS`` register.
    alert_voltage_high_flag_clear() -> None
        Clear the voltage high (VH) flag in the ``STATUS`` register.
    alert_voltage_low_flag_clear() -> None
        Clear the voltage low (VL) flag in the ``STATUS`` register.
    """

    # [0x02] VCELL      RO
    _cell_voltage = RORegister(_MAX1704X_VCELL_REG, used_bytes=USED_BYTES_BOTH)
    # [0x04] SOC        RO
    _cell_soc = RORegister(_MAX1704X_SOC_REG, used_bytes=USED_BYTES_BOTH)
    # [0x06] MODE       WO  Default: 0x0000
    _hibernating = ROBit(_MAX1704X_MODE_REG, bit=4)
    _enable_sleep = RWBit(_MAX1704X_MODE_REG, bit=5)
    _quick_start = RWBit(_MAX1704X_MODE_REG, bit=6)
    # [0x08] VERSION    RO  Default: 0x001_
    chip_version = RORegister(_MAX1704X_VERSION_REG, used_bytes=USED_BYTES_BOTH)
    # [0x0A] HIBRT      RW  Default: 0x8030
    _hibrt_actthr = RWRegister(_MAX1704X_HIBRT_REG, used_bytes=USED_BYTES_LSB, independent_bytes=True)
    _hibrt_hibthr = RWRegister(_MAX1704X_HIBRT_REG, used_bytes=USED_BYTES_MSB, independent_bytes=True)
    # [0x0C] CONFIG     RW  Default: 0x971C
    rcomp = RWRegister(_MAX1704X_CONFIG_REG, used_bytes=USED_BYTES_MSB)
    _sleep = RWBit(_MAX1704X_CONFIG_REG, bit=7)
    _alsc = RWBit(_MAX1704X_CONFIG_REG, bit=6)
    _alert_status = RWBit(_MAX1704X_CONFIG_REG, bit=5)
    _athd = RegisterField(_MAX1704X_CONFIG_REG, num_bits=5, lowest_bit=0)
    # [0x14] VALRT      RW  Default: 0x00FF
    _valrt_min = RWRegister(_MAX1704X_VALERT_REG, used_bytes=USED_BYTES_MSB, independent_bytes=True)
    _valrt_max = RWRegister(_MAX1704X_VALERT_REG, used_bytes=USED_BYTES_LSB, independent_bytes=True)
    # [0x16] CRATE      RO
    _cell_crate = RORegister(_MAX1704X_CRATE_REG, used_bytes=USED_BYTES_BOTH, signed=True)
    # [0x18] VRESET/ID  RW  Default: 0x96__
    _reset_voltage = RegisterField(_MAX1704X_VRESET_ID_REG, num_bits=7, lowest_bit=9, independent_bytes=True)
    _comparator_disabled = RWBit(_MAX1704X_VRESET_ID_REG, bit=8, independent_bytes=True)
    chip_id = RORegister(_MAX1704X_VRESET_ID_REG, used_bytes=USED_BYTES_LSB, independent_bytes=True)
    # [0x1A] STATUS     RW  Default: 0x01__
    _status = RORegister(_MAX1704X_STATUS_REG, used_bytes=USED_BYTES_MSB, independent_bytes=True)
    _reset_indicator = RWBit(_MAX1704X_STATUS_REG, bit=8, independent_bytes=True)
    _vh = RWBit(_MAX1704X_STATUS_REG, bit=9, independent_bytes=True)
    _vl = RWBit(_MAX1704X_STATUS_REG, bit=10, independent_bytes=True)
    _voltage_reset_alert = RWBit(_MAX1704X_STATUS_REG, bit=11, independent_bytes=True)
    _hd = RWBit(_MAX1704X_STATUS_REG, bit=12, independent_bytes=True)
    _sc = RWBit(_MAX1704X_STATUS_REG, bit=13, independent_bytes=True)
    _envr = RWBit(_MAX1704X_STATUS_REG, bit=14, independent_bytes=True)
    # [0xFE] CMD        RW  Default: 0xFFFF
    _cmd = RWRegister(_MAX1704X_CMD_REG, used_bytes=USED_BYTES_BOTH)

    def __init__(self, i2c_bus: int = 1, address: int = MAX1704X_I2CADDR_DEFAULT) -> None:
        """
        Initialize a MAX17048/MAX17049 fuel gauge instance.

        Establishes communication with the device over the specified I²C bus and
        verifies that a supported chip is present at the given address.

        Parameters
        ----------
        i2c_bus : int, optional
            I²C bus number where the device is connected. Default is ``1``.
        address : int, optional
            I²C address of the device. Default is
            ``MAX1704X_I2CADDR_DEFAULT``.

        Raises
        ------
        RuntimeError
            If the device does not respond with a valid chip version,
            indicating either incorrect wiring or absence of a MAX17048/MAX17049.
        """
        self.i2c_device = I2CDevice(i2c_bus, address)

        if self.chip_version & 0xFFF0 != 0x0010:
            raise RuntimeError("Failed to find MAX1704X - check your wiring!")

        self.reset()
        self.enable_sleep = False
        self.sleep = False

    def reset(self) -> None:
        """
        Perform a soft reset of the MAX17048/MAX17049 device.

        Sends the reset command and clears the reset alert flag.
        This operation performs a soft reset of the device, restarting
        its internal fuel gauge logic without physically disconnecting
        the power supply.

        Raises
        ------
        :py:exc:`RuntimeError`
            If the reset command does not succeed or if clearing the
            reset alert fails.
        """
        try:
            self._cmd = 0x5400
        except OSError:
            # NACKed, which is CORRECT
            pass
        else:
            raise RuntimeError("Reset did not succeed")

        try:
            self.clear_reset_indicator()  # Clean up RI alert
        except OSError as e:
            raise RuntimeError("Clearing reset alert did not succeed") from e

    @property
    def cell_voltage(self) -> float:
        """
        Battery cell voltage.

        Returns
        -------
        float
            Cell voltage in volts.
        """
        return self._cell_voltage * 78.125 / 1_000_000

    @property
    def cell_percent(self) -> float:
        """
        Battery state of charge (SOC).

        Returns
        -------
        float
            State of charge as a percentage of full capacity (0-100).
        """
        return self._cell_soc / 256.0

    @property
    def charge_rate(self) -> float:
        """
        Battery charge or discharge rate.

        Returns
        -------
        float
            Rate of change in percent per hour. Positive values indicate charging,
            negative values indicate discharging.
        """
        return self._cell_crate * 0.208

    @property
    def reset_voltage(self) -> float:
        """
        Reset threshold voltage.

        Cell voltage threshold at which the device considers a battery removal
        or reinsertion.

        Returns
        -------
        float
            Threshold voltage in volts, between 0 and 5.1 V.

        Raises
        ------
        :py:exc:`ValueError`
            If a value outside the valid range is assigned.
        """
        return self._reset_voltage * 0.04  # 40 mV steps

    @reset_voltage.setter
    def reset_voltage(self, vreset: float) -> None:
        if not 0 <= vreset <= (127 * 0.04):
            raise ValueError("Reset voltage must be between 0 and 5.1V")
        self._reset_voltage = int(vreset / 0.04)  # 40 mV steps

    @property
    def comparator_disabled(self) -> bool:
        """
        Control whether the analog comparator for ``VRESET`` is disabled.

        When set to ``True``, the analog comparator (used to detect battery
        removal and reinsertion) is disabled during hibernate mode, reducing
        supply current by about 0.5 µA. When ``False``, the comparator
        remains enabled.

        Returns
        -------
        bool
            ``True`` if the comparator is disabled in hibernate mode,
            ``False`` if enabled.

        Notes
        -----
        Corresponds to the ``Dis`` bit in the ``VRESET/ID`` register.
        See the *VRESET* section of the datasheet for details on threshold
        adjustment and reset timing behavior.
        """
        return bool(self._comparator_disabled)

    @comparator_disabled.setter
    def comparator_disabled(self, disabled: bool) -> None:
        self._comparator_disabled = int(disabled)

    @property
    def voltage_alert_min(self) -> float:
        """
        Minimum voltage threshold for triggering a voltage alert.

        Returns
        -------
        float
            Lower-limit threshold in volts, between 0 and 5.1 V.

        Raises
        ------
        :py:exc:`ValueError`
            If a value outside the valid range is assigned.
        """
        return self._valrt_min * 0.02  # 20 mV steps

    @voltage_alert_min.setter
    def voltage_alert_min(self, valert_min: float) -> None:
        if not 0 <= valert_min <= (255 * 0.02):
            raise ValueError("Alert voltage must be between 0 and 5.1V")
        self._valrt_min = int(valert_min / 0.02)

    @property
    def voltage_reset_alert(self) -> bool:
        """
        Voltage reset flag.

        Indicates whether the cell voltage dropped below and subsequently
        risen above the :py:attr:`reset_voltage` threshold.

        Returns
        -------
        bool
            ``True`` if the cell voltage dropped below and then rose above the
            configured reset threshold, ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``VR`` bit in the ``STATUS`` register. This
        property is read-only. Use :py:meth:`clear_voltage_reset_alert`
        to clear the flag after handling the alert.

        See Also
        --------
        :py:attr:`reset_voltage`
        :py:meth:`clear_voltage_reset_alert`
        """
        return bool(self._voltage_reset_alert)

    def clear_voltage_reset_alert(self) -> None:
        """
        Clear the voltage reset flag.

        Clear the ``VR`` (voltage reset) flag in the ``STATUS`` register.

        See Also
        --------
        :py:attr:`voltage_reset_alert`
        """
        self._voltage_reset_alert = 0

    @property
    def active_alert(self) -> bool:
        """
        Indicate whether an alert condition is currently active.

        Returns
        -------
        bool
            ``True`` if an alert is active, ``False`` otherwise.

        """
        return bool(self._alert_status)

    def clear_alert(self) -> None:
        """
        Clear the global alert flag and deassert the ``ALRT`` pin.

        This operation resets the alert status in the configuration register and
        simultaneously releases the physical ``ALRT`` pin, until a new alert
        condition is triggered.
        """
        self._alert_status = 0

    @property
    def alert_reason(self) -> int:
        """
        6-bit bitmask of currently active alert causes.

        Returns
        -------
        int
            Mask of alert flasgs. Multiple causes may be set simultaneously.
            Individual causes can be checked against the module constants
            (e.g. ``ALERTFLAG_SOC_LOW``).

        See Also
        --------
        :py:const:`ALERTFLAG_SOC_CHANGE`
        :py:const:`ALERTFLAG_SOC_LOW`
        :py:const:`ALERTFLAG_VOLTAGE_RESET`
        :py:const:`ALERTFLAG_VOLTAGE_LOW`
        :py:const:`ALERTFLAG_VOLTAGE_HIGH`
        :py:const:`ALERTFLAG_RESET_INDICATOR`
        """
        return self._status & 0x3F

    @property
    def reset_indicator(self) -> bool:
        """
        Reset indicator flag.

        Indicates whether the device has recently powered up or reset and
        still requires configuration. A value of ``True`` means the IC is
        signaling that initialization is pending. ``False`` means the device
        has already been configured and the flag has been cleared.

        Returns
        -------
        bool
            ``True`` if the reset indicator (RI) flag is set,
            ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``RI`` bit in the ``STATUS`` register. This
        property is read-only. Use :py:meth:`clear_reset_indicator` to
        acknowledge and clear the flag.

        See Also
        --------
        :py:meth:`clear_reset_indicator`
        """
        return bool(self._reset_indicator)

    def clear_reset_indicator(self) -> None:
        """
        Clear the reset indicator flag.

        Acknowledges that the device has been configured after a reset or
        power-up event by clearing the ``RI`` bit in the ``STATUS`` register.

        Notes
        -----
        This method explicitly writes ``0`` to the ``RI`` flag. The bit is
        set automatically by the device after power-up or reset.

        See Also
        --------
        :py:attr:`reset_indicator`
        """
        self._reset_indicator = 0

    @property
    def enable_voltage_reset_alert(self) -> bool:
        """
        Enable or disable voltage reset alert.

        Returns
        -------
        bool
            ``True`` if voltage reset alert is enabled, ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``EnVr`` bit in the ``STATUS`` register
        (read/write).

        See Also
        --------
        :py:attr:`reset_voltage`
        :py:meth:`clear_voltage_reset_alert`
        """
        return bool(self._envr)

    @enable_voltage_reset_alert.setter
    def enable_voltage_reset_alert(self, enabled: bool) -> None:
        self._envr = int(enabled)

    def quick_start(self) -> None:
        """
        Trigger a quick-start estimation of OCV and SOC.

        Initiates a recalculation of open-circuit voltage (OCV) and
        state-of-charge (SOC) based on the instantaneous cell voltage.

        Notes
        -----
        This method sets the ``Quick-Start`` bit in the ``MODE`` register to
        trigger a recalculation. Use with caution; see the *Quick-Start* section
        of the datasheet for details.
        """
        self._quick_start = 1

    @property
    def enable_sleep(self) -> bool:
        """
        Enable or disable sleep mode.

        Returns
        -------
        bool
            ``True`` if sleep mode is enabled, ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``EnSleep`` bit in the ``MODE`` register
        (read/write).
        """
        return bool(self._enable_sleep)

    @enable_sleep.setter
    def enable_sleep(self, enabled: bool) -> None:
        self._enable_sleep = int(enabled)

    @property
    def sleep(self) -> bool:
        """
        Control whether the IC is forced into sleep mode.

        Writing ``True`` forces the device into sleep mode, and ``False``
        forces it to exit. This control is effective only if
        :py:attr:`enable_sleep` is enabled.

        Returns
        -------
        bool
            ``True`` if forcing the device into sleep mode, ``False`` if
            forcing exit.

        Notes
        -----
        Corresponds to the ``SLEEP`` bit in the ``CONFIG`` register.
        """
        return bool(self._sleep)

    @sleep.setter
    def sleep(self, sleep: bool) -> None:
        self._sleep = int(sleep)

    @property
    def hibernating(self) -> bool:
        """
        Whether the device is currently in hibernation.

        Read the device hibernation status. Returns ``True`` when the hardware
        reports it is in hibernation mode (the bit named ``HibStat`` in the
        device datasheet).

        Returns
        -------
        bool
            ``True`` if the device is in hibernation, ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``HibStat`` bit in the ``MODE`` register.
        This property is read-only. Use :py:meth:`hibernate` or :py:meth:`wake`
        to change the device state.

        See Also
        --------
        :py:meth:`hibernate`
        :py:meth:`wake`
        """
        return bool(self._hibernating)

    @property
    def activity_threshold(self) -> float:
        """
        Charge/Discharge rate threshold to exit hibernation.

        When the rate of change of the cell voltage exceeds this threshold,
        the device leaves hibernation.

        Returns
        -------
        float
            Threshold in volts, between 0 and 0.31875 V.

        Raises
        ------
        :py:exc:`ValueError`
            If a value outside the valid range is assigned.

        See Also
        --------
        :py:attr:`hibernating`
        :py:meth:`hibernation_threshold`
        :py:meth:`hibernate`
        :py:meth:`wake`
        """
        return self._hibrt_actthr * 0.00125  # 1.25 mV steps

    @activity_threshold.setter
    def activity_threshold(self, threshold_voltage: float) -> None:
        if not 0 <= threshold_voltage <= (255 * 0.00125):
            raise ValueError("Activity volage change must be between 0 and 0.31875 V")
        self._hibrt_actthr = int(threshold_voltage / 0.00125)  # 1.25 mV steps

    @property
    def hibernation_threshold(self) -> float:
        """
        Charge/Discharge rate threshold to enter hibernation.

        When the rate of change of the cell falls below this threshold,
        the device enters hibernation. This condition must be maintained
        for 6 minutes.

        Returns
        -------
        float
            Threshold in percent per hour, between 0 and 53%/h.

        Raises
        ------
        :py:exc:`ValueError`
            If a value outside the valid range is assigned.

        See Also
        --------
        :py:attr:`hibernating`
        :py:meth:`activity_threshold`
        :py:meth:`hibernate`
        :py:meth:`wake`
        """
        return self._hibrt_hibthr * 0.208  # 0.208%/hr steps

    @hibernation_threshold.setter
    def hibernation_threshold(self, threshold_percent: float) -> None:
        if not 0 <= threshold_percent <= (255 * 0.208):
            raise ValueError("Hibernation percent/hour change must be between 0 and 53%")
        self._hibrt_hibthr = int(threshold_percent / 0.208)  # 0.208%/hr steps

    def hibernate(self) -> None:
        """
        Enter hibernation mode immediately.

        This method forces the device into hibernation by setting both thresholds
        to their maximum values, regardless of the current charge/discharge rate
        or voltage change.

        See Also
        --------
        :py:attr:`hibernating`
        :py:meth:`wake`
        :py:meth:`activity_threshold`
        :py:meth:`hibernation_threshold`

        Notes
        -----
        This operation overwrites the hibernation thresholds. Calling
        :meth:`hibernate` followed by :meth:`wake` does not restore
        previous threshold values.
        """
        self._hibrt_hibthr = 0xFF
        self._hibrt_actthr = 0xFF

    def wake(self) -> None:
        """
        Exit hibernation mode immediately.

        This method forces the device out of hibernation by setting both thresholds
        to zero, regardless of the current charge/discharge rate or voltage change.

        See Also
        --------
        :py:attr:`hibernating`
        :py:meth:`hibernate`
        :py:meth:`activity_threshold`
        :py:meth:`hibernation_threshold`

        Notes
        -----
        This operation overwrites the hibernation thresholds. Calling
        :meth:`hibernate` followed by :meth:`wake` does not restore
        previous threshold values.
        """
        self._hibrt_hibthr = 0x00
        self._hibrt_actthr = 0x00

    # ALERTS
    # SoC Change
    @property
    def alert_soc_change_enable(self) -> bool:
        """
        Enable or disable the state-of-charge (SOC) change alert.

        When enabled, the device asserts an alert whenever the SOC changes
        by at least 1%.

        Returns
        -------
        bool
            ``True`` if the SOC change alert is enabled, ``False`` otherwise.
        """
        return bool(self._alsc)

    @alert_soc_change_enable.setter
    def alert_soc_change_enable(self, enabled: bool) -> None:
        self._alsc = int(enabled)

    @property
    def alert_soc_change_flag(self) -> bool:
        """
        SOC change flag.

        Indicates whether SOC has changed at least 1% (if enabled).

        Returns
        -------
        bool
            ``True`` if SOC changed at least 1%,
            ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``SC`` bit in the ``STATUS`` register. This
        property is read-only. Use :py:meth:`alert_soc_change_flag_clear`
        to clear the flag after handling the alert.

        See Also
        --------
        :py:attr:`alert_soc_change_enable`
        :py:meth:`alert_soc_change_flag_clear`
        """
        return bool(self._sc)

    def alert_soc_change_flag_clear(self) -> None:
        """
        Clear the SOC change flag.

        Clear the ``SC`` (SOC change) flag in the ``STATUS`` register.

        See Also
        --------
        :py:attr:`alert_soc_change_flag`
        """
        self._sc = 0

    # Low SoC
    @property
    def alert_soc_low_threshold(self) -> int:
        """
        Low-SOC alert threshold.

        Defines the state-of-charge (SOC) percentage below which the
        device asserts an alert condition.

        Returns
        -------
        int
            Threshold in percent, between 1 and 32%.

        Raises
        ------
        :py:exc:`ValueError`
            If a value outside the valid range is assigned.
        """
        return 32 - self._athd

    @alert_soc_low_threshold.setter
    def alert_soc_low_threshold(self, percent_alert_threshold: int) -> None:
        if not 0 < percent_alert_threshold <= 32:
            raise ValueError("SOC alert threshold must be between 1 and 32%")
        self._athd = 32 - percent_alert_threshold

    @property
    def alert_soc_low_flag(self) -> bool:
        """
        SOC low flag.

        Indicates whether SOC crosses the :py:attr:`alert_soc_low_threshold`.

        Returns
        -------
        bool
            ``True`` if SOC crossed the configured threshold,
            ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``HD`` bit in the ``STATUS`` register. This
        property is read-only. Use :py:meth:`alert_soc_low_flag_clear`
        to clear the flag after handling the alert.

        See Also
        --------
        :py:attr:`alert_soc_low_threshold`
        :py:meth:`alert_soc_low_flag_clear`
        """
        return bool(self._hd)

    def alert_soc_low_flag_clear(self) -> None:
        """
        Clear the SOC low flag.

        Clear the ``HD`` (SOC low) flag in the ``STATUS`` register.

        See Also
        --------
        :py:attr:`alert_soc_low_flag`
        """
        self._hd = 0

    # Voltage High
    @property
    def alert_voltage_high_threshold(self) -> float:
        """The upper-limit voltage for the voltage alert."""
        """
        Maximum voltage threshold for triggering a voltage alert.

        Returns
        -------
        float
            Upper-limit threshold in volts, between 0 and 5.1 V.
        
        Raises
        ------
        :py:exc:`ValueError`
            If a value outside the valid range is assigned.
        """
        return self._valrt_max * 0.02  # 20 mV steps

    @alert_voltage_high_threshold.setter
    def alert_voltage_high_threshold(self, valert_max: float) -> None:
        if not 0 <= valert_max <= (255 * 0.02):
            raise ValueError("Alert voltage must be between 0 and 5.1V")
        self._valrt_max = int(valert_max / 0.02)

    @property
    def alert_voltage_high_flag(self) -> bool:
        """
        Voltage high flag.

        Indicates whether the high voltage alert is active. ``True`` means the
        cell voltage has exceeded the threshold set in :py:attr:`alert_voltage_high_threshold`.

        Returns
        -------
        bool
            ``True`` if the cell voltage has exceeded the threshold,
            ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``VH`` bit in the ``STATUS`` register. This
        property is read-only. Use :py:meth:`alert_voltage_high_flag_clear` to
        clear the flag after handling the alert.

        See Also
        --------
        :py:attr:`alert_voltage_high_threshold`
        :py:meth:`alert_voltage_high_flag_clear`
        """
        return bool(self._vh)

    def alert_voltage_high_flag_clear(self) -> None:
        """
        Clear the voltage high flag.

        Clear the ``VH`` (voltage high) flag in the ``STATUS`` register.

        See Also
        --------
        :py:attr:`alert_voltage_high_flag`
        """
        self._vh = 0

    # Voltage Low
    @property
    def alert_voltage_low_flag(self) -> bool:
        """
        Voltage low flag.

        Indicates whether the low voltage alert is active. ``True`` means the cell
        voltage has fallen below the threshold set in :py:attr:`voltage_alert_min`.

        Returns
        -------
        bool
            ``True`` if the cell voltage has fallen below the threshold,
            ``False`` otherwise.

        Notes
        -----
        Corresponds to the ``VL`` bit in the ``STATUS`` register. This
        property is read-only. Use :py:meth:`alert_voltage_low_flag_clear` to
        clear the flag after handling the alert.

        See Also
        --------
        :py:attr:`voltage_alert_min`
        :py:meth:`alert_voltage_low_flag_clear`
        """
        return bool(self._vl)

    def alert_voltage_low_flag_clear(self) -> None:
        """
        Clear the voltage low flag.

        Clear the ``VL`` (voltage low) flag in the ``STATUS`` register.

        See Also
        --------
        :py:attr:`alert_voltage_low_flag`
        """
        self._vl = 0