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
        # --------------------------------------------------
        # 1. BLACK EPAPER LAYER
        # --------------------------------------------------
        fig_b, (ax_cpu, ax_tr_black) = plt.subplots(2, 1, figsize=(2.4, 3.2), dpi=150)

        if not cpu_df.empty:
            sns.lineplot(
                x="timestamp",
                y="reading",
                data=cpu_df,
                ax=ax_cpu,
                color='black',
                linewidth=2,
            )

        # Black Layer Traffic: Left Y-Axis for total_requests
        if not traffic_df.empty:
            total_req_df = traffic_df[traffic_df["Metric"] == "total_requests"]
            sns.lineplot(
                x="date",
                y="Value",
                data=total_req_df,
                ax=ax_tr_black,
                color="black",
                linewidth=2
            )
            # Create a twin secondary axis on the right side for visual scale matching
            ax_tr_twin_b = ax_tr_black.twinx()
            unique_df = traffic_df[traffic_df["Metric"] == "unique_visitors"]
            if not unique_df.empty:
                # Ghost plot to establish right y-axis scale on black layer
                ax_tr_twin_b.plot(unique_df["date"], unique_df["Value"], color="none")

            ax_tr_twin_b.tick_params(axis='y', labelsize=8, width=1.5)
            for label in ax_tr_twin_b.get_yticklabels():
                label.set_fontproperties(custom_font)

        for ax, title in [(ax_cpu, "ServePi CPU °C"), (ax_tr_black, "Traffic")]:
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

        # Capture positions and right-axis limits
        pos_cpu = ax_cpu.get_position()
        pos_tr = ax_tr_black.get_position()
        xlim_cpu, ylim_cpu = ax_cpu.get_xlim(), ax_cpu.get_ylim()
        xlim_tr = ax_tr_black.get_xlim()

        if not traffic_df.empty:
            ylim_tr_right = ax_tr_twin_b.get_ylim()
        else:
            ylim_tr_right = (0, 1)

        fig_b.savefig("layer_black.png", dpi=150, bbox_inches="tight")
        plt.close(fig_b)

        # --------------------------------------------------
        # 2. RED EPAPER LAYER
        # --------------------------------------------------
        fig_r, (ax_cpu_r, ax_tr_r_base) = plt.subplots(2, 1, figsize=(2.4, 3.2), dpi=150)
        ax_cpu_r.set_position(pos_cpu)
        ax_tr_r_base.set_position(pos_tr)

        # Match left axes
        ax_cpu_r.set_xlim(xlim_cpu);
        ax_cpu_r.set_ylim(ylim_cpu)
        ax_tr_r_base.set_xlim(xlim_tr)

        for ax_r in (ax_cpu_r, ax_tr_r_base):
            ax_r.spines['top'].set_visible(False)
            ax_r.spines['right'].set_visible(False)
            ax_r.spines['left'].set_color('white')
            ax_r.spines['bottom'].set_color('white')
            ax_r.tick_params(axis='both', colors='white')
            ax_r.set_xticklabels([])

        if not cpu_df.empty:
            high_temps = cpu_df[cpu_df["reading"] > 60]
            if not high_temps.empty:
                ax_cpu_r.scatter(high_temps["timestamp"], high_temps["reading"], color="black", s=20)

        # Red Layer Traffic: Right Y-Axis for unique_visitors
        if not traffic_df.empty:
            ax_tr_red = ax_tr_r_base.twinx()
            ax_tr_red.set_xlim(xlim_tr)
            ax_tr_red.set_ylim(ylim_tr_right)

            unique_df = traffic_df[traffic_df["Metric"] == "unique_visitors"]
            sns.lineplot(
                data=unique_df,
                x="date",
                y="Value",
                ax=ax_tr_red,
                color="black",  # Black on red layer = physical RED
                linewidth=2
            )

            # Hide spines and labels on red twin axis, keeping right tick labels visible in white for layout padding
            ax_tr_red.spines['top'].set_visible(False)
            ax_tr_red.spines['left'].set_visible(False)
            ax_tr_red.spines['bottom'].set_visible(False)
            ax_tr_red.spines['right'].set_color('white')
            ax_tr_red.tick_params(axis='y', colors='white')
            ax_tr_red.set_xlabel("")
            ax_tr_red.set_ylabel("")

        plt.tight_layout(rect=[0, 0.1, 1, 1])

        fig_r.text(0.05, 0.02, "BonsaiTree.wiki status:", fontproperties=custom_font, color="white")

        if site_status.lower() != "good":
            fig_r.text(0.68, 0.02, f"{site_status}", fontproperties=custom_font, color="black")
        else:
            fig_r.text(0.68, 0.02, "Good", fontproperties=custom_font, color="white")

        fig_r.savefig("layer_red.png", dpi=150, bbox_inches="tight")
        plt.close(fig_r)

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
