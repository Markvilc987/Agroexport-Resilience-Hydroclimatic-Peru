#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_figures_300dpi.py
Generates 4 publication-grade 300 DPI multi-panel figures for Project 15:
  - Figure_1_Macro_Hydroclimatic_Agroexport_Dynamics.png
  - Figure_2_Spatial_Bivariate_ERA5_and_Bottlenecks.png
  - Figure_3_Subnational_DML_and_Infrastructure_Taxonomy.png
  - Figure_4_Supply_Chain_Pareto_Optimization.png
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

BASE_DIR = "/Users/marcos/Personal/1. PROYECTOS/1. ARTICULOS CIENTIFICOS"
PROJ_DIR = os.path.join(BASE_DIR, "15_Resiliencia_Agroexportadora_Hidroclimatica_Peru")
PROC_DIR = os.path.join(PROJ_DIR, "data", "processed")
SPATIAL_DIR = os.path.join(PROJ_DIR, "data", "spatial")
TAB_DIR = os.path.join(PROJ_DIR, "paper", "tables")
FIG_DIR = os.path.join(PROJ_DIR, "paper", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9.5,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.2,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def make_figure_1():
    print("Generating Figure 1: Macro-Longitudinal Hydroclimatic & Agro-Export Dynamics (312 months, 2000-2025)...")
    df_mo = pd.read_csv(os.path.join(PROC_DIR, "macro_monthly_agroexport_era5_panel_2000_2025.csv"))
    df_t1 = pd.read_csv(os.path.join(TAB_DIR, "table1_macro_crop_hydroclimatic_elasticities_312m.csv"))
    df_mo["date_dec"] = df_mo["year"] + (df_mo["month"] - 0.5) / 12.0

    fig = plt.figure(figsize=(16.2, 11.8))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.34)

    # Panel A: 26-Year Trajectory of Agricultural GDP Index & ERA5 Coastal UTCI Anomaly
    ax1 = fig.add_subplot(gs[0, 0])
    ax1_r = ax1.twinx()
    ax1_r.spines["top"].set_visible(False)

    # Highlight El Niño events (2017 Coastal El Niño, 2023-2024 El Niño / Cyclone Yaku)
    ax1.axvspan(2017.0, 2017.5, color="#fee090", alpha=0.55, label="2017 Coastal El Niño")
    ax1.axvspan(2023.0, 2024.4, color="#fdae61", alpha=0.45, label="2023–2024 El Niño / Cyclone Yaku")

    pbi_ma = df_mo["pbi_agricola_idx"].rolling(6, min_periods=1).mean()
    utci_ma = df_mo["utci_coast_agroexport_c"].rolling(6, min_periods=1).mean()

    l1, = ax1.plot(df_mo["date_dec"], pbi_ma, color="#1b7837", lw=2.1, label="Agricultural GDP Index (6m MA, 2007=100)")
    l2, = ax1_r.plot(df_mo["date_dec"], utci_ma, color="#d73027", lw=1.6, ls="--", label="Coastal ERA5 UTCI (6m MA, °C)")

    ax1.set_title("A. Agricultural Output & Satellite ERA5 Coastal Thermal Regime (2000–2025)", loc="left", pad=8)
    ax1.set_xlabel("Year (Monthly Observations, N = 312)")
    ax1.set_ylabel("Agricultural GDP Index (2007 = 100)", color="#1b7837", fontweight="bold")
    ax1_r.set_ylabel("Coastal Agro-Export UTCI (°C)", color="#d73027", fontweight="bold")
    ax1.set_xlim(2000, 2026)
    ax1.grid(True, alpha=0.22, ls=":")
    lines = [l1, l2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", frameon=True, facecolor="white", framealpha=0.9)

    # Panel B: Nocturnal Heat Stress (Tropical Nights) vs North Coast Mango & Lime Output (2007-2025)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2_r = ax2.twinx()
    ax2_r.spines["top"].set_visible(False)

    sub_07 = df_mo[df_mo["year"] >= 2007].copy()
    ax2.axvspan(2023.0, 2024.4, color="#fdae61", alpha=0.38)
    l_m, = ax2.plot(sub_07["date_dec"], sub_07["crop_mango_kt"].rolling(3, min_periods=1).mean(), color="#2b83ba", lw=1.9, label="Mango Output (3m MA, kt)")
    l_g, = ax2.plot(sub_07["date_dec"], sub_07["crop_grape_kt"].rolling(3, min_periods=1).mean(), color="#7b3294", lw=1.8, label="Table Grapes Output (3m MA, kt)")
    l_tn, = ax2_r.plot(sub_07["date_dec"], sub_07["tropical_nights_coast_agroexport"].rolling(3, min_periods=1).mean(), color="#e66101", lw=1.5, ls=":", label="Coastal Tropical Nights (>20°C/mo)")

    ax2.set_title("B. Nocturnal Heat Stress vs. Perennial Export Crops (2007–2025)", loc="left", pad=8)
    ax2.set_xlabel("Year (Monthly Observations, N = 228)")
    ax2.set_ylabel("Monthly Crop Production (thousand metric tons, kt)", fontweight="bold")
    ax2_r.set_ylabel("ERA5 Tropical Nights (>20°C / month)", color="#e66101", fontweight="bold")
    ax2.set_xlim(2007, 2026)
    ax2.grid(True, alpha=0.22, ls=":")
    lns2 = [l_m, l_g, l_tn]
    ax2.legend(lns2, [l.get_label() for l in lns2], loc="upper left", frameon=True, facecolor="white", framealpha=0.9)

    # Panel C: Forest Plot of Newey-West HAC Thermal & Nocturnal Heat Elasticities across Crops
    ax3 = fig.add_subplot(gs[1, 0])
    sub_c = df_t1[df_t1["crop_code"].str.startswith("crop_")].copy()
    sub_c = sub_c.sort_values("beta_utci_thermal_z", ascending=True).reset_index(drop=True)
    y_pos = np.arange(len(sub_c))
    short_labels = [s.split("(")[0].strip() for s in sub_c["crop_label"]]

    ax3.axvline(0, color="black", lw=1.0, ls="--", alpha=0.7)
    ax3.errorbar(
        sub_c["beta_utci_thermal_z"], y_pos + 0.14,
        xerr=1.96 * sub_c["se_utci_thermal_z"],
        fmt="o", color="#d73027", ecolor="#d73027", elinewidth=1.4, capsize=2.5, markersize=5.0,
        label="ERA5 Thermal Stress (UTCI 1 SD)"
    )
    ax3.errorbar(
        sub_c["beta_tropical_nights_z"], y_pos - 0.14,
        xerr=1.96 * sub_c["se_tropical_nights_z"],
        fmt="s", color="#4575b4", ecolor="#4575b4", elinewidth=1.4, capsize=2.5, markersize=4.5,
        label="ERA5 Nocturnal Heat (Tropical Nights 1 SD)"
    )
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(short_labels)
    ax3.set_xlabel("Log-Output Semi-Elasticity (Newey–West HAC ± 95% CI)")
    ax3.set_title("C. Crop-Specific Sensitivity to Daytime vs. Nocturnal Heat Anomalies", loc="left", pad=8)
    ax3.grid(True, axis="x", alpha=0.25, ls=":")
    ax3.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.9)

    # Panel D: 2023-2024 El Niño / Cyclone Yaku Production Shock (% change vs 2021-2022)
    ax4 = fig.add_subplot(gs[1, 1])
    sub_d = df_t1[df_t1["crop_code"].str.startswith("crop_")].copy()
    sub_d = sub_d.sort_values("shock_2023_2024_vs_2021_2022_pct", ascending=True).reset_index(drop=True)
    y_d = np.arange(len(sub_d))
    labels_d = [s.split("(")[0].strip() for s in sub_d["crop_label"]]
    vals_d = sub_d["shock_2023_2024_vs_2021_2022_pct"].values
    colors_d = ["#d73027" if v < 0 else "#1a9850" for v in vals_d]

    bars = ax4.barh(y_d, vals_d, color=colors_d, alpha=0.85, height=0.68, edgecolor="none")
    ax4.axvline(0, color="black", lw=1.0)
    ax4.set_yticks(y_d)
    ax4.set_yticklabels(labels_d)
    ax4.set_xlabel("Output Change in 2023–2024 ENSO vs. 2021–2022 Baseline (%)")
    ax4.set_title("D. Crop Production Divergence During 2023–2024 Hydroclimatic Shock", loc="left", pad=8)
    ax4.grid(True, axis="x", alpha=0.25, ls=":")
    x_min, x_max = min(vals_d.min() * 1.25, -35), max(vals_d.max() * 1.25, 25)
    ax4.set_xlim(x_min, x_max)
    for bar, v in zip(bars, vals_d):
        offset = 1.2 if v >= 0 else -1.2
        ha = "left" if v >= 0 else "right"
        ax4.text(v + offset, bar.get_y() + bar.get_height() / 2.0, f"{v:+.1f}%", va="center", ha=ha, fontsize=7.8, fontweight="bold")

    out_fp = os.path.join(FIG_DIR, "Figure_1_Macro_Hydroclimatic_Agroexport_Dynamics.png")
    fig.savefig(out_fp, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_fp}")


