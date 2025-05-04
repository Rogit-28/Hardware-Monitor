import time
from telemetryCollector import TelemetryCollector

def main():
    collector = TelemetryCollector(log_enabled=True)
    
    print("Collecting telemetry every 10 seconds...")
    try:
        while True:
            telemetry = collector.get_all_telemetry()
            print("\nTelemetry Data:")
            print(f"CPU Usage: {telemetry.get('cpu', {}).get('cpu_usage_percent', 'N/A')}%")
            print(f"Memory Usage: {telemetry.get('memory', {}).get('memory_usage_percent', 'N/A')}%")
            for device, disk_data in telemetry.get('disk', {}).items():
                print(f"Disk {device}: {disk_data.get('usage_percent', 'N/A')}%")
            for iface, net_data in telemetry.get('network', {}).items():
                print(f"Network {iface}: Sent {net_data.get('bytes_sent', 'N/A')} MB, Received {net_data.get('bytes_received', 'N/A')} MB")
            if telemetry.get('power', {}).get('battery'):
                print(f"Battery: {telemetry.get('power', {}).get('battery', {}).get('percent', 'N/A')}%")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nTelemetry collection stopped.")

if __name__ == "__main__":
    main()