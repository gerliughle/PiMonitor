import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import psutil

from Database import Database



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

def collect_temp(sample_interval=10, total_duration=120):
    """ Collects CPU temp at provided intervals. At end of duration, return sample list"""
    readings = []

    num_samples = int(total_duration / sample_interval)

    print(f"Starting CPU collections: sampling every {sample_interval}s for {total_duration}s total.")

    for i in range(num_samples):
        temp = get_cpu_temp()
        readings.append(temp)
        print(f"Sample {i + 1}/{num_samples}: {temp}°C")
        time.sleep(sample_interval)
    return readings

def temp_summary(readings):
    if not readings:
        return None

    return{
        "avg_temp": round(sum(readings) / len(readings), 2),
        "max_temp": round(max(readings), 2),
        "min_temp": round(min(readings), 2),
        "sample_count": len(readings)
    }


def run_monitor():
    while True:
        readings = collect_temp(sample_interval=10, total_duration=120)
        summary = temp_summary(readings)
        print("\nSummary:")
        for item in summary:
            print(f"{item}: {summary[item]}")
            print()
        Database.upload_readings(readings)
        log = Database.read_data()
        build_graph(log)

def build_graph(log_data):
    data = []
    for item in log_data:
        for reading in item["readings"]:
            row = [item["timestamp"], reading]
            data.append(row)

    df = pd.DataFrame(data, columns=("timestamp", "reading"))
    sns.catplot(x="timestamp", y="reading", data=df, kind="box")
    plt.show()


if __name__ == "__main__":
    print(f"Current CPU temp: {get_cpu_temp()}°C")
    run_monitor()

