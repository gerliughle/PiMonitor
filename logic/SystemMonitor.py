import psutil
import time
import pandas as pd
from database.Database import Database

class SystemMonitor:
    system_log = None
    system_data = []


    @staticmethod
    def get_cpu_temp():
        """ Reads Pi CPU temp in C """
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_raw = int(f.read().strip())
                if temp_raw != 27800:
                    return round(temp_raw / 1000.0, 2)

        except Exception:
            pass

        # For testing
        temps = psutil.sensors_temperatures()
        cpu_temp = temps['coretemp'][0].current
        return round(cpu_temp, 2)

    @classmethod
    def collect_temp(cls, sample_interval=10, total_duration=120):
        """ Collects CPU temp at provided intervals. At end of duration, return sample list"""
        readings = []

        num_samples = int(total_duration / sample_interval)

        print(f"Starting CPU collections: sampling every {sample_interval}s for {total_duration}s total.")

        for i in range(num_samples):
            temp = cls.get_cpu_temp()
            readings.append(temp)
            print(f"Sample {i + 1}/{num_samples}: {temp}°C")
            time.sleep(sample_interval)
        return readings


    @staticmethod
    def temp_summary(readings):
        if not readings:
            return None

        return {
            "avg_temp": round(sum(readings) / len(readings), 2),
            "max_temp": round(max(readings), 2),
            "min_temp": round(min(readings), 2),
            "sample_count": len(readings)
        }

    @classmethod
    def system_monitor(cls, sample_interval, total_duration):

        readings = cls.collect_temp(sample_interval=sample_interval, total_duration=total_duration)

        summary = cls.temp_summary(readings)
        print("\nSummary:")
        for item in summary:
            print(f"{item}: {summary[item]}")
        print()
        Database.upload_cpu_readings(readings)
        cls.system_log = Database.read_system_stats()
        cls.system_data = []
        for item in cls.system_log:
            for reading in item["readings"]:
                row = [item["timestamp"], reading]
                cls.system_data.append(row)

    @classmethod
    def get_system_data(cls):
        cls.system_log = Database.read_system_stats()
        cls.system_data = []
        for item in cls.system_log:
            for reading in item["readings"]:
                row = [item["timestamp"], reading]
                cls.system_data.append(row)
        return cls.system_data

    @classmethod
    def get_df(cls):
        data = cls.get_system_data()
        df = pd.DataFrame(data, columns=("timestamp", "reading"))
        if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = df["timestamp"].dt.strftime("%H:%M")
        else:
            df["timestamp"] = df["timestamp"].astype(str)
        return df



