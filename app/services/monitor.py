import psutil
from .log import get_logger
from logging import Logger
from .custom_types import MonitoringMessage, ListMonitoringMessage
from functools import cache
import cv2


class MonitoringService:
    def __init__(self, logger: Logger):
        self.logger = logger

        self.locked_status = None
        self.network_status = None
        self.charger_status = None
        self.valid_methods = None

    def check_locked_status(self) -> MonitoringMessage:
        title = "System Locked Status"
        locked_status = False
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == "LogonUI.exe":
                locked_status = True
                break

        if locked_status:
            content = "LOCKED!"
            ok_status = False
        else:
            content = "NOT LOCKED!"
            ok_status = True

        return MonitoringMessage(
            title=title,
            content=content,
            ok_status=ok_status,
        )

    def check_charger_status(self) -> MonitoringMessage:
        battery = psutil.sensors_battery()
        title = "Charger Status"
        if battery is None:
            self.logger.warning("Battery information not available.")
            content = "Battery information not available."
            ok_status = None
            value = None
        else:
            if battery.power_plugged:
                self.logger.info("Charger is connected.")
                content = (
                    f"Charger is connected. Battery percentage: {battery.percent}%"
                )
                ok_status = True

            else:
                self.logger.warning("Charger is not connected.")
                content = (
                    f"Charger is NOT connected. Battery percentage: {battery.percent}%"
                )
                ok_status = False
            value = battery.percent

        return MonitoringMessage(
            title=title,
            content=content,
            ok_status=ok_status,
            value=str(value)
        )

    def check_network_status(self) -> MonitoringMessage:
        ethernet_status = psutil.net_if_stats().get("Ethernet")
        wifi_status = psutil.net_if_stats().get("Wi-Fi")
        title="Network Status"
        if ethernet_status and ethernet_status.isup:
            self.logger.debug("Ethernet is connected.")
            content="Ethernet is connected."
            ok_status=True
        elif wifi_status and wifi_status.isup:
            self.logger.debug("Wi-Fi is connected.")
            content="Wi-Fi is connected."
            ok_status=True
        else:
            self.logger.warning("No network connection detected.")
            content="Wi-Fi is connected."
            ok_status=True
        
        return MonitoringMessage(
            title=title,
            content=content,
            ok_status=ok_status,
        )

    def setup(self) -> None:
        check_methods = [method for method in dir(self) if method.startswith("check_")]
        valid_methods = []
        for method_name in check_methods:
            self.logger.debug(
                f"Checking {method_name.replace('check_', '')} availability"
            )
            method = getattr(self, method_name)
            result = method()
            if result is not None:
                self.logger.info(f"{method_name.replace('check_', '')} available.")
                valid_methods.append(method_name)
            else:
                self.logger.info(f"{method_name.replace('check_', '')} NOT available.")
                self.logger.warning(
                    f"{method_name.replace('check_', '').capitalize()} not available."
                )

        self.valid_methods = valid_methods

    def system_status(self) -> ListMonitoringMessage:
        methods_results = []
        for method_name in self.valid_methods:
            self.logger.debug(f"Checking {method_name.replace('check_', '')} status...")
            method = getattr(self, method_name)
            result = method()
            methods_results.append(result)
            setattr(self, method_name.replace("check_", ""), result)

        return methods_results

    def get_photo(self):
        # Initialize the webcam (0 represents the default camera)
        cap = cv2.VideoCapture(0)

        # Check if the webcam opened successfully
        if not cap.isOpened():
            self.logger.error("Error: Could not open webcam.")
            return None

        # Capture a single frame
        ret, frame = cap.read()
        cap.release()
        # Check if the frame was captured successfully
        if ret:
            # Display the captured frame (optional)
            is_success, buffer = cv2.imencode(".jpg", frame)
            if not is_success:
                self.logger.error("Error: Could not encode image.")
                return None

            # Save the captured frame as an image file
            return buffer.tobytes()

        else:
            self.logger.error("Error: Failed to capture frame.")

        return None


@cache
def get_monitor() -> MonitoringService:
    monitor = MonitoringService(get_logger())
    monitor.setup()
    return monitor
