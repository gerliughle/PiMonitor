import os
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from waveshare_epd import epd3in52b

from SystemMonitor import SystemMonitor

class DisplayManager:
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.width = 360
        self.height = 240

    @staticmethod
    def generate_system_graph(output_path="SystemGraph.png"):
        df = pd.DataFrame(SystemMonitor.system_log, columns=("timestamp", "reading"))
        g = sns.catplot(
            x="timestamp",
            y="reading",
            data=df,
            kind="box",
            height=2.4,
            aspect=3.6 / 2.4
        )
        g.set_xticklabels(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        plt.close()

    def update_screen(self):
        try:
            image_path = "SystemGraph.png"
            self.generate_system_graph(image_path)
            epd = epd3in52b.EPD()
            epd.init()

            Himage = Image.open(image_path).convert("RGB")
            Himage = Himage.resize((epd.width, epd.height))

            epd.display(epd.getbuffer(Himage))
            epd.sleep()

        except Exception as e:
            print(f"[DisplayManager] Refresh failed: {e}")