def make_figure_2():
    print("Generating Figure 2: Spatial Choropleth Maps across N = 1,873 Districts...")
    shp_fp = os.path.join(SPATIAL_DIR, "v_distritos_2023.shp")
    gdf = gpd.read_file(shp_fp)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    ubigeo_col = [c for c in gdf.columns if "ubigeo" in c.lower() or "id_dist" in c.lower()][0]
    gdf["ubigeo"] = gdf[ubigeo_col].astype(str).str.strip().str.zfill(6)

    df_dist = pd.read_csv(os.path.join(PROC_DIR, "district_agro_logistics_resilience_1873.csv"))
    df_dist["ubigeo"] = df_dist["ubigeo"].astype(str).str.strip().str.zfill(6)
    gdf = gdf.merge(df_dist, on="ubigeo", how="left")

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 7.2))
    plt.subplots_adjust(wspace=0.12)

    panels = [
        (
            "era5_utci_mean_2000_2025_c",
            "A. Satellite ERA5 Thermal Regime\n(Mean UTCI °C, 2000–2025)",
            "RdYlBu_r",
            "UTCI (°C, Topographic Downscaled)",
        ),
        (
            "agro_logistics_bottleneck_rate_pct",
            "B. Hydro-Agri & Logistics Bottlenecks\n(% Stalled/Delayed Works, N = 40,538)",
            "PuRd",
            "Bottleneck / Delay Rate (%)",
        ),
        (
            "rural_vulnerability_index_0_100",
            "C. Rural Socio-Productive Vulnerability\n(Composite Index 0–100, N = 1,873)",
            "viridis_r",
            "Vulnerability Index (0–100)",
        ),
    ]

    for ax, (col, title, cmap, cbar_label) in zip(axes, panels):
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(gdf[col].median())
        vmin, vmax = np.nanpercentile(gdf[col], 1), np.nanpercentile(gdf[col], 99)
        gdf.plot(
            column=col,
            ax=ax,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            linewidth=0.08,
            edgecolor="#444444",
            legend=True,
            legend_kwds={"label": cbar_label, "orientation": "horizontal", "shrink": 0.78, "pad": 0.04, "aspect": 25},
        )
        ax.set_title(title, fontsize=10.5, fontweight="bold", pad=8)
        ax.set_axis_off()

    out_fp = os.path.join(FIG_DIR, "Figure_2_Spatial_Bivariate_ERA5_and_Bottlenecks.png")
    fig.savefig(out_fp, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_fp}")


