import psutil
from .telegram_bot import TelegramBot
import logging

class WindowsMonitor:
    def __init__(self, telegram_bot: TelegramBot, logger: logging.Logger):
        self.telegram_bot = telegram_bot
        self.logger = logger

        self.locked_status = None
        self.network_status = None
        self.charger_status = None

    def check_locked_status(self) -> bool:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'LogonUI.exe':
                return True
        return False

    def check_charger_status(self) -> bool:
        battery = psutil.sensors_battery()
        if battery is None:
            self.logger.warning("Battery information not available.")
            return None
        
        if battery.power_plugged:
            self.logger.info("Charger is connected.")
            return True
        self.logger.warning("Charger is not connected.")
        return False

    def check_network_status(self) -> bool:
        ethernet_status = psutil.net_if_stats().get('Ethernet')
        wifi_status = psutil.net_if_stats().get('Wi-Fi')
        if ethernet_status and ethernet_status.isup:
            return True
        elif wifi_status and wifi_status.isup:
            return True
        return False
    
    def setup(self) -> list:
        check_methods = [method for method in dir(self) if method.startswith('check_')]
        valid_methods = []
        for method_name in check_methods:
            self.logger.info(f"Checking {method_name.replace('check_', '')} availability")
            method = getattr(self, method_name)
            result = method()
            if result is not None:
                self.logger.info(f"{method_name.replace('check_', '')} available.")
                valid_methods.append(method_name)
            else:
                self.logger.info(f"{method_name.replace('check_', '')} NOT available.")
                self.logger.warning(f"{method_name.replace('check_', '').capitalize()} not available.")

        return valid_methods


    def system_status(self, to_monitor: list) -> str:
        check_methods = [method for method in dir(self) if method.startswith('check_')]
        for method_name in to_monitor:
            self.logger.debug(f"Checking {method_name.replace('check_', '')} status...")
            method = getattr(self, method_name)
            result = method()
            if result != getattr(self, method_name.replace('check_', '')):
                self.logger.info(f"{method_name.replace('check_', '').capitalize()} status changed from {getattr(self, method_name.replace('check_', ''))} to {result}")
                self.telegram_bot.send_message(f"{method_name.replace('check_', '').capitalize()} status changed: {result}")
                setattr(self, method_name.replace('check_', ''), result)
            