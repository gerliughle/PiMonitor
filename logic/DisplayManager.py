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
    WIDTH = 240
    HEIGHT = 360

    def __init__(self, db_connection=None):
        self.db = db_connection


    @staticmethod
    def generate_layered_dashboard(cpu_df, traffic_df, site_status="Good"):
        # BLACK EPAPER LAYER
        # Contains CPU Graph, Traffic Graph, Status text, and status if good.

        fig_b, (ax_cpu, ax_tr) = plt.subplots(2,1, figsize=(2.4, 3.2), dpi=150)

        if not cpu_df.empty:
            sns.lineplot(
                x="timestamp",
                y="reading",
                data=cpu_df,
                ax=ax_cpu,
                color='black',
                linewidth=2,
            )
        if not traffic_df.empty:
            sns.lineplot(
                x="date",
                y="Value",
                hue="Metric",
                style="Metric",
                data=traffic_df,
                ax=ax_tr,
                palette=["black", "black"],
                linewidth=2
            )
            ax_tr.get_legend().remove()

        for ax, title in [(ax_cpu, "ServePi CPU °C"), (ax_tr, "Traffic")]:
            ax.set_title(title, fontproperties=title_font, loc="left")
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.set_xticklabels([])
            ax.tick_params(axis='y', labelsize=8, width=1.5)
            for label in ax.get_yticklabels():
                label.set_fontproperties(custom_font)
            sns.despine(ax=ax)

        plt.tight_layout(rect=[0, 0.1, 1, 1])

        fig_b.text(0.05, 0.02, "BonsaiTree.wiki status:", fontproperties=custom_font)
        if site_status.lower() == "good":
            fig_b.text(0.68, 0.02, "Good", fontproperties=custom_font)
        fig_b.savefig("layer_black.png", dpi=150, bbox_inches="tight")
        plt.close(fig_b)

        # Red Layer
        # Contains cpu temp if high and site status if not good
        fig_r, (ax_cpu_r, ax_tr_r) = plt.subplots(2,1, figsize=(2.4, 3.2), dpi=150)


        if not cpu_df.empty:
            high_temps = cpu_df[cpu_df["reading"] > 60]
            if not high_temps.empty:
                ax_cpu_r.set_xlim(ax_cpu.get_xlim())
                ax_cpu_r.set_ylim(ax_cpu.get_ylim())
                ax_cpu_r.scatter(high_temps["timestamp"], high_temps["reading"], color="black", s=20)

        if not traffic_df.empty:
            unique_df = traffic_df[traffic_df["Metric"] == "unique_visitors"]
            ax_tr_r.set_xlim(ax.get_xlim())
            ax_tr_r.set_ylim(ax.get_ylim())
            sns.lineplot(
                data=unique_df,
                x="date",
                y="Value",
                ax=ax_tr_r,
                color="black",
                linewidth=2
            )

        for ax in (ax_cpu_r, ax_tr_r):
            ax.axis("off")

        if site_status.lower() != "good":
            fig_r.text(0.68, 0.02, f"{site_status}", fontproperties=custom_font, color="black")

        plt.tight_layout(rect=[0, 0.1, 1, 1])
        fig_r.savefig("layer_red.png", dpi=150, bbox_inches="tight")
        plt.close(fig_r)
        print("Dashboard images generated.")

    @classmethod
    def update_screen(cls):
        try:
            cpu_df = SystemMonitor.get_df()
            traffic_df = SiteMonitor.get_df()
            site_status = SiteMonitor.get_status()
            cls.generate_layered_dashboard(cpu_df, traffic_df, site_status="Good")

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
