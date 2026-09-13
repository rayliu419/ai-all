#!/usr/bin/env python3
"""Generate diagrams for the component-selection notes.

Output: docs/system-design/images/*.png (high-DPI PNGs)

Run:  venv/bin/python docs/system-design/generate_diagrams.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT, exist_ok=True)

# ── Palette (matches the note CSS) ──
BG = "#f5faf6"
CARD = "#e8f5ec"
BORDER = "#c3dbcc"
GREEN = "#2d7a4a"
GREEN_L = "#d4edda"
AMBER = "#e8a838"
AMBER_L = "#fff3e0"
RED = "#dc3545"
BLUE = "#2a6e9e"
BLUE_L = "#e3f2fd"
GREY = "#d8e3dc"
TEXT = "#2d3a31"
MUTED = "#5a7a6a"

plt.rcParams.update({
    "font.family": ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "text.color": TEXT,
})


# ════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════
def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, label, fc=CARD, ec=BORDER, tc=TEXT, fs=9,
        weight="normal", lw=1.2, radius=0.06, zorder=2, lsp=1.45):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, color=tc, fontweight=weight, zorder=zorder + 1,
            linespacing=lsp)


def arrow(ax, x1, y1, x2, y2, color=GREEN, lw=1.4, ls="-", rad=0.0, zorder=4):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
        color=color, lw=lw, linestyle=ls, zorder=zorder,
        connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1))


def note(ax, x, y, text, fs=8.5, color=MUTED, ha="left", va="center", style="italic"):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va=va, style=style,
            linespacing=1.5)


def title(ax, y, text, fs=13):
    ax.text(0, y, text, fontsize=fs, color="#1a4f2e", fontweight="bold",
            ha="left", va="center")


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    print(f"wrote {path}")


# ════════════════════════════════════════════════════
# 1. cache-layers.png — 缓存放在哪里
# ════════════════════════════════════════════════════
def fig_cache_layers():
    fig, ax = canvas(7.2, 5.7, (0, 7.0), (0, 6.05))
    title(ax, 5.82, "缓存放在哪里：四个层次 + 事实来源")

    C1, C2, C3 = 0.25, 3.25, 4.75
    for x, label in ((C2, "典型延迟"), (C3, "失效范围 / 一致性代价")):
        ax.text(x, 5.40, label, fontsize=8.5, color="#1a4f2e",
                fontweight="bold", ha="left", va="center")
    ax.plot([C1, 6.60], [5.16, 5.16], color=BORDER, lw=1.0, zorder=1)

    rows = [
        ("① 浏览器 HTTP 缓存", "< 1 ms（本地）", "只影响该用户；由 Cache-Control 决定", CARD, BORDER),
        ("② CDN 边缘缓存", "10–50 ms", "影响整个区域用户；回源风暴风险", CARD, BORDER),
        ("③ 应用本地缓存\nCaffeine / Guava", "< 1 ms", "每实例一份；更新需广播或极短 TTL", AMBER_L, AMBER),
        ("④ 分布式缓存\nRedis / Memcached", "0.5–2 ms", "全局共享视图；故障影响面最大", BLUE_L, BLUE),
        ("⑤ 数据库（事实来源）", "5–50 ms+", "—", GREY, "#9fb3a8"),
    ]

    y_top, step, h, bw = 4.38, 0.80, 0.68, 2.80
    for i, (name, lat, cost, fc, ec) in enumerate(rows):
        y = y_top - i * step
        box(ax, C1, y, bw, h, name, fc=fc, ec=ec, fs=8.5, lsp=1.2,
            weight="bold" if i >= 3 else "normal")
        ax.text(C2, y + h / 2, lat, fontsize=8.5, color=TEXT, ha="left", va="center")
        ax.text(C3, y + h / 2, cost, fontsize=8.5, color=MUTED, ha="left", va="center")
        if i < len(rows) - 1:
            arrow(ax, C1 + bw / 2, y - 0.02, C1 + bw / 2, y - step + h + 0.02)

    note(ax, C1, 0.85, "读路径自上而下逐层查找，命中即返回；越往下延迟越高、一致性越强、失效越贵。")
    save(fig, "cache-layers.png")


# ════════════════════════════════════════════════════
# 2. cache-read-paths.png — Cache-Aside vs Read-Through
# ════════════════════════════════════════════════════
def lifelines(ax, actors, xs, top, bottom, h=0.6):
    for name, x in zip(actors, xs):
        box(ax, x - 1.0, top, 2.0, h, name, fs=8.5, weight="bold")
        ax.plot([x, x], [bottom, top], color=BORDER, lw=1.0, ls=(0, (4, 3)), zorder=1)


def fig_cache_read_paths():
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.9), facecolor=BG)
    for ax in axes:
        ax.set_facecolor(BG)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 6)
        ax.axis("off")

    # ---- A. Cache-Aside（旁路缓存）----
    ax = axes[0]
    ax.text(0, 5.75, "A. Cache-Aside（旁路缓存）", fontsize=11.5,
            color="#1a4f2e", fontweight="bold", ha="left", va="center")
    lifelines(ax, ["应用", "缓存", "数据库"], [2.0, 6.0, 10.0], 4.85, 0.6)

    arrow(ax, 2.0, 4.35, 6.0, 4.35, color=BLUE)
    ax.text(4.0, 4.5, "① GET key", fontsize=8, color=BLUE, ha="center")
    arrow(ax, 6.0, 3.85, 2.0, 3.85, color=RED)
    ax.text(4.0, 4.0, "② miss", fontsize=8, color=RED, ha="center")
    arrow(ax, 2.0, 3.25, 10.0, 3.25, color=GREEN)
    ax.text(6.0, 3.4, "③ 回源查询（应用自己发起）", fontsize=8, color=GREEN, ha="center")
    arrow(ax, 10.0, 2.65, 2.0, 2.65, color=GREEN)
    ax.text(6.0, 2.8, "④ 结果", fontsize=8, color=GREEN, ha="center")
    arrow(ax, 2.0, 2.05, 6.0, 2.05, color=BLUE)
    ax.text(4.0, 2.2, "⑤ SET key（写回缓存）", fontsize=8, color=BLUE, ha="center")
    note(ax, 0.2, 1.2, "应用要写两段逻辑；缓存故障时可降级为直连 DB。")

    # ---- B. Read-Through（读穿透）----
    ax = axes[1]
    ax.text(0, 5.75, "B. Read-Through（读穿透）", fontsize=11.5,
            color="#1a4f2e", fontweight="bold", ha="left", va="center")
    lifelines(ax, ["应用", "缓存", "数据库"], [2.0, 6.0, 10.0], 4.85, 0.6)

    arrow(ax, 2.0, 4.35, 6.0, 4.35, color=BLUE)
    ax.text(4.0, 4.5, "① GET key", fontsize=8, color=BLUE, ha="center")
    arrow(ax, 6.0, 3.75, 10.0, 3.75, color=GREEN)
    ax.text(8.0, 3.9, "② 缓存回源", fontsize=8, color=GREEN, ha="center")
    arrow(ax, 10.0, 3.05, 6.0, 3.05, color=GREEN)
    ax.text(8.0, 3.2, "③ 结果", fontsize=8, color=GREEN, ha="center")
    arrow(ax, 6.0, 2.35, 2.0, 2.35, color=BLUE)
    ax.text(4.0, 2.5, "④ 结果（应用不感知回源）", fontsize=8, color=BLUE, ha="center")
    note(ax, 0.2, 1.4, "应用只有一段逻辑；回源策略由缓存层统一实现（如 Redis 客户端 / 代理）。")
    note(ax, 0.2, 1.0, "写侧对应 Write-Through（同步写穿）与 Write-Behind（异步回写）。")

    fig.subplots_adjust(wspace=0.05)
    save(fig, "cache-read-paths.png")


# ════════════════════════════════════════════════════
# 3. row-vs-column-store.png — 行存 vs 列存读取 I/O
# ════════════════════════════════════════════════════
def fig_row_vs_column_store():
    cols, rows = 5, 4
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 6.4), facecolor=BG,
                             gridspec_kw={"height_ratios": [1.15, 1.0]})
    for ax in axes.ravel():
        ax.set_facecolor(BG)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 6)
        ax.axis("off")

    X0, XMAX, GAP = 1.6, 11.9, 0.25

    def draw_table(ax, cx, cy, cw, ch, highlight_col=2):
        for c in range(cols):
            for r in range(rows):
                needed = (c == highlight_col)
                ax.add_patch(Rectangle((cx + c * cw, cy - (r + 1) * ch), cw, ch,
                                       facecolor=GREEN_L if needed else "#ffffff",
                                       edgecolor=BORDER, lw=0.9, zorder=2))
        for c in range(cols):
            ax.text(cx + (c + 0.5) * cw, cy + 0.22, f"c{c+1}", fontsize=8,
                    color=GREEN if c == highlight_col else MUTED, ha="center",
                    fontweight="bold" if c == highlight_col else "normal")
        for r in range(rows):
            ax.text(cx - 0.28, cy - (r + 0.5) * ch, f"r{r+1}", fontsize=8,
                    color=MUTED, ha="right", va="center")

    def draw_pages_row(ax, y):
        """行存：每页一整行"""
        pw = (XMAX - X0 - (rows - 1) * GAP) / rows
        ph = 0.55
        for i in range(rows):
            x = X0 + i * (pw + GAP)
            ax.add_patch(Rectangle((x, y), pw, ph, facecolor=AMBER_L,
                                   edgecolor=AMBER, lw=1.1, zorder=2))
            slot = pw / cols
            for c in range(cols):
                ax.add_patch(Rectangle((x + c * slot, y), slot, ph,
                                       facecolor=GREEN if c == 2 else "none",
                                       edgecolor=BORDER, lw=0.7, zorder=3))
            ax.text(x + pw / 2, y - 0.28, f"页{i+1}（整行 r{i+1}）", fontsize=7.5,
                    color=MUTED, ha="center", va="top")
        ax.text(0.15, y + ph + 0.30, "磁盘布局：行优先", fontsize=9,
                color="#1a4f2e", fontweight="bold")
        ax.text(0.15, 1.15, "读取 I/O：4 / 4 页 —— 每页只有 1/5 是有用列",
                fontsize=8.5, color=RED)

    def draw_pages_col(ax, y):
        """列存：每页一整列"""
        pw = (XMAX - X0 - (cols - 1) * GAP) / cols
        ph = 0.85
        for c in range(cols):
            x = X0 + c * (pw + GAP)
            fc = GREEN_L if c == 2 else "#ffffff"
            ec = GREEN if c == 2 else BORDER
            ax.add_patch(Rectangle((x, y), pw, ph, facecolor=fc, edgecolor=ec,
                                   lw=1.4 if c == 2 else 1.0, zorder=2))
            ax.text(x + pw / 2, y + ph / 2, f"c{c+1}\n×{rows}", fontsize=8,
                    color=GREEN if c == 2 else MUTED, ha="center", va="center",
                    fontweight="bold" if c == 2 else "normal")
        ax.text(0.15, y + ph + 0.30, "磁盘布局：列优先", fontsize=9,
                color="#1a4f2e", fontweight="bold")
        ax.text(0.15, 1.15, "读取 I/O：1 / 5 页 —— 整页都是有用数据",
                fontsize=8.5, color=GREEN)

    # 行存
    ax = axes[0][0]
    ax.text(0, 5.70, "A. 行存（row-oriented）", fontsize=11.5, color="#1a4f2e",
            fontweight="bold", ha="left", va="center")
    ax.text(11.9, 5.70, "查询：AVG(c3) —— 需要所有行的 c3", fontsize=8.5,
            color=GREEN, ha="right", va="center", fontweight="bold")
    draw_table(ax, 2.6, 5.00, 0.65, 0.42)
    draw_pages_row(ax, 2.10)

    # 列存
    ax = axes[0][1]
    ax.text(0, 5.70, "B. 列存（column-oriented）", fontsize=11.5, color="#1a4f2e",
            fontweight="bold", ha="left", va="center")
    ax.text(11.9, 5.70, "查询：AVG(c3) —— 需要所有行的 c3", fontsize=8.5,
            color=GREEN, ha="right", va="center", fontweight="bold")
    draw_table(ax, 2.6, 5.00, 0.65, 0.42)
    draw_pages_col(ax, 1.95)

    # 底部：两条结论
    ax = axes[1][0]
    ax.axis("off")
    ax.text(0, 5.4, "为什么行存不适合分析查询", fontsize=10.5, color="#1a4f2e",
            fontweight="bold", ha="left", va="center")
    for i, t in enumerate([
        "• 必须把整页读进内存，再过滤出需要的列 → 内存与 I/O 双重浪费",
        "• 列值类型相同、排列紧密 → 压缩率远高于行存",
        "• 顺序读取同一列 → 顺序 I/O，缓存局部性远好于跳着读",
        "• 假设：每行 / 每列各占一个磁盘页；实际还会按 batch 组织",
    ]):
        ax.text(0.1, 4.6 - i * 0.75, t, fontsize=8.5, color=TEXT, ha="left", va="center")

    ax = axes[1][1]
    ax.axis("off")
    ax.text(0, 5.4, "列存的代价", fontsize=10.5, color="#1a4f2e",
            fontweight="bold", ha="left", va="center")
    for i, t in enumerate([
        "• 点查（取整行）需要拼接多个列文件，反而更慢",
        "• B+Tree 实现的列存插入困难：中间插一行要重写列文件",
        "• 因此列存多用 LSM 结构（ClickHouse MergeTree 等）",
        "• 各列必须保持同一行序，否则无法还原完整记录",
    ]):
        ax.text(0.1, 4.6 - i * 0.75, t, fontsize=8.5, color=TEXT, ha="left", va="center")

    fig.subplots_adjust(hspace=0.05, wspace=0.12)
    save(fig, "row-vs-column-store.png")


# ════════════════════════════════════════════════════
# 4. oltp-vs-olap.png — 负载特征对比
# ════════════════════════════════════════════════════
def fig_oltp_vs_olap():
    fig, ax = canvas(10.4, 5.6, (0, 10.4), (0, 6.2))
    title(ax, 5.9, "OLTP 与 OLAP 的负载特征差异（等级为定性示意）")

    dims = [
        ("单请求扫描行数", 1, 4, "几十行", "千万 ~ 亿行"),
        ("并发请求数", 4, 1, "高（数千 QPS）", "低（少量报表）"),
        ("延迟要求", 4, 1, "ms 级", "秒 ~ 分钟级"),
        ("写入模式", 3, 2, "单行小事务", "批量导入 / 追加"),
        ("事务需求", 4, 1, "强 ACID", "弱 / 无需事务"),
        ("主要索引", 2, 4, "B+Tree 点查", "分区裁剪 + 列存"),
    ]
    x0, span, bh = 2.9, 3.4, 0.26
    for i, (name, l_oltp, l_olap, t_oltp, t_olap) in enumerate(dims):
        y = 5.0 - i * 0.82
        ax.text(0.05, y + 0.14, name, fontsize=9, color=TEXT, ha="left",
                va="center", fontweight="bold")

        ax.add_patch(Rectangle((x0, y + 0.14), span * l_oltp / 4, bh,
                               facecolor=GREEN_L, edgecolor=GREEN, lw=1.0, zorder=2))
        ax.text(x0 + span * l_oltp / 4 + 0.15, y + 0.14 + bh / 2, t_oltp,
                fontsize=8, color=GREEN, ha="left", va="center")

        ax.add_patch(Rectangle((x0, y - 0.34), span * l_olap / 4, bh,
                               facecolor=AMBER_L, edgecolor=AMBER, lw=1.0, zorder=2))
        ax.text(x0 + span * l_olap / 4 + 0.15, y - 0.34 + bh / 2, t_olap,
                fontsize=8, color="#a8791a", ha="left", va="center")

    ax.add_patch(Rectangle((0.05, 0.28), 0.35, 0.24, facecolor=GREEN_L,
                           edgecolor=GREEN, lw=1.0))
    ax.text(0.5, 0.40, "OLTP（业务库）", fontsize=8.5, color=GREEN, va="center")
    ax.add_patch(Rectangle((2.6, 0.28), 0.35, 0.24, facecolor=AMBER_L,
                           edgecolor=AMBER, lw=1.0))
    ax.text(3.05, 0.40, "OLAP（分析库 / 数据仓库）", fontsize=8.5,
            color="#a8791a", va="center")
    save(fig, "oltp-vs-olap.png")


# ════════════════════════════════════════════════════
# 5. lsm-vs-btree.png — 写入路径
# ════════════════════════════════════════════════════
def fig_lsm_vs_btree():
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.4), facecolor=BG)
    for ax in axes:
        ax.set_facecolor(BG)
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 6)
        ax.axis("off")

    # ---- A. B-Tree ----
    ax = axes[0]
    ax.text(0, 5.7, "A. B+Tree：原地更新", fontsize=11.5, color="#1a4f2e",
            fontweight="bold", ha="left", va="center")
    box(ax, 4.6, 4.55, 2.8, 0.7, "根页", fs=9, weight="bold")
    box(ax, 1.6, 3.35, 2.8, 0.7, "内部页", fs=9)
    box(ax, 7.6, 3.35, 2.8, 0.7, "内部页", fs=9)
    for i, x in enumerate((0.5, 2.9, 5.3, 7.7, 10.1)):
        fc = GREEN_L if i == 2 else "#ffffff"
        ec = GREEN if i == 2 else BORDER
        box(ax, x, 2.05, 1.6, 0.7, f"叶{i+1}", fs=8.5, fc=fc, ec=ec)
    arrow(ax, 6.0, 4.53, 3.0, 4.07)
    arrow(ax, 6.0, 4.53, 9.0, 4.07)
    for x1, x2 in ((3.0, 1.3), (3.0, 3.7), (9.0, 6.1), (9.0, 8.5), (9.0, 10.9)):
        arrow(ax, x1, 3.33, x2, 2.77, lw=1.0)
    ax.text(6.0, 1.72, "① 定位叶页 → ② 页内改写 → ③ 满则页分裂",
            fontsize=8.5, color=GREEN, ha="center", va="center")
    for i, t in enumerate([
        "• 原地更新：随机 I/O，页分裂带来额外写",
        "• 读放大低：树高固定，点查 2~4 次页读",
        "• 写放大小（1 次逻辑写 ≈ 1 次物理写）",
        "• 天然支持范围查询与事务（InnoDB、PostgreSQL）",
    ]):
        ax.text(0.05, 1.25 - i * 0.3, t, fontsize=8.3, color=TEXT, ha="left", va="center")

    # ---- B. LSM-Tree ----
    ax = axes[1]
    ax.text(0, 5.7, "B. LSM-Tree：追加写 + 后台 compaction", fontsize=11.5,
            color="#1a4f2e", fontweight="bold", ha="left", va="center")
    box(ax, 0.5, 4.6, 2.9, 0.7, "MemTable\n内存，有序", fs=8.5, fc=BLUE_L, ec=BLUE)
    box(ax, 3.9, 4.6, 2.9, 0.7, "Immutable\nMemTable", fs=8.5, fc=BLUE_L, ec=BLUE)
    arrow(ax, 3.45, 4.95, 3.85, 4.95)
    box(ax, 7.3, 4.6, 2.4, 0.7, "WAL（先落盘）", fs=8.5, fc=GREY, ec="#9fb3a8")
    ax.text(7.3, 5.45, "① 写入只追加到日志 / 内存", fontsize=8.3, color=GREEN,
            ha="left", va="center")
    arrow(ax, 5.5, 4.58, 8.0, 3.85)
    ax.text(8.2, 4.12, "② 刷盘为不可变 SSTable", fontsize=8.3, color=GREEN,
            ha="left", va="center")
    for i, x in enumerate((6.9, 8.4, 9.9)):
        box(ax, x, 3.0, 1.35, 0.65, f"L0\nSST{i + 1}", fs=7.5, fc=AMBER_L, ec=AMBER)
    arrow(ax, 8.5, 2.98, 8.5, 2.32)
    box(ax, 6.9, 1.65, 1.7, 0.65, "L1 SSTable", fs=7.5, fc="#ffffff")
    box(ax, 8.8, 1.65, 1.9, 0.65, "L1 SSTable", fs=7.5, fc="#ffffff")
    ax.text(6.9, 1.35, "③ compaction：合并 + 去重 + 删除墓碑", fontsize=8.3,
            color=GREEN, ha="left", va="center")
    for i, t in enumerate([
        "• 写放大高：同一份数据在多层之间被反复重写",
        "• 读放大高：一次读要查 MemTable + 多个 SSTable",
        "• 空间放大：可通过层数与 compaction 策略调节",
        "• 全顺序写、吞吐高 → 写密集（HBase、Cassandra、ClickHouse）",
    ]):
        ax.text(0.05, 0.98 - i * 0.3, t, fontsize=8.3, color=TEXT, ha="left", va="center")

    fig.subplots_adjust(wspace=0.06)
    save(fig, "lsm-vs-btree.png")


# ════════════════════════════════════════════════════
# 6. batch-vs-stream.png — 批 vs 流的时间轴
# ════════════════════════════════════════════════════
def fig_batch_vs_stream():
    fig, ax = canvas(11.6, 5.2, (0, 12), (0, 6))
    title(ax, 5.75, "同一份事件流：批处理与流处理的可见延迟")

    hours = 6
    ax.plot([0.8, 11.6], [4.35, 4.35], color=BORDER, lw=1.0)
    ax.text(0.05, 4.35, "事件产生", fontsize=9, color=TEXT, ha="left",
            va="center", fontweight="bold")
    rng = [0.15, 0.55, 0.75, 1.35, 1.85, 2.15, 2.6, 3.15, 3.55, 4.2,
           4.75, 5.1, 5.6, 6.05, 6.5, 7.1, 7.55, 8.2, 8.6, 9.1, 9.6, 10.2, 10.9]
    for h in rng:
        x = 0.8 + h
        ax.plot([x, x], [4.15, 4.55], color=GREEN, lw=1.2)
        ax.plot(x, 4.15, marker="o", ms=3.2, color=GREEN)

    # 批处理
    for i in range(hours):
        x = 0.8 + i * (10.8 / hours)
        w = 10.8 / hours - 0.12
        ax.add_patch(Rectangle((x, 2.85), w, 0.55, facecolor=AMBER_L,
                               edgecolor=AMBER, lw=1.1, zorder=2))
        ax.text(x + w / 2, 3.12, f"窗口 {i+1}", fontsize=7.5, color="#a8791a",
                ha="center", va="center")
        ax.plot([x + w, x + w], [2.7, 3.0], color=AMBER, lw=1.0)
        ax.plot(x + w, 2.7, marker="v", ms=5, color=AMBER)
    ax.text(0.05, 3.12, "批处理", fontsize=9, color="#a8791a", ha="left",
            va="center", fontweight="bold")
    note(ax, 0.8, 2.35, "结果在窗口关闭后才可见：小时级（日切任务则是 T+1，延迟 小时 ~ 天级）",
         color="#a8791a", fs=8.5, style="normal")

    # 流处理
    for h in rng:
        x = 0.8 + h
        ax.plot([x, x], [1.45, 1.75], color=BLUE, lw=1.0, ls=(0, (2, 1.5)))
        ax.plot(x, 1.45, marker="o", ms=3.2, markerfacecolor="none",
                markeredgecolor=BLUE, markeredgewidth=1.1)
    ax.plot([0.8, 11.6], [1.45, 1.45], color=BORDER, lw=1.0)
    ax.text(0.05, 1.6, "流处理", fontsize=9, color=BLUE, ha="left",
            va="center", fontweight="bold")
    note(ax, 0.8, 1.0, "事件到达即处理：延迟 秒级 ~ 亚秒级（受窗口 / 水位线策略影响）",
         color=BLUE, fs=8.5, style="normal")

    arrow(ax, 0.8, 0.25, 11.6, 0.25, color=MUTED, lw=1.0)
    for h in range(hours + 1):
        x = 0.8 + h * (10.8 / hours)
        ax.plot([x, x], [0.18, 0.32], color=MUTED, lw=1.0)
        ax.text(x, 0.02, f"{h}h", fontsize=7.5, color=MUTED, ha="center", va="center")
    note(ax, 6.2, 0.66, "批处理延迟 = 窗口长度；流处理延迟 = 事件在内存中的滞留时间",
         fs=8.5, ha="center")
    save(fig, "batch-vs-stream.png")


if __name__ == "__main__":
    fig_cache_layers()
    fig_cache_read_paths()
    fig_row_vs_column_store()
    fig_oltp_vs_olap()
    fig_lsm_vs_btree()
    fig_batch_vs_stream()
    print("done.")