def make_figure_3():
    print("Generating Figure 3: Subnational Causal DML & Infrastructure Taxonomy (N = 1,873 districts; 40,538 works)...")
    df_dist = pd.read_csv(os.path.join(PROC_DIR, "district_agro_logistics_resilience_1873.csv"))
    df_t2 = pd.read_csv(os.path.join(TAB_DIR, "table2_subnational_dml_agro_logistics_1873.csv"))
    df_t3 = pd.read_csv(os.path.join(TAB_DIR, "table3_infrastructure_taxonomy_40538.csv"))

    fig = plt.figure(figsize=(16.6, 11.4))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.36, wspace=0.52)

    # Panel A: Infrastructure Taxonomy & Bottleneck Rates across 40,538 works
    ax1 = fig.add_subplot(gs[0, 0])
    df_t3_s = df_t3.sort_values("n_projects", ascending=True).reset_index(drop=True)
    y_p = np.arange(len(df_t3_s))
    short_cat = [c.split(":", 1)[1].strip() if ":" in c else c for c in df_t3_s["infrastructure_category"]]
    colors_cat = ["#1f78b4" if "Hydro-Agri" in c else "#e66101" for c in df_t3_s["infrastructure_category"]]

    bars = ax1.barh(y_p, df_t3_s["n_projects"], color=colors_cat, alpha=0.85, height=0.65)
    ax1.set_yticks(y_p)
    ax1.set_yticklabels(short_cat, fontsize=8.3)
    ax1.set_xlabel("Number of Public Investment Works (Total N = 40,538)")
    ax1.set_title("A. Hydro-Agricultural (Blue) & Logistics (Orange) Portfolio", loc="left", pad=8)
    ax1.set_xlim(0, df_t3_s["n_projects"].max() * 1.38)
    ax1.grid(True, axis="x", alpha=0.25, ls=":")
    for bar, (_, r) in zip(bars, df_t3_s.iterrows()):
        w = bar.get_width()
        ax1.text(
            w + 150, bar.get_y() + bar.get_height() / 2.0,
            f"{int(w):,} ({r['bottleneck_or_delayed_rate_pct']:.1f}% delayed)",
            va="center", ha="left", fontsize=7.6, fontweight="bold"
        )

    # Panel B: OLS-FE vs 5-Fold Cross-Fitted DML Parameter Estimates (Vulnerability Index & Poverty)
    ax2 = fig.add_subplot(gs[0, 1])
    sub_v = df_t2[df_t2["outcome_code"] == "rural_vulnerability_index_0_100"].copy().reset_index(drop=True)
    y_v = np.arange(len(sub_v))
    short_tr = [
        "Irrigation Bottleneck (1 SD)",
        "First-Mile Road/Bridge Bottleneck (1 SD)",
        "Satellite ERA5 Thermal Shock (1 SD)",
        "Compound Climate × Bottleneck (1 SD)",
        "Completed Infra Buffer per 1k (1 SD)",
    ]

    ax2.axvline(0, color="black", lw=1.0, ls="--")
    ax2.errorbar(
        sub_v["ols_fe_beta"], y_v + 0.14,
        xerr=1.96 * sub_v["ols_fe_se_hc3"],
        fmt="o", color="#5e3c99", ecolor="#5e3c99", elinewidth=1.5, capsize=3, markersize=5.5,
        label="Spatial OLS + Dept. Fixed Effects (HC3)"
    )
    ax2.errorbar(
        sub_v["dml_5fold_theta"], y_v - 0.14,
        xerr=1.96 * sub_v["dml_5fold_se"],
        fmt="D", color="#d95f02", ecolor="#d95f02", elinewidth=1.5, capsize=3, markersize=5.5,
        label="Double/Debiased ML (5-Fold Cross-Fitted)"
    )
    ax2.set_yticks(y_v)
    ax2.set_yticklabels(short_tr, fontsize=8.5)
    ax2.set_ylim(-0.6, len(y_v) - 0.15)
    ax2.set_xlabel("Effect on Rural Vulnerability Index (0–100 Scale, ± 95% CI)")
    ax2.set_title("B. Causal DML vs. OLS-FE Estimates across N = 1,873 Districts", loc="left", pad=8)
    ax2.grid(True, axis="x", alpha=0.25, ls=":")
    ax2.legend(loc="lower left", frameon=True, facecolor="white", framealpha=0.92, fontsize=8.0)

    # Panel C: Compound Interaction: Rural Vulnerability & Agricultural-Labor Dropout across Climate x Bottleneck Regimes
    ax3 = fig.add_subplot(gs[1, 0])
    df_dist["clim_tercile"] = pd.qcut(df_dist["d_hydroclimatic_shock_z"], q=3, labels=["Low ERA5 Shock", "Moderate ERA5 Shock", "High ERA5 Shock"])
    df_dist["bot_tercile"] = pd.qcut(
        0.5 * df_dist["d_irrigation_bottleneck_z"] + 0.5 * df_dist["d_logistics_bottleneck_z"],
        q=3, labels=["Low Bottlenecks\n(T1)", "Medium Bottlenecks\n(T2)", "Severe Bottlenecks\n(T3)"]
    )
    piv = df_dist.groupby(["bot_tercile", "clim_tercile"], observed=False)["rural_vulnerability_index_0_100"].agg(["mean", "sem"]).unstack()

    x_b = np.arange(3)
    width = 0.25
    palette_c = ["#4575b4", "#fdae61", "#d73027"]
    for i, c_lvl in enumerate(["Low ERA5 Shock", "Moderate ERA5 Shock", "High ERA5 Shock"]):
        means = piv["mean"][c_lvl].values
        sems = piv["sem"][c_lvl].values
        ax3.bar(
            x_b + (i - 1) * width, means, width=width, color=palette_c[i], alpha=0.88,
            yerr=1.96 * sems, capsize=3, label=c_lvl
        )
    ax3.set_xticks(x_b)
    ax3.set_xticklabels(["Low Bottlenecks (T1)", "Medium Bottlenecks (T2)", "Severe Bottlenecks (T3)"])
    ax3.set_ylabel("Rural Socio-Productive Vulnerability (0–100)")
    ymin_c = max(0.0, float(piv["mean"].min().min()) - 14.0)
    ymax_c = float(piv["mean"].max().max()) + 12.0
    ax3.set_ylim(ymin_c, ymax_c)
    ax3.set_title("C. Synergistic Amplification: Climate Shock × Supply-Chain Paralysis", loc="left", pad=8)
    ax3.grid(True, axis="y", alpha=0.25, ls=":")
    ax3.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9)

    # Panel D: Protective Buffer Effect of Completed Irrigation & Feeder-Road Density across Deciles
    ax4 = fig.add_subplot(gs[1, 1])
    df_dist["comp_decile"] = pd.qcut(df_dist["d_completed_agro_logistics_per_1k_z"].rank(method="first"), q=8, labels=[f"O{i}" for i in range(1, 9)])
    oct_grp = df_dist.groupby("comp_decile", observed=False).agg(
        vuln_mean=("rural_vulnerability_index_0_100", "mean"),
        vuln_se=("rural_vulnerability_index_0_100", "sem"),
        pov_mean=("poverty_rate_pct", "mean"),
        pov_se=("poverty_rate_pct", "sem"),
    ).reset_index()

    x_o = np.arange(len(oct_grp))
    ax4_r = ax4.twinx()
    ax4_r.spines["top"].set_visible(False)

    l_v = ax4.errorbar(x_o, oct_grp["vuln_mean"], yerr=1.96 * oct_grp["vuln_se"], fmt="-o", color="#1b7837", lw=2.0, capsize=3, label="Vulnerability Index (0–100)")
    l_p = ax4_r.errorbar(x_o, oct_grp["pov_mean"], yerr=1.96 * oct_grp["pov_se"], fmt="--s", color="#2b83ba", lw=1.8, capsize=3, label="Monetary Poverty Rate (%)")

    ax4.set_xticks(x_o)
    ax4.set_xticklabels([f"Octile {i}" for i in range(1, 9)], rotation=20)
    ax4.set_xlabel("Completed Irrigation & Rural Feeder-Road Buffer Density (Octiles)")
    ax4.set_ylabel("Rural Vulnerability Index (0–100)", color="#1b7837", fontweight="bold")
    ax4_r.set_ylabel("Monetary Poverty Rate (%)", color="#2b83ba", fontweight="bold")
    ax4.set_title("D. Protective Buffer of Completed Hydro-Agri & Feeder-Road Works", loc="left", pad=8)
    ax4.grid(True, alpha=0.25, ls=":")

    out_fp = os.path.join(FIG_DIR, "Figure_3_Subnational_DML_and_Infrastructure_Taxonomy.png")
    fig.savefig(out_fp, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_fp}")


