class MAX17048:

    def __init__(self, i2c_bus: int = 1, address: int = 0x36) -> None:
        pass

    def reset() -> None:
        raise NotImplementedError("Reset method not implemented")

    def cell_voltage(self) -> float:
        raise NotImplementedError("Cell voltage method not implemented")

    def cell_percent(self) -> float:
        raise NotImplementedError("Cell percent method not implemented")

    def charge_rate(self) -> float:
        raise NotImplementedError("Charge rate method not implemented")

    def reset_voltage(self) -> float:
        raise NotImplementedError("Reset voltage method not implemented")

    def voltage_alert_min(self) -> float:
        raise NotImplementedError("Voltage alert min method not implemented")

    def voltage_alert_max(self) -> float:
        raise NotImplementedError("Voltage alert max method not implemented")

    def active_alert(self) -> bool:
        raise NotImplementedError("Active alert method not implemented")

    def alert_reason(self) -> int:
        raise NotImplementedError("Alert reason method not implemented")

    def activity_threshold(self) -> float:
        raise NotImplementedError("Activity threshold method not implemented")
    
    def hibernation_threshold(self) -> float:
        raise NotImplementedError("Hibernation threshold method not implemented")

    def hibernate(self) -> None:
        raise NotImplementedError("Hibernate method not implemented")

    def wake(self) -> None:
        raise NotImplementedError("Wake method not implemented")
