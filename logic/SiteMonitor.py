import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from database.Database import Database
from database.CloudFlareTraffic import CloudFlareTraffic

class SiteMonitor:

    @classmethod
    def site_monitor(cls):
        CloudFlareTraffic.get_cloudflare_analytics(7)
        log = Database.read_site_stats()
        cls.build_site_graph(log)

    @classmethod
    def build_site_graph(cls, log):
        df = pd.DataFrame(log)
        df_melted = pd.melt(df, id_vars=["date"], value_vars=["total_requests", "unique_visitors"],
                            var_name="Metric", value_name="Value")


        plt.figure(figsize = (10,5))

        sns.lineplot(data=df_melted, x="date", y="Value", hue="Metric")
        plt.savefig("SiteGraph.png")
        plt.close()


if __name__ == "__main__":
    SiteMonitor.site_monitor()