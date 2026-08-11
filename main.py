def get_cpu_temp():
    """ Reads Pi CPU temp in C """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_raw = int(f.read().strip())
            return round(temp_raw / 1000.0, 2)
    except FileNotFoundError:
        print("Thermal zone file not found.")
        return 0.0




if __name__ == "__main__":
    print(f"Current CPU temp: {get_cpu_temp()}°C")