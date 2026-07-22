#!/usr/bin/env python3
"""Generate professional ML-basis diagrams using matplotlib/seaborn.

Output: notes/llm-basis/images/*.png (high-DPI PNGs)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

OUT = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(OUT, exist_ok=True)

# ── Global style ──
sns.set_theme(style="whitegrid", palette="muted", font=["PingFang SC", "sans-serif"])
BG = "#f5faf6"
GREEN = "#2d7a4a"
AMBER = "#e8a838"
RED = "#dc3545"
TEXT = "#2d3a31"


# ════════════════════════════════════════════════════
# 1. Confusion Matrix (heatmap)
# ════════════════════════════════════════════════════
def plot_confusion_matrix():
    cm = np.array([[48, 98], [25, 229]])
    annot = [["TP = 48\nTrue Positive\nY 真阳", "FN = 98\nFalse Negative\nN 假阴"],
             ["FP = 25\nFalse Positive\nN 假阳", "TN = 229\nTrue Negative\nY 真阴"]]

    fig, ax = plt.subplots(figsize=(5, 4.5), facecolor=BG)
    ax.set_facecolor(BG)

    cmap = matplotlib.colors.ListedColormap(
        sns.color_palette(["#d4edda", "#f8d7da", "#ffeeba", "#d4edda"], as_cmap=False))

    sns.heatmap(cm, annot=np.array(annot), fmt="", cmap=cmap,
                linewidths=2, linecolor="white", cbar=False,
                xticklabels=["Predict Positive (1)", "Predict Negative (0)"],
                yticklabels=["Actual Positive (1)", "Actual Negative (0)"],
                ax=ax, annot_kws={"fontsize": 11, "fontweight": "bold"})

    ax.set_title("Confusion Matrix — 混淆矩阵", fontsize=15, fontweight="bold", color=TEXT, pad=14)
    ax.set_xlabel("Predicted Label", fontsize=12, color=TEXT)
    ax.set_ylabel("Actual Label", fontsize=12, color=TEXT, rotation=0, labelpad=14)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

    acc = (48 + 229) / 400 * 100
    fig.text(0.5, 0.01, f"Overall Accuracy = (48 + 229) / 400 = {acc:.2f}%",
             ha="center", fontsize=11, color=TEXT, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.4", fc="#e8f5ec", ec="#c3dbcc"))

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.savefig(os.path.join(OUT, "confusion-matrix.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ confusion-matrix.png")


# ════════════════════════════════════════════════════
# 2. ROC Curve
# ════════════════════════════════════════════════════
def plot_roc_curve():
    np.random.seed(42)
    n = 200
    scores = np.clip(np.concatenate([
        np.random.normal(0.6, 0.25, n // 2),
        np.random.normal(0.3, 0.25, n // 2)]), 0, 1)
    labels = np.concatenate([np.ones(n // 2), np.zeros(n // 2)])

    thresholds = np.linspace(0, 1, 200)
    tprs, fprs = [], []
    for t in thresholds:
        tp = np.sum((scores >= t) & (labels == 1))
        fn = np.sum((scores < t) & (labels == 1))
        fp = np.sum((scores >= t) & (labels == 0))
        tn = np.sum((scores < t) & (labels == 0))
        tprs.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
        fprs.append(fp / (fp + tn) if (fp + tn) > 0 else 0)

    auc_val = np.trapezoid(tprs, fprs)

    fig, ax = plt.subplots(figsize=(6, 5.5), facecolor=BG)
    ax.set_facecolor(BG)

    ax.fill_between(fprs, tprs, alpha=0.15, color=GREEN, label=f"AUC = {auc_val:.3f}")
    ax.plot(fprs, tprs, color=GREEN, lw=2.5, label="ROC Curve")
    ax.plot([0, 1], [0, 1], "k--", lw=1.2, alpha=0.5, label="Random (AUC=0.5)")

    idx = np.argmax(np.array(tprs) - np.array(fprs))
    ax.scatter(fprs[idx], tprs[idx], color=RED, s=80, zorder=5, label="Best Threshold")
    ax.annotate("Best Threshold\nTPR↑ FPR↓",
                xy=(fprs[idx], tprs[idx]), xytext=(fprs[idx] + 0.2, tprs[idx] - 0.15),
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
                fontsize=10, color=RED, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RED, alpha=0.8))

    ax.set_xlabel("False Positive Rate (FPR)", fontsize=12, color=TEXT)
    ax.set_ylabel("True Positive Rate (TPR)", fontsize=12, color=TEXT)
    ax.set_title("ROC Curve — 受试者工作特征曲线", fontsize=15, fontweight="bold", color=TEXT, pad=12)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "roc-curve.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ roc-curve.png")


# ════════════════════════════════════════════════════
# 3. PR Curve
# ════════════════════════════════════════════════════
def plot_pr_curve():
    recall = np.linspace(0.01, 1, 200)
    prec_con = 0.95 / (1 + np.exp(5 * (recall - 0.35)))
    prec_greedy = 0.7 / (1 + np.exp(3 * (recall - 0.65)))
    eps = 1e-10
    f1_con = 2 * prec_con * recall / (prec_con + recall + eps)
    f1_greedy = 2 * prec_greedy * recall / (prec_greedy + recall + eps)
    idx_con = np.argmax(f1_con)
    idx_greedy = np.argmax(f1_greedy)

    fig, ax = plt.subplots(figsize=(6, 5.5), facecolor=BG)
    ax.set_facecolor(BG)

    ax.plot(recall, prec_con, color=GREEN, lw=2.5, label="Conservative Model A (Precision↑)")
    ax.plot(recall, prec_greedy, color=AMBER, lw=2.5, ls="--", label="Greedy Model B (Recall↑)")
    ax.axhline(y=0.5, color="gray", lw=1, ls=":", alpha=0.5, label="Random Baseline")

    ax.scatter(recall[idx_con], prec_con[idx_con], color=GREEN, s=80, zorder=5)
    ax.annotate(f"F1={f1_con[idx_con]:.2f}",
                xy=(recall[idx_con], prec_con[idx_con]),
                xytext=(recall[idx_con] + 0.12, prec_con[idx_con] - 0.08),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.2),
                fontsize=10, color=GREEN, fontweight="bold")

    ax.scatter(recall[idx_greedy], prec_greedy[idx_greedy], color=AMBER, s=80, zorder=5)
    ax.annotate(f"F1={f1_greedy[idx_greedy]:.2f}",
                xy=(recall[idx_greedy], prec_greedy[idx_greedy]),
                xytext=(recall[idx_greedy] + 0.12, prec_greedy[idx_greedy] - 0.08),
                arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.2),
                fontsize=10, color=AMBER, fontweight="bold")

    ax.set_xlabel("Recall (覆盖率)", fontsize=12, color=TEXT)
    ax.set_ylabel("Precision (精确率)", fontsize=12, color=TEXT)
    ax.set_title("Precision-Recall Curve — PR 曲线", fontsize=15, fontweight="bold", color=TEXT, pad=12)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "pr-curve.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ pr-curve.png")


# ════════════════════════════════════════════════════
# 4. Bias-Variance Bullseye
# ════════════════════════════════════════════════════
def plot_bias_variance():
    fig, axes = plt.subplots(2, 2, figsize=(8, 8), facecolor=BG)
    titles = [
        ("★ Ideal\nLow Bias + Low Variance", GREEN),
        ("Overfitting (High Variance)\nLow Bias + High Variance", AMBER),
        ("Underfitting (High Bias)\nHigh Bias + Low Variance", AMBER),
        ("Worst Case\nHigh Bias + High Variance", RED),
    ]
    patterns = [(0, 0, 0.08), (0, 0, 0.35), (0.4, 0.4, 0.08), (0.4, 0.4, 0.35)]
    status_texts = [
        "Y Accurate & Stable\n训练 & 测试误差都低",
        "Y Avg correct but volatile\n训练误差低，测试误差高",
        "X Consistently off-target\n训练 & 测试误差都高",
        "X Off-target & volatile\n最差情况",
    ]

    for idx, (ax, (title, color), (cx, cy, spread), status) in enumerate(
            zip(axes.flat, titles, patterns, status_texts)):
        ax.set_facecolor(BG)
        for r in [0.7, 0.5, 0.3, 0.1]:
            circle = plt.Circle((0, 0), r, fill=False, edgecolor="#c3dbcc", lw=1.2, zorder=1)
            ax.add_patch(circle)
        ax.axhline(0, color=TEXT, lw=1.5, zorder=2)
        ax.axvline(0, color=TEXT, lw=1.5, zorder=2)
        center = plt.Circle((0, 0), 0.03, color=RED, zorder=3)
        ax.add_patch(center)

        np.random.seed(idx * 10 + 5)
        n_hits = 30
        xs = np.random.normal(cx, spread, n_hits)
        ys = np.random.normal(cy, spread, n_hits)
        ax.scatter(xs, ys, color=color, s=20, alpha=0.7, zorder=4)

        ax.set_title(title, fontsize=12, fontweight="bold", color=color, pad=10)
        ax.text(0, -0.88, status, ha="center", fontsize=9, color=TEXT,
                bbox=dict(boxstyle="round,pad=0.3", fc="#e8f5ec", ec="#c3dbcc", alpha=0.8))
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.suptitle("Bias-Variance Tradeoff — 偏差-方差权衡", fontsize=16, fontweight="bold",
                 color=TEXT, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(OUT, "bias-variance.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ bias-variance.png")


# ════════════════════════════════════════════════════
# 5. L1 vs L2 Regularization Contour
# ════════════════════════════════════════════════════
def plot_l1_l2_contour():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=BG)
    w1 = np.linspace(-1.5, 1.5, 300)
    w2 = np.linspace(-1.5, 1.5, 300)
    W1, W2 = np.meshgrid(w1, w2)
    Z = (W1 - 0.5) ** 2 + 3 * (W2 - 0.2) ** 2 + 0.5 * (W1 - 0.5) * (W2 - 0.2)

    for ax, reg_type in [(ax1, "L1"), (ax2, "L2")]:
        ax.set_facecolor(BG)
        ax.contour(W1, W2, Z, levels=12, colors="#c3dbcc", linewidths=0.8, alpha=0.7)

        if reg_type == "L1":
            diamond = mpatches.Polygon(
                [[0, 1], [1, 0], [0, -1], [-1, 0]],
                fill=False, edgecolor=GREEN, lw=2.5, zorder=3)
            ax.add_patch(diamond)
            ax.set_title("L1 (Lasso) — 菱形约束", fontsize=13, fontweight="bold", color=GREEN)
            opt_x, opt_y = 1.0, 0.0
        else:
            circle = plt.Circle((0, 0), 1, fill=False, edgecolor=AMBER, lw=2.5, zorder=3)
            ax.add_patch(circle)
            ax.set_title("L2 (Ridge) — 圆形约束", fontsize=13, fontweight="bold", color=AMBER)
            opt_x, opt_y = 0.82, 0.45

        ax.scatter(opt_x, opt_y, color=RED, s=100, zorder=5, edgecolors="white", linewidth=1.5)
        label = f"Optimum: w\u2081={opt_x:.2f}, w\u2082={opt_y:.2f}\n"
        label += "\u2192 w\u2082=0 (Sparse)" if reg_type == "L1" else "\u2192 Both non-zero (Non-sparse)"
        ax.annotate(label, xy=(opt_x, opt_y), xytext=(opt_x + 0.3, opt_y + 0.25),
                    arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
                    fontsize=9, color=RED, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RED, alpha=0.85))

        ax.axhline(0, color=TEXT, lw=1)
        ax.axvline(0, color=TEXT, lw=1)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlabel("w\u2081", fontsize=12, color=TEXT)
        ax.set_ylabel("w\u2082", fontsize=12, color=TEXT)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)

    fig.suptitle("L1 vs L2 Regularization — 正则化约束对比", fontsize=15, fontweight="bold",
                 color=TEXT, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "l1-l2-contour.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ l1-l2-contour.png")


# ════════════════════════════════════════════════════
# 6. Bayes Formula — clean layout with no overlap
# ════════════════════════════════════════════════════
def plot_bayes_formula():
    fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(0.5, 0.97, "Bayes' Theorem \u2014 贝叶斯公式",
            ha="center", fontsize=16, fontweight="bold", color=TEXT)

    # -- Venn diagram (middle) --
    # Sample space
    rect = FancyBboxPatch((0.03, 0.05), 0.94, 0.50,
                           boxstyle="round,pad=0.02",
                           fill=False, edgecolor="#c3dbcc", lw=1.5, ls="--")
    ax.add_patch(rect)
    ax.text(0.5, 0.03, "Sample Space \u03a9 (All possible outcomes)",
            ha="center", fontsize=9, color="#6a8f7a", style="italic")

    # P(A) — left ellipse
    e_a = mpatches.Ellipse((0.30, 0.34), 0.26, 0.28, fill=True,
                            facecolor=GREEN, alpha=0.12, edgecolor=GREEN, lw=2.5)
    ax.add_patch(e_a)
    ax.text(0.30, 0.32, "A", ha="center", fontsize=18, fontweight="bold", color=GREEN)
    ax.text(0.30, 0.22, "Prior P(A)", ha="center", fontsize=10, color=GREEN)

    # P(B) — right ellipse
    e_b = mpatches.Ellipse((0.74, 0.34), 0.30, 0.32, fill=True,
                            facecolor="#dc3545", alpha=0.08, edgecolor="#dc3545", lw=2.5)
    ax.add_patch(e_b)
    ax.text(0.74, 0.34, "B", ha="center", fontsize=18, fontweight="bold", color="#dc3545")
    ax.text(0.74, 0.24, "Evidence P(B)", ha="center", fontsize=10, color="#dc3545")

    # A\u2229B — intersection
    inter = mpatches.Ellipse((0.5, 0.34), 0.16, 0.18, fill=True,
                              facecolor=GREEN, alpha=0.3, edgecolor=GREEN, lw=2)
    ax.add_patch(inter)
    ax.text(0.5, 0.32, "A\u2229B", ha="center", fontsize=12, fontweight="bold", color=TEXT)
    ax.text(0.5, 0.23, "P(B|A)P(A)", ha="center", fontsize=9, color=TEXT)

    # -- Flow arrows above Venn --
    ax.annotate("", xy=(0.55, 0.62), xytext=(0.15, 0.62),
                arrowprops=dict(arrowstyle="->", color=TEXT, lw=2))
    ax.text(0.35, 0.64, "New evidence B is observed",
            ha="center", fontsize=10, fontweight="bold", color=TEXT)

    ax.annotate("", xy=(0.85, 0.62), xytext=(0.55, 0.62),
                arrowprops=dict(arrowstyle="->", color=TEXT, lw=2))
    ax.text(0.70, 0.64, "Belief is updated",
            ha="center", fontsize=10, fontweight="bold", color=TEXT)

    # -- Formula box (top-right area, not overlapping) --
    fb = FancyBboxPatch((0.15, 0.70), 0.70, 0.22,
                         boxstyle="round,pad=0.05",
                         fill=True, facecolor="#e8f5ec", edgecolor="#c3dbcc")
    ax.add_patch(fb)
    ax.text(0.5, 0.84, "P(A|B) = P(B|A) \u00b7 P(A) / P(B)",
            ha="center", fontsize=14, fontweight="bold", color=TEXT)
    ax.text(0.5, 0.74, "Posterior = Prior \u00d7 Adjustment Factor",
            ha="center", fontsize=10, color=TEXT,
            style="italic")

    # -- Term definitions (bottom) --
    terms = (
        "\u2022  P(A) = Prior: Initial belief about A before seeing data\n"
        "\u2022  P(B|A) = Likelihood: Probability of observing B given A is true\n"
        "\u2022  P(B) = Evidence: Marginal probability of B (normalization constant)\n"
        "\u2022  P(A|B) = Posterior: Updated belief about A after observing B"
    )
    ax.text(0.5, 0.50, terms, ha="center", fontsize=9, color=TEXT,
            bbox=dict(boxstyle="round,pad=0.5", fc="#e8f5ec", ec="#c3dbcc"))

    plt.savefig(os.path.join(OUT, "bayes-formula.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ bayes-formula.png")


# ════════════════════════════════════════════════════
# 7. Naive Bayes Flowchart — fixed spacing & text
# ════════════════════════════════════════════════════
def plot_naive_bayes_flow():
    fig, ax = plt.subplots(figsize=(7.5, 7.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def draw_box(x, y, w, h, lines, color=GREEN, alpha=0.12):
        """lines = [(bold_line, sub_line), ...]"""
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                              boxstyle="round,pad=0.1",
                              fill=True, facecolor=color, alpha=alpha,
                              edgecolor=color, lw=2)
        ax.add_patch(box)
        n = len(lines)
        for i, (bold, sub) in enumerate(lines):
            yy = y + (n - 1) / 2 * 0.18 - i * 0.18
            ax.text(x, yy + 0.04, bold, ha="center", fontsize=10,
                    fontweight="bold", color=TEXT)
            if sub:
                ax.text(x, yy - 0.12, sub, ha="center", fontsize=8, color=TEXT)

    def draw_arrow(y_from, y_to, x=5):
        ax.annotate("", xy=(x, y_to), xytext=(x, y_from),
                    arrowprops=dict(arrowstyle="->", color=TEXT, lw=2))

    def draw_highlight(x, y, w, h, text):
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                              boxstyle="round,pad=0.05",
                              fill=True, facecolor="#fff3cd", alpha=1,
                              edgecolor="#ffc107", lw=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", fontsize=9, fontweight="bold", color="#856404")

    # Step 1
    draw_box(5, 9.2, 4, 0.55,
             [("① Training Data", "Samples (x\u2081~x_d) + Labels")])
    draw_arrow(8.9, 8.3)

    # Step 2
    draw_box(5, 7.8, 5.5, 0.65,
             [("② Calculate Prior P(C\u2096)", ""),
              ("P(C\u2096) = Count(C\u2096) / Total Samples", "")])
    ax.text(1.5, 7.8, "for each\nclass k", ha="center", fontsize=8,
            color="#6a8f7a", style="italic")
    draw_arrow(7.45, 6.75)

    # Step 3
    draw_box(5, 6.3, 8, 0.7,
             [("③ Calculate Conditional Prob P(x\u1d62|C\u2096)", ""),
              ("P(x\u1d62|C\u2096) = frequency of feature", ""),
              ("x\u1d62 in class C\u2096", "")],
             color=GREEN, alpha=0.08)
    draw_arrow(5.9, 5.2)

    # Key assumption
    draw_highlight(5, 4.7, 8.5, 0.45,
                   "Core Assumption: Feature Independence\n"
                   "P(x\u2081...x_d|C\u2096) = \u220f P(x\u1d62|C\u2096)")
    draw_arrow(4.45, 3.7)

    # Step 4
    draw_box(5, 3.2, 6.5, 0.65,
             [("④ Predict New Sample", ""),
              ("Choose max P(C\u2096) \u00b7 \u220f P(x\u1d62|C\u2096)", "")],
             color=GREEN, alpha=0.12)
    draw_arrow(2.85, 2.2)

    # Formula
    fb = FancyBboxPatch((2, 1.8), 6, 0.5,
                         boxstyle="round,pad=0.05",
                         fill=True, facecolor=GREEN, alpha=0.06,
                         edgecolor="#c3dbcc", lw=1)
    ax.add_patch(fb)
    ax.text(5, 2.05, "\u0177 = argmax\u2096  P(C\u2096) \u00b7 \u220f\u1d62 P(x\u1d62|C\u2096)",
            ha="center", fontsize=13, fontweight="bold", color=TEXT,
            fontfamily="monospace")

    ax.set_title("Naive Bayes \u2014 朴素贝叶斯计算流程",
                 fontsize=15, fontweight="bold", color=TEXT, pad=10)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "naive-bayes-flow.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("✓ naive-bayes-flow.png")



# ════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating ML-basis diagrams...\n")
    plot_confusion_matrix()
    plot_roc_curve()
    plot_pr_curve()
    plot_bias_variance()
    plot_l1_l2_contour()
    plot_bayes_formula()
    plot_naive_bayes_flow()
    print(f"\nAll diagrams saved to: {OUT}/")
