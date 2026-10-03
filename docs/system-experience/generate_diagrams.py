#!/usr/bin/env python3
"""Generate diagrams for the Grafana note.

Output: docs/system-experience/images/*.png (high-DPI PNGs)
Run:    venv/bin/python docs/system-experience/generate_diagrams.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT, exist_ok=True)

# ── Palette (matches the note CSS) ──
BG = "#f5faf6"
GREEN = "#2d7a4a"
GREEN_L = "#c8e6c9"
AMBER = "#e8a838"
AMBER_L = "#ffe9b8"
RED = "#dc3545"
RED_L = "#f8d0d4"
PURPLE = "#8e7cc3"
PURPLE_L = "#ded6f0"
TEXT = "#2d3a31"
MUTED = "#5a7a6a"

plt.rcParams.update({
    "font.family": ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "text.color": TEXT,
})


# ════════════════════════════════════════════════════
# 1. Alert lifecycle state machine
# ════════════════════════════════════════════════════
def alert_lifecycle():
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 11)
    ax.set_ylim(-0.85, 6.2)
    ax.axis("off")

    r = 0.95
    states = {
        "OK": (1.7, 3.2, GREEN, GREEN_L),
        "PENDING": (5.4, 3.2, AMBER, AMBER_L),
        "ALERTING": (9.0, 3.2, RED, RED_L),
        "NO DATA": (7.4, 0.3, PURPLE, PURPLE_L),
    }
    for name, (x, y, edge, face) in states.items():
        ax.add_patch(Circle((x, y), r, facecolor=face, edgecolor=edge, lw=2.2, zorder=3))
        ax.text(x, y, name, ha="center", va="center", fontsize=11,
                fontweight="bold", color=edge, zorder=4)

    def pt(name, angle_deg):
        x, y, _, _ = states[name]
        a = np.deg2rad(angle_deg)
        return np.array([x + r * np.cos(a), y + r * np.sin(a)])

    def curve(p0, p1, bend, color, ls="-", lw=1.6):
        """Quadratic Bezier with an explicit control point; returns its midpoint.
        bend > 0 offsets the control point toward the left of the travel direction."""
        d = p1 - p0
        n = np.array([-d[1], d[0]])
        n = n / np.hypot(*n)
        c = (p0 + p1) / 2 + bend * np.hypot(*d) * n
        ax.add_patch(PathPatch(
            Path([tuple(p0), tuple(c), tuple(p1)],
                 [Path.MOVETO, Path.CURVE3, Path.CURVE3]),
            fill=False, edgecolor=color, lw=lw, linestyle=ls, zorder=2))
        # arrow head, aligned with the curve tangent at the end point
        t = p1 - c
        t = t / np.hypot(*t)
        ax.add_patch(FancyArrowPatch(tuple(p1 - t * 0.05), tuple(p1),
                                     arrowstyle="-|>", mutation_scale=13,
                                     color=color, lw=lw, zorder=2,
                                     shrinkA=0, shrinkB=0))
        return (p0 + 2 * c + p1) / 4

    def edge_arrow(src, dst, out_deg, in_deg, **kw):
        return curve(pt(src, out_deg), pt(dst, in_deg), **kw)

    def label(pos, text, color=MUTED, off=(0.0, 0.0), fs=8.3):
        ax.text(pos[0] + off[0], pos[1] + off[1], text, ha="center", va="center",
                fontsize=fs, color=color, zorder=5,
                bbox=dict(boxstyle="round,pad=0.22", fc=BG, ec="none"))

    # START
    ax.annotate("", xy=tuple(pt("OK", 150)), xytext=(0.45, 4.15),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.6,
                                shrinkA=0, shrinkB=0, mutation_scale=13))
    ax.text(0.35, 4.28, "START", ha="left", va="bottom", fontsize=8.6,
            color=GREEN)

    label(edge_arrow("OK", "PENDING", 38, 142, bend=0.20, color=MUTED),
          "Rule TRUE (incl FOR)", GREEN, off=(0, 0.22))
    label(edge_arrow("PENDING", "ALERTING", 38, 142, bend=0.20, color=MUTED),
          "FOR satisfied", AMBER, off=(0, 0.22))
    label(edge_arrow("ALERTING", "PENDING", 112, 68, bend=-0.45, color=MUTED),
          "Rule TRUE (excl FOR)", RED, off=(0, 0.24))
    label(edge_arrow("PENDING", "OK", 218, 322, bend=0.22, color=MUTED),
          "FOR not satisfied", MUTED, off=(0, -0.20))
    label(edge_arrow("ALERTING", "OK", 236, 304, bend=0.30, color=MUTED),
          "Rule FALSE", MUTED, off=(0, -0.22))

    # 无数据：任一状态都会进入 NO DATA；恢复后回到 OK
    edge_arrow("PENDING", "NO DATA", 320, 118, bend=0.15,
               color=PURPLE, ls=(0, (4, 2)), lw=1.5)
    label((8.45, 1.42), "No data to evaluate rule（任一状态）", PURPLE)
    label(edge_arrow("NO DATA", "OK", 165, 292, bend=0.45,
                     color=PURPLE, ls=(0, (4, 2)), lw=1.5),
          "Data available to evaluate rule", PURPLE, off=(0, -0.45))

    ax.text(0.05, 6.0, "Grafana Alert 状态机（OK / PENDING / ALERTING / NO DATA）",
            fontsize=11.5, fontweight="bold", color="#1a4f2e", ha="left", va="top")

    fig.savefig(os.path.join(OUT, "alert-lifecycle.png"), dpi=200,
                facecolor=BG, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


# ════════════════════════════════════════════════════
# 2. Sampling resolution: spike visible vs. smoothed away
# ════════════════════════════════════════════════════
def sampling_resolution():
    rng = np.random.default_rng(7)
    step = 10                                     # 原始抓取间隔 10s
    span = 7 * 24 * 3600                          # 7 天原始数据
    t = np.arange(0, span, step)

    base = 30 + 6 * np.sin(2 * np.pi * t / 3600) + rng.normal(0, 0.8, t.size)
    spike_start = int(3 * 24 * 3600 / step / 2)   # 第 3.5 天
    spike_len = int(600 / step)                   # 持续 10 分钟的尖峰
    raw = base.copy()
    raw[spike_start:spike_start + spike_len] += 55

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), facecolor=BG)
    for ax in axes:
        ax.set_facecolor("#ffffff")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color("#c3dbcc")
        ax.spines["bottom"].set_color("#c3dbcc")
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.set_ylim(15, 95)
        ax.set_ylabel("CPU 使用率 (%)", fontsize=9, color=MUTED)

    # 左：1 小时窗口，100 点 → step = 36s
    t0 = spike_start * step
    m = (t >= t0 - 1500) & (t < t0 + 2100)
    xm = (t[m] - t0) / 60.0                        # 相对分钟，0 = spike 开始
    axes[0].plot(xm, raw[m], color="#9cc7a8", lw=1.2, label="原始 10s 数据")
    s36 = (t[m] - t0) % 36 == 0
    axes[0].plot(xm[s36], raw[m][s36], color=GREEN, lw=1.6,
                 marker="o", ms=2.6, label="36s 步长采点")
    axes[0].set_xlabel("相对时间（分钟）　1 小时窗口 / 100 点 → step = 36s",
                       fontsize=8.6, color=MUTED)
    axes[0].set_title("短时间范围：10 分钟 spike 清晰可见（峰值 ~90%）", fontsize=9.5,
                      color=GREEN, pad=8)
    axes[0].legend(fontsize=7.6, frameon=False, loc="upper right")
    axes[0].annotate("spike 持续 10 分钟", xy=(5, 89), xytext=(11, 62),
                     fontsize=8, color=RED,
                     arrowprops=dict(arrowstyle="-|>", color=RED, lw=1))

    # 右：7 天窗口，100 个点，step ≈ 1.68h，每桶取平均
    step_long = span / 100
    bins = np.arange(0, span + step_long, step_long)
    idx = np.digitize(t, bins)
    avg = np.array([raw[idx == i].mean() if np.any(idx == i) else np.nan
                    for i in range(1, len(bins))])
    xh = (bins[1:] - step_long / 2) / 3600
    axes[1].plot(xh, avg, color="#2a6e9e", lw=1.8, marker="o", ms=3,
                 label="每 1.68h 取 avg（100 个点）")
    axes[1].set_xlabel("小时　7 天窗口 / 100 点 → step ≈ 1.68h", fontsize=8.6,
                       color=MUTED)
    axes[1].set_title("长时间范围：同一 spike 被平均稀释，曲线变平滑", fontsize=9.5,
                      color="#2a6e9e", pad=8)
    axes[1].legend(fontsize=7.6, frameon=False, loc="upper right")
    peak_x = xh[np.nanargmax(avg)]
    peak_v = np.nanmax(avg)
    axes[1].annotate("峰值只剩 +%.1f 个百分点（原本 +55）" % (peak_v - 30),
                     xy=(peak_x, peak_v), xytext=(11, 58),
                     fontsize=8, color=RED,
                     arrowprops=dict(arrowstyle="-|>", color=RED, lw=1))

    fig.suptitle("Grafana 采点：图表是原始数据的有损采样视图", fontsize=11.5,
                 fontweight="bold", color="#1a4f2e", x=0.06, ha="left", y=1.03)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "sampling-resolution.png"), dpi=200,
                facecolor=BG, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


if __name__ == "__main__":
    alert_lifecycle()
    sampling_resolution()
    print("written to", OUT)
