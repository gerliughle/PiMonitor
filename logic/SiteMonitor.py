import pandas as pd
import requests

from database.CloudFlareTraffic import CloudFlareTraffic
from database.Database import Database
from datetime import datetime, timezone


class SiteMonitor:

    @classmethod
    def site_monitor(cls):
        CloudFlareTraffic.get_cloudflare_analytics(7)
        log = Database.read_site_stats()


    @staticmethod
    def get_status(url="https://bonsaitree.wiki", timeout=5):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return "Good"
            else:
                return f"HTTP {response.status_code}"
        except requests.exceptions.RequestException:
            return "DOWN"

    @classmethod
    def get_df(cls):
        CloudFlareTraffic.get_cloudflare_analytics(7)
        log = Database.read_site_stats()
        df = pd.DataFrame(log)
        df_melted = pd.melt(df, id_vars=["date"], value_vars=["total_requests", "unique_visitors"],
                            var_name="Metric", value_name="Value")
        df_melted = df_melted[df_melted["date"] != datetime.now(timezone.utc).strftime("%Y-%m-%d")]
        return df_melted


if __name__ == "__main__":
    SiteMonitor.site_monitor()