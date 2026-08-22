import os

import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageText, ImageFont
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

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "determination.ttf")
if os.path.exists(FONT_PATH):
    custom_font = fm.FontProperties(fname=FONT_PATH, size=10, weight="bold")
    title_font = fm.FontProperties(fname=FONT_PATH, size=13)
    title_ImageFont = ImageFont.truetype(FONT_PATH, 18)
    text_ImageFont = ImageFont.truetype(FONT_PATH, 12)
else:
    custom_font = fm.FontProperties(size=10, weight="bold")
    title_font = fm.FontProperties(size=13, weight="bold")


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

        layout = [['CB', 'CK'],
                  ['T', 'T']]
        fig, ax = plt.subplot_mosaic(layout, figsize=(2.4, 3), dpi=400, width_ratios=[5, 1])  # Leaving space at top
        sns.axes_style({"xtick.bottom": False})

        sns.boxenplot(cpu_df,
                      x="timestamp",
                      y="reading",
                      color="black",
                      fill=False,
                      flier_kws={"marker": ".",
                                 "facecolor": "black",
                                 "linewidth": 1.5
                                 },
                      ax=ax['CB']
                      )

        ax['CB'].set_xlabel("")
        ax['CB'].set_ylabel("")
        ax['CB'].set_xticks([])
        ax['CB'].set_title("CPU °C", fontproperties=title_font, loc="left")
        for label in ax['CB'].get_yticklabels():
            label.set_fontproperties(custom_font)

        sns.kdeplot(cpu_df,
                    y='reading',
                    ax=ax['CK'],
                    color="black",
                    linewidth=1.5)
        ax['CK'].set_xlabel("")
        ax['CK'].set_ylabel("")
        ax['CK'].set_xticks([])
        ax['CK'].set_yticks([])
        ax['CK'].set_title("")

        requests_df = traffic_df[traffic_df["Metric"] == "unique_visitors"]

        sns.regplot(requests_df,
                    x=requests_df.index,
                    y="Value",
                    order=2,
                    ci=None,
                    marker='.',
                    scatter=False,
                    line_kws={"linestyle": ":"},
                    color="black",
                    ax=ax['T'])
        sns.lineplot(requests_df,
                     x=requests_df.index,
                     y="Value",
                     ax=ax['T'],
                     color="black",
                     linewidth=2,
                     )
        ax['T'].set_xlabel("")
        ax['T'].set_ylabel("")
        ax['T'].set_xticks([])
        ax['T'].set_title("Site Requests", fontproperties=title_font, loc="left")
        for label in ax['T'].get_yticklabels():
            label.set_fontproperties(custom_font)

        sns.despine(bottom=True)
        fig.tight_layout()

        fig.savefig("layer_black.png")
        plt.close(fig)
        print("Image Generated.")

    @classmethod
    def update_screen(cls):
        try:
            cpu_df = SystemMonitor.get_df()
            traffic_df = SiteMonitor.get_df()
            site_status = SiteMonitor.get_status()
            cls.generate_layered_dashboard(cpu_df, traffic_df)

            black_img = Image.open("layer_black.png").convert("L")
            black_img = black_img.resize((240, 300), resample=Image.Resampling.LANCZOS)

            # for i in range(100, 150):
            #     new_img = black_img.point(lambda x: 255 if x > i else 0).convert("1")
            #     new_img.save(f"{i}_black_img_preview.png")
            new_img = black_img.point(lambda x: 255 if x > 127 else 0).convert("1")

            dashboard_b = Image.new("1", (240, 360), 255)
            dashboard_b.paste(new_img, (-5, 60))

            title = ImageText.Text("ServePi!", title_ImageFont)
            title.embed_color()

            status = ImageText.Text("BonsaiTree.Wiki status: ", text_ImageFont)
            status.embed_color()

            b = ImageDraw.Draw(dashboard_b)
            b.text((20, 10), title, 0)
            b.text((20, 34), status, 0)

            # Red image
            dashboard_r = Image.new("1", (240, 360), 255)

            site_status = SiteMonitor.get_status()
            if site_status == "Good":

                status_text = ImageText.Text("Good!", text_ImageFont)
                status_text.embed_color()
                b.text((175, 34), status_text, 0)
            else:
                r = ImageDraw.Draw(dashboard_r)
                status_text = ImageText.Text(site_status, text_ImageFont)
                status_text.embed_color()
                r.text((175, 34), status_text, 0)

            if HAS_HARDWARE:

                epd = epd3in52b.EPD()
                epd.init()

                epd.display(epd.getbuffer(dashboard_b), epd.getbuffer(dashboard_r))
                epd.sleep()
            else:
                dashboard_b.save("dashboard_b_preview.png")
                dashboard_r.save("dashboard_r_preview.png")


        except Exception as e:
            print(f"[DisplayManager] Refresh failed: {e}")


if __name__ == "__main__":
    DisplayManager.update_screen()
