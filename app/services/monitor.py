import psutil
import logging
from .types import MonitoringMessage

class MonitoringService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

        self.locked_status = None
        self.network_status = None
        self.charger_status = None
        self.valid_methods = None

    def check_locked_status(self) -> MonitoringMessage:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'LogonUI.exe':
                return MonitoringMessage(
                    title="System Locked Status",
                    content="The system is currently LOCKED.",
                    timestamp=psutil.boot_time(),
                    ok_status=False
                )
        return MonitoringMessage(
            title="System Locked Status",
            content="The system is NOT LOCKED.",
            timestamp=psutil.boot_time(),
            ok_status=True
        )

    def check_charger_status(self) -> MonitoringMessage:
        battery = psutil.sensors_battery()
        if battery is None:
            self.logger.warning("Battery information not available.")
            return MonitoringMessage(
                title="Charger Status",
                content="Battery information not available.",
                ok_status=None
            )
        
        if battery.power_plugged:
            self.logger.info("Charger is connected.")
            return MonitoringMessage(
                title="Charger Status",
                content=f"Charger is connected. Battery percentage: {battery.percent}%",
                ok_status=True
            )
        self.logger.warning("Charger is not connected.")
        return MonitoringMessage(
            title="Charger Status",
            content=f"Charger is NOT connected. Battery percentage: {battery.percent}%",
            timestamp=psutil.boot_time(),
            ok_status=False
        )

    def check_network_status(self) -> MonitoringMessage:
        ethernet_status = psutil.net_if_stats().get('Ethernet')
        wifi_status = psutil.net_if_stats().get('Wi-Fi')
        if ethernet_status and ethernet_status.isup:
            self.logger.debug("Ethernet is connected.")
            return MonitoringMessage(
                title="Network Status",
                content="Ethernet is connected.",
                ok_status=True
            )
        elif wifi_status and wifi_status.isup:
            self.logger.debug("Wi-Fi is connected.")
            return MonitoringMessage(
                title="Network Status",
                content="Wi-Fi is connected.",
                ok_status=True
            )
        self.logger.warning("No network connection detected.")
        return MonitoringMessage(
            title="Network Status",
            content="No network connection detected.",
            timestamp=psutil.boot_time(),
            ok_status=False
        )
    
    def setup(self) -> None:
        check_methods = [method for method in dir(self) if method.startswith('check_')]
        valid_methods = []
        for method_name in check_methods:
            self.logger.debug(f"Checking {method_name.replace('check_', '')} availability")
            method = getattr(self, method_name)
            result = method()
            if result is not None:
                self.logger.info(f"{method_name.replace('check_', '')} available.")
                valid_methods.append(method_name)
            else:
                self.logger.info(f"{method_name.replace('check_', '')} NOT available.")
                self.logger.warning(f"{method_name.replace('check_', '').capitalize()} not available.")

        self.valid_methods = valid_methods


    def system_status(self) -> list:
        methods_results = []
        for method_name in self.valid_methods:
            self.logger.debug(f"Checking {method_name.replace('check_', '')} status...")
            method = getattr(self, method_name)
            result = method()
            methods_results.append(result)
            if result != getattr(self, method_name.replace('check_', '')):
                self.logger.debug(f"{method_name.replace('check_', '').capitalize()} status changed from {getattr(self, method_name.replace('check_', ''))} to {result}")
                setattr(self, method_name.replace('check_', ''), result)
            
        return methods_results