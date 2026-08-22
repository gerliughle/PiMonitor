import os
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.font_manager as fm

from logic.SystemMonitor import SystemMonitor
from logic.SiteMonitor import SiteMonitor


HAS_HARDWARE = False
try:
    from waveshare_epd import epd3in52b
    HAS_HARDWARE = True
except(ImportError, OSError):
    print("[DisplayManager] Failed to import epd3in52b epaper display. Running dev mode.")

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "Font.ttc")
if os.path.exists(FONT_PATH):
    custom_font = fm.FontProperties(fname=FONT_PATH, size=9)
    title_font = fm.FontProperties(fname=FONT_PATH, size=10, weight="bold")
else:
    custom_font = fm.FontProperties(size=9, weight="bold")
    title_font = fm.FontProperties(size=10, weight="bold")

class DisplayManager:
    WIDTH = 480
    HEIGHT = 720

    def __init__(self, db_connection=None):
        self.db = db_connection

    @staticmethod
    def generate_layered_dashboard(cpu_df, traffic_df):
        """ This is the most annoying func of all time.

        Take in a DF for CPU and Traffic, and save a black and red image.
        May not build entire image."""
        print("Generating Image")

        fig, ax = plt.subplots(2, 1, figsize=(4.8, 6)) # Leaving space at top
        sns.set_context("poster", font_scale=0.5)
        sns.axes_style({"xtick.bottom": False})

        if not cpu_df.empty:
            sns.boxenplot(cpu_df,
                        x="timestamp",
                        y="reading",
                        color="black",
                        fill=False,
                        # linewidth=2,
                        ax=ax[0])
            ax[0].set_xlabel("")
            ax[0].set_ylabel("CPU Temp")
            ax[0].set_xticklabels([])

        else:
            print("Error, no CPU dataframe.")
        if not traffic_df.empty:
            requests_df = traffic_df[traffic_df["Metric"] == "unique_visitors"]
            sns.lineplot(requests_df,
                         x="date",
                         y="Value",
                         ax=ax[1],
                         # linewidth=2,
                         color="r")
            ax[1].set_xlabel("")
            ax[1].set_ylabel("Traffic")
            ax[1].set_xticklabels([])
        else:
            print("Error, no Traffic dataframe.")


        sns.despine()
        fig.tight_layout()


        fig.savefig("test_plot.png")
        plt.close(fig)
        print("Image Generated.")







    @classmethod
    def update_screen(cls):

        try:
            cpu_df = SystemMonitor.get_df()
            traffic_df = SiteMonitor.get_df()
            site_status = SiteMonitor.get_status()
            cls.generate_layered_dashboard(cpu_df, traffic_df)

            black_img = Image.open("layer_black.png")
            red_img = Image.open("layer_red.png")

            # rotated_img = img.rotate(90, expand=True)
            resized_b = black_img.resize((cls.WIDTH, cls.HEIGHT), Image.Resampling.LANCZOS)
            resized_r = red_img.resize((cls.WIDTH, cls.HEIGHT), Image.Resampling.LANCZOS)
            # dithered = resized_img.convert("L").convert("1", dither=Image.Dither.FLOYDSTEINBERG)

            final_b = resized_b
            final_r = resized_r

            if HAS_HARDWARE:

                epd = epd3in52b.EPD()
                epd.init()


                epd.display(epd.getbuffer(final_b), epd.getbuffer(final_r))
                epd.sleep()
            else:
                final_b.save("black_preview.png")
                final_r.save("red_preview.png")


        except Exception as e:
            print(f"[DisplayManager] Refresh failed: {e}")
