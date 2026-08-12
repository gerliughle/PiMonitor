import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from logic.SiteMonitor import SiteMonitor
from logic.SystemMonitor import SystemMonitor

# Set system update rates.
SYSTEM_SAMPLE = 10 # Seconds between system stats checked (CPU Temp)
SYSTEM_UPLOAD = 550 # Seconds between system stats uploaded, graph updated. Set a few seconds less than SYSTEM_SCHEDULER
SYSTEM_SCHEDULER = 10 # Minutes between scheduler system run.

# Site monitoring is static at once per day.

def run_monitor():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        SystemMonitor.system_monitor, "interval", minutes=SYSTEM_SCHEDULER, id="system_monitor",
        args=[SYSTEM_SAMPLE, SYSTEM_UPLOAD], next_run_time=datetime.now()
    )

    scheduler.add_job(
        SiteMonitor.site_monitor, "cron", hour=1, minute=0, id="site_monitor", next_run_time=datetime.now()
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