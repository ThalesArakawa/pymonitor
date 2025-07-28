import psutil
from .telegram_bot import TelegramBot

class WindowsMonitor:
    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot

    def check_locked_status(self) -> bool:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'LogonUI.exe':
                return False
        return True

    def check_network_status(self) -> bool:
        ethernet_status = psutil.net_if_stats().get('Ethernet')
        wifi_status = psutil.net_if_stats().get('Wi-Fi')
        if ethernet_status and ethernet_status.isup:
            return True
        return False
    
    
    def check_charger_status(self) -> bool:
        battery = psutil.sensors_battery()
        if battery is None:
            return False
        return not battery.power_plugged
    
    def system_status(self) -> str:
        check_methods = [method for method in dir(self) if method.startswith('check_')]
        for method_name in check_methods:
            method = getattr(self, method_name)
            if not method():
                print(f"{method_name} with Problem.")
                self.telegram_bot.send_message(f"{method_name} with Problem.")
            