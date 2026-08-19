import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from logic.SiteMonitor import SiteMonitor
from logic.SystemMonitor import SystemMonitor
from logic.DisplayManager import DisplayManager

# Set system update rates.
SYSTEM_SAMPLE = 10 # Seconds between system stats checked (CPU Temp)
SYSTEM_SCHEDULER = 60 # Minutes between scheduler system run.

# Site monitoring is static at once per day.

def run_monitor():
    scheduler = BackgroundScheduler()
    display_manager = DisplayManager()
    system_upload = SYSTEM_SCHEDULER * 60 - 10

    SystemMonitor.system_monitor(10, 10)

    scheduler.add_job(
        SystemMonitor.system_monitor, "interval", minutes=SYSTEM_SCHEDULER, id="system_monitor",
        args=[SYSTEM_SAMPLE, system_upload], next_run_time=datetime.now()
    )

    scheduler.add_job(
        SiteMonitor.site_monitor, "cron", hour=1, minute=0, id="site_monitor", next_run_time=datetime.now()
    )

    scheduler.add_job(
        display_manager.update_screen,
        'interval',
        minutes=10,
        id='display_manager',
        next_run_time=datetime.now()
    )

    scheduler.start()
    print("Starting scheduled monitoring. Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except(KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Exiting scheduled monitoring.")


if __name__ == "__main__":
    run_monitor()