def make_figure_4():
    print("Generating Figure 4: Supply-Chain & Hydro-Agricultural Pareto Optimization...")
    with open(os.path.join(PROC_DIR, "optimization_pareto_curves.json"), "r", encoding="utf-8") as f:
        pareto = json.load(f)
    df_t4 = pd.read_csv(os.path.join(TAB_DIR, "table4_supply_chain_pareto_optimization.csv"))
    df_dist = pd.read_csv(os.path.join(PROC_DIR, "district_agro_logistics_resilience_1873.csv"))

    fig = plt.figure(figsize=(16.6, 11.2))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.36, wspace=0.52)

    # Panel A: Pareto Frontier Curve across Budget Ceilings
    ax1 = fig.add_subplot(gs[0, 0])
    styles = {
        "Policy 4: Climate-Supply-Chain DML Pareto Optimal": ("#d73027", "-o", 2.4),
        "Policy 2: Small-Works Greedy (Lowest Cost First)": ("#2b83ba", "--s", 1.8),
        "Policy 3: Unidimensional Poverty Ranking": ("#1b7837", "-.^", 1.8),
        "Policy 1: Historical Inertia (SIAF Budget Share)": ("#7f7f7f", ":d", 1.8),
    }
    for p_name, (col, fmt, lw) in styles.items():
        if p_name in pareto:
            b_vec = [0] + pareto[p_name]["budgets"]
            g_vec = [0.0] + pareto[p_name]["pct_resilience_gain"]
            short_p = p_name.split(":", 1)[1].strip()
            ax1.plot(b_vec, g_vec, fmt, color=col, lw=lw, markersize=5.0, label=short_p)

    ax1.set_xlabel("Completion Budget Ceiling B (Million Soles, S/)")
    ax1.set_ylabel("National Climate–Supply-Chain Resilience Gain (%)")
    ax1.set_title("A. Multi-Objective Pareto Frontier Across Budget Regimes", loc="left", pad=8)
    ax1.set_xlim(0, 12800)
    ax1.set_ylim(0, 105)
    ax1.grid(True, alpha=0.25, ls=":")
    ax1.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.92)

    # Panel B: Unlocked Irrigation vs First-Mile Logistics Projects under DML Pareto Policy
    ax2 = fig.add_subplot(gs[0, 1])
    sub_p4 = df_t4[df_t4["allocation_policy"].str.contains("Policy 4")].copy().reset_index(drop=True)
    x_b = np.arange(len(sub_p4))
    w = 0.36
    b1 = ax2.bar(x_b - w/2, sub_p4["irrigation_works_unlocked"], width=w, color="#1f78b4", label="Irrigation Works Unlocked (Canals, Dams)")
    b2 = ax2.bar(x_b + w/2, sub_p4["logistics_works_unlocked"], width=w, color="#e66101", label="First-Mile Logistics Unlocked (Feeder Roads, Bridges)")

    ax2.set_xticks(x_b)
    ax2.set_xticklabels([f"S/ {int(b):,}M" for b in sub_p4["budget_ceiling_million_soles"]])
    ax2.set_xlabel("Debottlenecking Budget Ceiling (Million Soles)")
    ax2.set_ylabel("Number of Stalled/Delayed Works Completed")
    ax2.set_title("B. Hydro-Agricultural vs. Logistics Works Unlocked (Pareto Policy)", loc="left", pad=8)
    ax2.set_ylim(0, max(sub_p4["logistics_works_unlocked"].max(), sub_p4["irrigation_works_unlocked"].max()) * 1.22)
    ax2.grid(True, axis="y", alpha=0.25, ls=":")
    ax2.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.92)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, h + 60, f"{int(h):,}", ha="center", va="bottom", fontsize=7.6, fontweight="bold")

    # Panel C: Regional Breakdown of Bottlenecked Irrigation & Logistics Works (Top 14 Departments)
    ax3 = fig.add_subplot(gs[1, 0])
    reg_grp = df_dist.groupby("nombdep").agg(
        irrig_bot=("agri_works_bottleneck_n", "sum"),
        log_bot=("logistics_works_bottleneck_n", "sum"),
    ).reset_index()
    reg_grp["total_bot"] = reg_grp["irrig_bot"] + reg_grp["log_bot"]
    reg_grp = reg_grp.sort_values("total_bot", ascending=True).tail(14).reset_index(drop=True)

    y_r = np.arange(len(reg_grp))
    ax3.barh(y_r, reg_grp["irrig_bot"], color="#1f78b4", height=0.65, label="Hydro-Agricultural Bottlenecks")
    ax3.barh(y_r, reg_grp["log_bot"], left=reg_grp["irrig_bot"], color="#e66101", height=0.65, label="Rural Transport Logistics Bottlenecks")
    ax3.set_yticks(y_r)
    ax3.set_yticklabels(reg_grp["nombdep"], fontsize=8.3)
    ax3.set_xlabel("Number of Stalled/Delayed Infrastructure Projects")
    ax3.set_title("C. Regional Concentration of Supply-Chain & Irrigation Bottlenecks", loc="left", pad=8)
    ax3.set_xlim(0, reg_grp["total_bot"].max() * 1.25)
    ax3.grid(True, axis="x", alpha=0.25, ls=":")
    ax3.legend(loc="lower right", frameon=True, facecolor="white", framealpha=0.92)
    for idx_r, r in reg_grp.iterrows():
        ax3.text(r["total_bot"] + 15, idx_r, f"{int(r['total_bot']):,}", va="center", ha="left", fontsize=7.8, fontweight="bold")

    # Panel D: Resilience Gain Comparison at B = S/ 2,500 Million across the 4 Policies
    ax4 = fig.add_subplot(gs[1, 1])
    sub_2500 = df_t4[df_t4["budget_ceiling_million_soles"] == 2500].copy().sort_values("resilience_gain_captured_pct", ascending=True).reset_index(drop=True)
    y_p4 = np.arange(len(sub_2500))
    short_names = [s.split(":", 1)[1].strip() for s in sub_2500["allocation_policy"]]
    p_cols = ["#7f7f7f", "#1b7837", "#2b83ba", "#d73027"]

    bars4 = ax4.barh(y_p4, sub_2500["resilience_gain_captured_pct"], color=p_cols, height=0.58, alpha=0.9)
    ax4.set_yticks(y_p4)
    ax4.set_yticklabels(short_names, fontsize=8.5)
    ax4.set_xlabel("National Resilience Gain Captured at B = S/ 2,500M (%)")
    ax4.set_title("D. Policy Efficiency Comparison at S/ 2,500 Million Budget", loc="left", pad=8)
    ax4.set_xlim(0, max(105.0, float(sub_2500["resilience_gain_captured_pct"].max()) * 1.48))
    ax4.grid(True, axis="x", alpha=0.25, ls=":")
    for bar, (_, r) in zip(bars4, sub_2500.iterrows()):
        w_val = bar.get_width()
        ax4.text(
            w_val + 1.5, bar.get_y() + bar.get_height() / 2.0,
            f"{w_val:.1f}% ({int(r['districts_debottlenecked']):,} dists / {int(r['total_works_unlocked']):,} works)",
            va="center", ha="left", fontsize=8.0, fontweight="bold"
        )

    out_fp = os.path.join(FIG_DIR, "Figure_4_Supply_Chain_Pareto_Optimization.png")
    fig.savefig(out_fp, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_fp}")


def main():
    make_figure_1()
    make_figure_2()
    make_figure_3()
    make_figure_4()


if __name__ == "__main__":
    main()
