import os
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from logic.SystemMonitor import SystemMonitor


HAS_HARDWARE = False
try:
    from waveshare_epd import epd3in52b
    HAS_HARDWARE = True
except(ImportError, OSError):
    print("[DisplayManager] Failed to import epd3in52b epaper display. Running dev mode.")


class DisplayManager:

    def __init__(self, db_connection=None):
        self.db = db_connection
        self.width = 360
        self.height = 240

    @staticmethod
    def generate_system_graph(output_path="SystemGraph.png"):
        data = SystemMonitor.get_system_data()
        df = pd.DataFrame(data, columns=("timestamp", "reading"))
        if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = df["timestamp"].dt.strftime("%H:%M")
        else:
            df["timestamp"] = df["timestamp"].astype(str)


        fix, ax = plt.subplots(figsize=(3.6, 2.4), dpi=150)
        sns.boxplot(
            x="timestamp",
            y="reading",
            data=df,
            color='white',
            linecolor='black',
            fliersize=2
        )
        ax.set_xlabel("")
        ax.set_ylabel("CPU °C")
        ax.set_xticklabels([])
        ax.tick_params(axis='y', labelsize=8)
        sns.despine()
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

    def update_screen(self):
        try:
            image_path = "SystemGraph.png"
            self.generate_system_graph(image_path)
            img = Image.open(image_path).convert("1")
            rotated_img = img.rotate(90, expand=True)
            resized_img = rotated_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            dithered = resized_img.convert("L").convert("1", dither=Image.Dither.FLOYDSTEINBERG)

            if HAS_HARDWARE:

                epd = epd3in52b.EPD()
                epd.init()
                red_image = Image.new("1", (epd.width, epd.height), 255)

                epd.display(epd.getbuffer(dithered), epd.getbuffer(red_image))
                epd.sleep()
            else:
                dev_preview_path = "SystemGraph_preview.png"
                dithered.save(dev_preview_path)


        except Exception as e:
            print(f"[DisplayManager] Refresh failed: {e}")
