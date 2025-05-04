import psutil
import wmi
from datetime import datetime
from typing import Dict, Any, Optional
from socket import AF_INET
import winreg
from utils import setup_logging

class TelemetryCollector:
    def __init__(self, log_enabled: bool = False, log_dir: str = "telemetry_logs"):
        # init telemetry collector
        self.wmi_client = self._init_wmi()
        self.log_enabled = log_enabled
        self.logger = setup_logging(log_dir) if log_enabled else None
        self.telemetry_data: Dict[str, Any] = {}

    def _init_wmi(self) -> Optional[Any]:
        # init WMI client
        try:
            return wmi.WMI()
        except Exception as e:
            if self.log_enabled and self.logger:
                self.logger.error(f"WMI initialization failed: {e}")
            return None

    def _log(self, message: str) -> None:
        # log notif if currently logging telemetry

        if self.log_enabled and self.logger:
            self.logger.info(message)

    def get_cpu_telemetry(self) -> Dict[str, Any]:
        # CPU telemetry fn
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_cores = psutil.cpu_count(logical=True)
            cpu_physical_cores = psutil.cpu_count(logical=False)
            cpu_data = {
                "cpu_usage_percent": cpu_percent,
                "cpu_frequency_mhz": cpu_freq.current if cpu_freq else None,
                "cpu_max_frequency_mhz": cpu_freq.max if cpu_freq else None,
                "logical_cores": cpu_cores,
                "physical_cores": cpu_physical_cores,
                "timestamp": datetime.now().isoformat()
            }
            self.telemetry_data["cpu"] = cpu_data
            self._log(f"Collected CPU telemetry: {cpu_data}")
            return cpu_data
        except Exception as e:
            self._log(f"Error collecting CPU telemetry: {e}")
            return {}

    def get_memory_telemetry(self) -> Dict[str, Any]:
        # Memory telemetry fn
        try:
            memory = psutil.virtual_memory()
            memory_data = {
                "total_memory_mb": memory.total / (1024 ** 2),
                "used_memory_mb": memory.used / (1024 ** 2),
                "free_memory_mb": memory.available / (1024 ** 2),
                "memory_usage_percent": memory.percent,
                "timestamp": datetime.now().isoformat()
            }
            self.telemetry_data["memory"] = memory_data
            self._log(f"Collected memory telemetry: {memory_data}")
            return memory_data
        except Exception as e:
            self._log(f"Error collecting memory telemetry: {e}")
            return {}

    def get_disk_telemetry(self) -> Dict[str, Any]:
        # Dist telemetry fn
        disk_data = {}
        try:
            disk_partitions = psutil.disk_partitions()
            for partition in disk_partitions:
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    disk_data[partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "total_space_gb": disk_usage.total / (1024 ** 3),
                        "used_space_gb": disk_usage.used / (1024 ** 3),
                        "free_space_gb": disk_usage.free / (1024 ** 3),
                        "usage_percent": disk_usage.percent,
                        "timestamp": datetime.now().isoformat()
                    }
                except PermissionError:
                    self._log(f"Permission denied accessing {partition.device}")
                    continue
            self.telemetry_data["disk"] = disk_data
            self._log(f"Collected disk telemetry: {disk_data}")
            return disk_data
        except Exception as e:
            self._log(f"Error collecting disk telemetry: {e}")
            return {}

    def get_network_telemetry(self) -> Dict[str, Any]:
        # Network telemetry fn
        network_data = {}
        try:
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            for iface in net_io:
                try:
                    stats = net_io[iface]
                    if_stats = net_if_stats.get(iface, None)
                    addrs = net_if_addrs.get(iface, [])
                    ip_addresses = [addr.address for addr in addrs if addr.family == AF_INET]
                    network_data[iface] = {
                        "bytes_sent": stats.bytes_sent / (1024 ** 2),
                        "bytes_received": stats.bytes_recv / (1024 ** 2),
                        "packets_sent": stats.packets_sent,
                        "packets_received": stats.packets_recv,
                        "errors_in": stats.errin,
                        "errors_out": stats.errout,
                        "dropped_in": stats.dropin,
                        "dropped_out": stats.dropout,
                        "is_up": if_stats.isup if if_stats else None,
                        "speed_mbps": if_stats.speed if if_stats else None,
                        "mtu": if_stats.mtu if if_stats else None,
                        "ip_addresses": ip_addresses,
                        "timestamp": datetime.now().isoformat()
                    }
                    if self.wmi_client:
                        for adapter in self.wmi_client.Win32_NetworkAdapter():
                            if adapter.NetConnectionID == iface:
                                network_data[iface].update({
                                    "adapter_name": adapter.Name,
                                    "mac_address": adapter.MACAddress,
                                    "connection_status": adapter.NetConnectionStatus
                                })
                except Exception as e:
                    self._log(f"Error collecting data for network interface {iface}: {e}")
                    continue
            self.telemetry_data["network"] = network_data
            self._log(f"Collected network telemetry: {network_data}")
            return network_data
        except Exception as e:
            self._log(f"Error collecting network telemetry: {e}")
            return {}

    def get_power_telemetry(self) -> Dict[str, Any]:
        # Battery telemetry
        power_data = {}
        try:
            battery = psutil.sensors_battery()
            if battery:
                power_data["battery"] = {
                    "percent": battery.percent,
                    "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "unlimited",
                    "power_plugged": battery.power_plugged,
                    "timestamp": datetime.now().isoformat()
                }
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes") as key:
                    active_scheme = winreg.QueryValueEx(key, "ActivePowerScheme")[0]
                    power_data["active_power_scheme_guid"] = active_scheme
            except Exception as e:
                self._log(f"Error accessing power scheme: {e}")
            self.telemetry_data["power"] = power_data
            self._log(f"Collected power telemetry: {power_data}")
            return power_data
        except Exception as e:
            self._log(f"Error collecting power telemetry: {e}")
            return {}

    def get_all_telemetry(self) -> Dict[str, Any]:
        # Telemetry aggregator from all other fns
        try:
            telemetry = {
                "cpu": self.get_cpu_telemetry(),
                "memory": self.get_memory_telemetry(),
                "disk": self.get_disk_telemetry(),
                "network": self.get_network_telemetry(),
                "power": self.get_power_telemetry(),
                "collection_timestamp": datetime.now().isoformat()
            }
            self._log(f"Collected all telemetry: {telemetry}")
            return telemetry
        except Exception as e:
            self._log(f"Error collecting all telemetry: {e}")
            return {}