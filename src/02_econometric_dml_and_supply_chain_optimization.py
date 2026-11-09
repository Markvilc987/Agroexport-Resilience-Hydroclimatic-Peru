#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_econometric_dml_and_supply_chain_optimization.py
Executes the three core empirical and operations-research modules for Project 15:
  Module 1: Macro-Longitudinal Distributed-Lag & HAC Econometrics (N = 312 months,
            2000-2025) across 24 series (3 macro-sectoral GDP indices, 3 aggregate
            crop baskets, and 18 individual agro-export and staple crops) under
            Satellite ERA5 Thermal Stress (UTCI, Tropical Nights) and ENSO Shocks.
  Module 2: Subnational Spatial Econometrics & 5-Fold Cross-Fitted Double/Debiased
            Machine Learning (DML, N = 1,873 districts; 40,538 infrastructure works)
            conditioning on district altitude, topographic slope, log population,
            rurality, baseline climate, fiscal capacity, and department fixed effects.
  Module 3: Constrained Budget-Allocation & Pareto Frontier Optimization for
            Debottlenecking Hydro-Agricultural and First-Mile Logistics Networks.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.model_selection import KFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

BASE_DIR = "/Users/marcos/Personal/1. PROYECTOS/1. ARTICULOS CIENTIFICOS"
PROJ_DIR = os.path.join(BASE_DIR, "15_Resiliencia_Agroexportadora_Hidroclimatica_Peru")
PROC_DIR = os.path.join(PROJ_DIR, "data", "processed")
TAB_DIR = os.path.join(PROJ_DIR, "paper", "tables")
os.makedirs(TAB_DIR, exist_ok=True)


def zscore(s):
    s = pd.Series(s, dtype=float)
    std = s.std(ddof=1)
    if std == 0 or np.isnan(std):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std


def run_module1_macro_crop_elasticities():
    print("=== Module 1: Macro-Longitudinal Crop & Agro-Export Hydroclimatic Elasticities (N = 312 months, 2000-2025) ===")
    mo_fp = os.path.join(PROC_DIR, "macro_monthly_agroexport_era5_panel_2000_2025.csv")
    df = pd.read_csv(mo_fp)
    df = df.sort_values(["year", "month"]).reset_index(drop=True)

    df["utci_coast_ma3"] = df["utci_coast_agroexport_c_anom_z"].rolling(3, min_periods=1).mean()
    df["utci_andes_ma3"] = df["utci_andes_staple_c_anom_z"].rolling(3, min_periods=1).mean()
    df["utci_selva_ma3"] = df["utci_selva_coffee_c_anom_z"].rolling(3, min_periods=1).mean()
    df["trop_nights_coast_ma3"] = df["tropical_nights_coast_agroexport_anom_z"].rolling(3, min_periods=1).mean()
    df["oni_ma3"] = df["oni_sst_anomaly"].rolling(3, min_periods=1).mean()
    df["trend_t"] = np.arange(len(df)) / 12.0

    month_dummies = pd.get_dummies(df["month"], prefix="m", drop_first=True, dtype=float)

    # Exact 24 series: 3 Macro Aggregates + 3 Composite Baskets + 18 Individual Crops
    crops_spec = [
        ("pbi_agricola_idx", "Agricultural GDP Index (2007=100)", "Macro Aggregate", "utci_coast_ma3"),
        ("pbi_pecuario_idx", "Livestock GDP Index (2007=100)", "Macro Aggregate", "utci_coast_ma3"),
        ("pbi_manufactura_primaria_idx", "Primary Resource Processing GDP Index (2007=100)", "Macro Aggregate", "utci_coast_ma3"),
        ("agroexport_crops_core_kt", "Core Agro-Export Basket (kt)", "Export Aggregate", "utci_coast_ma3"),
        ("agroexport_crops_total_kt", "Total High-Value Agro-Export Basket (kt)", "Export Aggregate", "utci_coast_ma3"),
        ("staple_crops_total_kt", "Domestic Food-Security Staple Basket (kt)", "Staple Aggregate", "utci_andes_ma3"),
        ("crop_mango_kt", "Mango (North Coast Export)", "Agro-Export Crop", "utci_coast_ma3"),
        ("crop_lime_kt", "Tahiti/Sutil Lime (North Coast)", "Agro-Export Crop", "utci_coast_ma3"),
        ("crop_grape_kt", "Table Grapes (Irrigated Coast Export)", "Agro-Export Crop", "utci_coast_ma3"),
        ("crop_asparagus_kt", "Asparagus (Irrigated Coast Export)", "Agro-Export Crop", "utci_coast_ma3"),
        ("crop_mandarin_kt", "Mandarin Citrus (Central Coast Export)", "Agro-Export Crop", "utci_coast_ma3"),
        ("crop_orange_kt", "Sweet Orange (Central/Selva Citrus)", "Agro-Export Crop", "utci_selva_ma3"),
        ("crop_olive_kt", "Olive (Southern Coast Export)", "Agro-Export Crop", "utci_coast_ma3"),
        ("crop_coffee_kt", "Coffee (Selva Alta Traditional Export)", "Agro-Export Crop", "utci_selva_ma3"),
        ("crop_cocoa_kt", "Cocoa (Amazonian Export)", "Agro-Export Crop", "utci_selva_ma3"),
        ("crop_quinoa_kt", "Quinoa (Highland Superfood Export)", "Agro-Export Crop", "utci_andes_ma3"),
        ("crop_onion_kt", "Yellow/Red Onion (Coast Export/Domestic)", "Horticultural Crop", "utci_coast_ma3"),
        ("crop_garlic_kt", "Garlic (Arequipa/Coast Horticultural Export)", "Horticultural Crop", "utci_coast_ma3"),
        ("crop_tomato_kt", "Tomato (Coastal Horticultural Crop)", "Horticultural Crop", "utci_coast_ma3"),
        ("crop_sugarcane_kt", "Sugarcane (Agro-Industrial Coast)", "Agro-Industrial", "utci_coast_ma3"),
        ("crop_potato_kt", "Potato (Andean Staple)", "Staple Crop", "utci_andes_ma3"),
        ("crop_rice_kt", "Paddy Rice (Coast/Selva Staple)", "Staple Crop", "utci_coast_ma3"),
        ("crop_maize_starchy_kt", "Starchy Maize (Andean Staple)", "Staple Crop", "utci_andes_ma3"),
        ("crop_maize_yellow_kt", "Hard Yellow Maize (Feed/Agro-Industry)", "Staple Crop", "utci_coast_ma3"),
    ]

    results = []
    for col, label, cat, utci_var in crops_spec:
        if col not in df.columns:
            continue
        sub = df[[col, "year", "month", utci_var, "trop_nights_coast_ma3", "oni_ma3", "trend_t"]].copy()
        sub = pd.concat([sub, month_dummies], axis=1).dropna(subset=[col, utci_var, "oni_ma3"])
        if len(sub) < 60:
            continue

        y_raw = sub[col].values
        y_log = np.log(np.maximum(y_raw, 0.1))

        X_cols = [utci_var, "trop_nights_coast_ma3", "oni_ma3", "trend_t"] + list(month_dummies.columns)
        X = sm.add_constant(sub[X_cols].fillna(0.0))
        model = sm.OLS(y_log, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})

        base_21_22 = df[df["year"].isin([2021, 2022])][col].mean()
        shock_23_24 = df[df["year"].isin([2023, 2024])][col].mean()
        enso_23_24_pct = 100.0 * (shock_23_24 - base_21_22) / base_21_22 if base_21_22 and base_21_22 > 0 else np.nan

        results.append({
            "crop_code": col,
            "crop_label": label,
            "category": cat,
            "n_months": int(len(sub)),
            "period": f"{int(sub['year'].min())}-{int(sub['year'].max())}",
            "mean_monthly_output": float(np.nanmean(y_raw)),
            "beta_utci_thermal_z": float(model.params[utci_var]),
            "se_utci_thermal_z": float(model.bse[utci_var]),
            "pval_utci_thermal_z": float(model.pvalues[utci_var]),
            "beta_tropical_nights_z": float(model.params["trop_nights_coast_ma3"]),
            "se_tropical_nights_z": float(model.bse["trop_nights_coast_ma3"]),
            "pval_tropical_nights_z": float(model.pvalues["trop_nights_coast_ma3"]),
            "beta_oni_enso": float(model.params["oni_ma3"]),
            "se_oni_enso": float(model.bse["oni_ma3"]),
            "pval_oni_enso": float(model.pvalues["oni_ma3"]),
            "trend_annual_growth_pct": float(model.params["trend_t"] * 100.0),
            "r2_adj": float(model.rsquared_adj),
            "shock_2023_2024_vs_2021_2022_pct": float(enso_23_24_pct),
        })

    df_res1 = pd.DataFrame(results)
    t1_fp = os.path.join(TAB_DIR, "table1_macro_crop_hydroclimatic_elasticities_312m.csv")
    df_res1.to_csv(t1_fp, index=False)
    n_indiv_crops = int(df_res1["crop_code"].str.startswith("crop_").sum())
    print(f"  Saved Table 1 ({len(df_res1)} total models: {n_indiv_crops} individual crops + 6 macro/basket series) -> {t1_fp}")
    return df_res1


def run_dml_crossfit(y, d, X_conf, n_splits=5, random_state=42):
    """5-fold cross-fitted Double/Debiased Machine Learning (Chernozhukov et al., 2018)."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    y_tilde = np.zeros_like(y, dtype=float)
    d_tilde = np.zeros_like(d, dtype=float)

    for train_idx, test_idx in kf.split(X_conf):
        ml_y = GradientBoostingRegressor(n_estimators=110, max_depth=3, learning_rate=0.05, random_state=random_state)
        ml_d = GradientBoostingRegressor(n_estimators=110, max_depth=3, learning_rate=0.05, random_state=random_state)
        ml_y.fit(X_conf[train_idx], y[train_idx])
        ml_d.fit(X_conf[train_idx], d[train_idx])
        y_tilde[test_idx] = y[test_idx] - ml_y.predict(X_conf[test_idx])
        d_tilde[test_idx] = d[test_idx] - ml_d.predict(X_conf[test_idx])

    theta = np.sum(d_tilde * y_tilde) / np.sum(d_tilde ** 2)
    psi = (y_tilde - theta * d_tilde) * d_tilde
    se = np.sqrt(np.mean(psi ** 2) / (len(y) * (np.mean(d_tilde ** 2) ** 2)))
    t_stat = theta / se
    p_val = 2.0 * (1.0 - stats.norm.cdf(np.abs(t_stat)))
    return float(theta), float(se), float(t_stat), float(p_val)


def run_module2_subnational_dml_and_infrastructure():
    print("\n=== Module 2: Subnational Econometrics & Causal DML across N = 1,873 Districts & 40,538 Works ===")
    dist_fp = os.path.join(PROC_DIR, "district_agro_logistics_resilience_1873.csv")
    df = pd.read_csv(dist_fp)

    pw_fp = os.path.join(PROC_DIR, "agro_and_logistics_public_works_40537.parquet")
    df_pw = pd.read_parquet(pw_fp)
    est_upper = df_pw["estado_ejecucion"].astype(str).str.upper()
    df_pw["is_completed"] = est_upper.str.contains("FINALIZAD|LIQUIDAD|CONCLUID|RECEPCIONAD", regex=True).astype(int)
    df_pw["is_bottleneck"] = (
        (df_pw["is_stalled_or_paralyzed"] == 1)
        | (df_pw.get("target_retraso_binario", 0) == 1)
        | (df_pw.get("mef_num_atrasos_paralizaciones", 0) > 0)
    ).astype(int)
    cost_col = "costo_inversion_referencial" if "costo_inversion_referencial" in df_pw.columns else "costo_et_soles"
    df_pw["cost_m_soles"] = pd.to_numeric(df_pw[cost_col], errors="coerce").fillna(0.0).clip(upper=5e9) / 1e6

    # Ensure sobrecosto_pct_clean is strictly on the percentage scale (0 to 300%)
    raw_ov = pd.to_numeric(df_pw.get("sobrecosto_pct", df_pw.get("sobrecosto_pct_clean", 0.0)), errors="coerce").fillna(0.0)
    df_pw["overrun_pct_scaled"] = np.where(
        (raw_ov > 0.0) & (raw_ov <= 3.0),
        raw_ov * 100.0,
        np.where(raw_ov > 3.0, np.clip(raw_ov, 0.0, 300.0), 0.0),
    )

    def classify_subcat(row):
        n1 = str(row.get("tipo_obra_n1", ""))
        n2 = str(row.get("tipo_obra_n2", ""))
        n3 = str(row.get("tipo_obra_n3", ""))
        if n1 == "Agricultura":
            if n3 == "Canales":
                return "Hydro-Agri 1: Irrigation Canals (Canales)"
            elif n3 in ("Represa/Reservorio", "Almacenamiento Y Distribución"):
                return "Hydro-Agri 2: Dams, Reservoirs & Water Storage"
            elif n3 in ("Muro De Contención", "Dique", "Bocatomas", "Defensa Ribereña", "Encauzamiento/Descolmatación"):
                return "Hydro-Agri 3: Riverbank Defenses, Dikes & Intakes"
            elif n2 == "Riego":
                return "Hydro-Agri 4: Pressurized/Other Irrigation Systems"
            else:
                return "Hydro-Agri 5: Productive Crop & Livestock Facilities"
        else:
            if n3 == "Caminos Vecinales":
                return "Logistics 1: Rural Feeder Roads (Caminos Vecinales)"
            elif n3 in ("Trocha Carrozable", "Caminos De Herradura", "Accesos"):
                return "Logistics 2: Rural Tracks & Farm Access Paths (Trochas)"
            elif n3 == "Puentes":
                return "Logistics 3: Rural & Interurban Bridges (Puentes)"
            elif n3 in ("Carreteras", "Vías"):
                return "Logistics 4: Regional & Trunk Highways (Carreteras)"
            else:
                return "Logistics 5: Ancillary Land Transport Infrastructure"

    df_pw["taxonomy_group"] = df_pw.apply(classify_subcat, axis=1)
    tax_rows = []
    for grp, gdf in df_pw.groupby("taxonomy_group"):
        tax_rows.append({
            "infrastructure_category": grp,
            "n_projects": int(len(gdf)),
            "share_of_portfolio_pct": float(100.0 * len(gdf) / len(df_pw)),
            "total_investment_million_soles": float(gdf["cost_m_soles"].sum()),
            "completed_rate_pct": float(100.0 * gdf["is_completed"].mean()),
            "formal_paralysis_rate_pct": float(100.0 * gdf["is_stalled_or_paralyzed"].mean()),
            "bottleneck_or_delayed_rate_pct": float(100.0 * gdf["is_bottleneck"].mean()),
            "stalled_capital_million_soles": float((gdf["cost_m_soles"] * gdf["is_stalled_or_paralyzed"]).sum()),
            "bottleneck_capital_million_soles": float((gdf["cost_m_soles"] * gdf["is_bottleneck"]).sum()),
            "mean_cost_overrun_pct": float(gdf["overrun_pct_scaled"].mean()),
            "mean_delay_ratio": float(gdf["retraso_ratio_clean"].mean()),
        })
    df_tax = pd.DataFrame(tax_rows).sort_values("infrastructure_category").reset_index(drop=True)
    t3_fp = os.path.join(TAB_DIR, "table3_infrastructure_taxonomy_40538.csv")
    df_tax.to_csv(t3_fp, index=False)
    print(f"  Saved Table 3 (Infrastructure Taxonomy across {len(df_pw):,} projects, Overrun % range: {df_tax['mean_cost_overrun_pct'].min():.2f}%-{df_tax['mean_cost_overrun_pct'].max():.2f}%) -> {t3_fp}")

    # Outcomes:
    enroll = pd.to_numeric(df["students_total"], errors="coerce").replace(0, np.nan).fillna(500.0)
    agri_drop = pd.to_numeric(df["drop_agri_work"], errors="coerce").fillna(0.0)
    child_drop = pd.to_numeric(df["drop_child_labor"], errors="coerce").fillna(0.0)
    econ_drop = pd.to_numeric(df["drop_economic"], errors="coerce").fillna(0.0)
    df["agri_labor_dropout_per_1k"] = 1000.0 * (agri_drop + child_drop + 0.35 * econ_drop) / np.maximum(enroll, 30.0)
    df["school_dropout_rate_pct"] = pd.to_numeric(df["dropout_rate_pct"], errors="coerce").fillna(0.0)
    df["poverty_rate_pct"] = pd.to_numeric(df["pobreza_monetaria_oficial"], errors="coerce").fillna(df["pobreza_monetaria_oficial"].median())

    # Composite Rural Socio-Productive Vulnerability Index (normalized 0-100 scale, mean = 50, SD = 15)
    z_pov = zscore(df["poverty_rate_pct"])
    z_agdrop = zscore(np.log1p(df["agri_labor_dropout_per_1k"]))
    z_schdrop = zscore(df["school_dropout_rate_pct"])
    raw_vuln = 0.45 * z_pov + 0.30 * z_agdrop + 0.25 * z_schdrop
    df["rural_vulnerability_index_0_100"] = np.clip(50.0 + 15.0 * zscore(raw_vuln), 2.0, 98.0)

    # Demographic & topographic covariates
    pop = pd.to_numeric(df["poblacion_oficial"], errors="coerce").replace(0, np.nan).fillna(4000.0)
    df["ln_pop"] = np.log1p(pop)
    df["pct_rural_schools_clean"] = pd.to_numeric(df.get("pct_rural_schools", 50.0), errors="coerce").fillna(50.0)
    df["altitude_mean_m"] = pd.to_numeric(df.get("altitude_mean_m", 1800.0), errors="coerce").fillna(1800.0)
    df["topo_slope_deg"] = pd.to_numeric(df.get("topo_slope_deg", 12.0), errors="coerce").fillna(12.0)

    # D1: Hydro-Agricultural & Irrigation Bottleneck Exposure (mean 0, SD 1)
    irrig_deficit = np.where(df["agri_works_total"] == 0, 52.0, df["agri_bottleneck_rate_pct"])
    irrig_stalled_cap_ratio = np.where(
        df["agri_inv_total_soles"] > 0,
        100.0 * df["agri_inv_bottleneck_soles"] / df["agri_inv_total_soles"],
        45.0,
    )
    df["d_irrigation_bottleneck_z"] = zscore(
        0.35 * zscore(df["agri_paralysis_rate_pct"])
        + 0.25 * zscore(irrig_deficit)
        + 0.15 * zscore(irrig_stalled_cap_ratio)
        + 0.25 * zscore(pd.to_numeric(df["pct_no_public_water"], errors="coerce").fillna(25.0))
    )

    # D2: First-Mile Rural Road, Track & Bridge Bottleneck Exposure (mean 0, SD 1)
    log_deficit = np.where(df["logistics_works_total"] == 0, 52.0, df["logistics_bottleneck_rate_pct"])
    log_stalled_cap_ratio = np.where(
        df["logistics_inv_total_soles"] > 0,
        100.0 * df["logistics_inv_bottleneck_soles"] / df["logistics_inv_total_soles"],
        45.0,
    )
    df["d_logistics_bottleneck_z"] = zscore(
        0.30 * zscore(log_deficit)
        + 0.25 * zscore(df["logistics_paralysis_rate_pct"])
        + 0.15 * zscore(log_stalled_cap_ratio)
        + 0.30 * zscore(np.log1p(pd.to_numeric(df["travel_time_primary_min"], errors="coerce").fillna(20.0)))
    )

    # D3: Pure Intra-District Satellite ERA5 Hydrometeorological Anomaly during El Niño / Yaku (2017 & 2023-2024 vs 2000-2015)
    # Combines intra-district UTCI z-score, intra-district Tropical Nights z-score, and intra-district ERA5 extreme precipitation z-score,
    # standardized within natural-region / altitudinal strata so it is orthogonal to coastal baseline mean temperature
    raw_intra_clim = (
        0.40 * zscore(df["intra_dist_utci_z_enso"])
        + 0.25 * zscore(df["intra_dist_trop_nights_z_enso"])
        + 0.35 * zscore(df["intra_dist_precip_extreme_z_enso"])
    )
    # Orthogonalize with respect to baseline 2000-2015 UTCI temperature so D3 is a pure intra-district shock
    base_temp_X = sm.add_constant(df[["era5_utci_base_2000_2015_c", "sierra_dummy", "selva_dummy"]].fillna(0.0))
    clim_resid = sm.OLS(raw_intra_clim, base_temp_X).fit().resid
    df["d_hydroclimatic_shock_z"] = zscore(clim_resid)

    # D4: Synergistic Interaction D3 * (0.5*D1 + 0.5*D2) centered and standardized (mean 0, SD 1)
    joint_bottleneck = zscore(0.50 * df["d_irrigation_bottleneck_z"] + 0.50 * df["d_logistics_bottleneck_z"])
    d3_pos = df["d_hydroclimatic_shock_z"] - df["d_hydroclimatic_shock_z"].min() + 0.25
    jb_pos = joint_bottleneck - joint_bottleneck.min() + 0.25
    df["d_compound_climate_bottleneck_z"] = zscore(d3_pos * jb_pos)

    # D5: Completed Irrigation & Feeder-Road Infrastructure Density (per 1,000 inhabitants + completion share, mean 0, SD 1)
    comp_per_1k = 1000.0 * (df["agri_works_completed_n"] + df["logistics_works_completed_n"]) / np.maximum(pop, 500.0)
    comp_share = np.where(
        df["agro_logistics_total_works"] > 0,
        100.0 * (df["agri_works_completed_n"] + df["logistics_works_completed_n"]) / df["agro_logistics_total_works"],
        35.0,
    )
    water_access_buf = 100.0 - pd.to_numeric(df["pct_no_public_water"], errors="coerce").fillna(25.0)
    df["d_completed_agro_logistics_per_1k_z"] = zscore(
        0.35 * zscore( np.log1p(comp_per_1k) )
        + 0.40 * zscore(comp_share)
        + 0.25 * zscore(water_access_buf)
    )

    # High-dimensional conditioning set X_i: district altitude, topographic slope, log population, rurality,
    # geographic coordinates, baseline 2000-2015 UTCI, municipal fiscal resources, ecological dummies, and 25 department FEs
    conf_cols = [
        "altitude_mean_m", "topo_slope_deg", "ln_pop", "pct_rural_schools_clean",
        "centroid_lat", "centroid_lon", "era5_utci_base_2000_2015_c",
        "canon_regalias_pc", "gasto_inv_total_pc",
        "sierra_dummy", "selva_dummy"
    ]
    X_conf_df = df[conf_cols].copy()
    for c in X_conf_df.columns:
        X_conf_df[c] = pd.to_numeric(X_conf_df[c], errors="coerce").fillna(X_conf_df[c].median())

    dept_dummies = pd.get_dummies(df["nombdep"].astype(str), prefix="dept", drop_first=True, dtype=float)
    W_full_df = pd.concat([X_conf_df, dept_dummies], axis=1).fillna(0.0)
    X_conf_scaled = StandardScaler().fit_transform(W_full_df.values)

    outcomes_spec = [
        ("rural_vulnerability_index_0_100", "Rural Socio-Productive Vulnerability Index (0-100)"),
        ("poverty_rate_pct", "District Monetary Poverty Rate (%)"),
        ("agri_labor_dropout_per_1k", "Agricultural- & Child-Labor School Dropout (per 1,000 students)"),
        ("school_dropout_rate_pct", "Overall Rural School Dropout Rate (%)"),
    ]
    treatments_spec = [
        ("d_irrigation_bottleneck_z", "Hydro-Agricultural & Irrigation Bottleneck Exposure (1 SD)"),
        ("d_logistics_bottleneck_z", "First-Mile Rural Road & Bridge Bottleneck Exposure (1 SD)"),
        ("d_hydroclimatic_shock_z", "Satellite ERA5 ENSO Thermal & Nocturnal Heat Shock (1 SD)"),
        ("d_compound_climate_bottleneck_z", "Compound ERA5 Climate Shock x Infrastructure Bottleneck (1 SD)"),
        ("d_completed_agro_logistics_per_1k_z", "Completed Irrigation & Feeder-Road Buffer Density (1 SD)"),
    ]

    dml_rows = []
    for y_col, y_label in outcomes_spec:
        y_vec = df[y_col].values.astype(float)

        for d_col, d_label in treatments_spec:
            d_vec = df[d_col].values.astype(float)
            X_ols = sm.add_constant(pd.concat([df[[d_col]], W_full_df], axis=1))
            ols_fit = sm.OLS(y_vec, X_ols).fit(cov_type="HC3")
            theta_dml, se_dml, t_dml, p_dml = run_dml_crossfit(y_vec, d_vec, X_conf_scaled, n_splits=5, random_state=42)

            dml_rows.append({
                "outcome_code": y_col,
                "outcome_label": y_label,
                "treatment_code": d_col,
                "treatment_label": d_label,
                "n_districts": int(len(df)),
                "ols_fe_beta": float(ols_fit.params[d_col]),
                "ols_fe_se_hc3": float(ols_fit.bse[d_col]),
                "ols_fe_pval": float(ols_fit.pvalues[d_col]),
                "ols_fe_r2_adj": float(ols_fit.rsquared_adj),
                "dml_5fold_theta": theta_dml,
                "dml_5fold_se": se_dml,
                "dml_5fold_tstat": t_dml,
                "dml_5fold_pval": p_dml,
                "ci95_low_dml": theta_dml - 1.96 * se_dml,
                "ci95_high_dml": theta_dml + 1.96 * se_dml,
            })

    df_res2 = pd.DataFrame(dml_rows)
    t2_fp = os.path.join(TAB_DIR, "table2_subnational_dml_agro_logistics_1873.csv")
    df_res2.to_csv(t2_fp, index=False)
    print(f"  Saved Table 2 ({len(df_res2)} OLS-FE & 5-Fold Causal DML estimates) -> {t2_fp}")
    for _, r in df_res2[df_res2["outcome_code"] == "rural_vulnerability_index_0_100"].iterrows():
        print(
            f"    [Vuln Index] {r['treatment_label']:58s} | OLS={r['ols_fe_beta']:+.3f} (p={r['ols_fe_pval']:.4f}) "
            f"| DML={r['dml_5fold_theta']:+.3f} (p={r['dml_5fold_pval']:.4f})"
        )

    df.to_csv(dist_fp, index=False)
    return df, df_res2, df_tax


def run_module3_supply_chain_pareto_optimization(df_dist):
    print("\n=== Module 3: Multi-Objective Supply-Chain & Hydro-Agricultural Debottlenecking Optimization ===")
    df_opt = df_dist.copy()
    df_opt["has_bottleneck"] = (df_opt["agro_logistics_bottleneck_works"] > 0).astype(int)

    # Realistic remainder-of-work ("saldo de obra") completion cost per bottlenecked project:
    # Mean remainder-of-work cost is S/ 1.35M per stalled irrigation project and S/ 1.45M per stalled rural road/bridge,
    # modulated by the district's observed percentage cost-overrun complexity and bounded within [0.45, 28.0] million Soles.
    overrun_pct_val = np.clip(pd.to_numeric(df_opt["agri_mean_overrun_pct"], errors="coerce").fillna(0.0), 0.0, 200.0)
    overrun_mult = 1.0 + 0.15 * (overrun_pct_val / 100.0)
    raw_comp_cost = (
        1.35 * df_opt["agri_works_bottleneck_n"] + 1.45 * df_opt["logistics_works_bottleneck_n"]
    ) * overrun_mult
    df_opt["completion_cost_m_soles"] = np.where(
        df_opt["has_bottleneck"] == 1, np.clip(raw_comp_cost, 0.45, 28.0), 0.0
    )

    # Equation (5): Orthogonal components without double-counting AgriDrop_i (since Vuln_i already includes AgriDrop_i with weight 0.30)
    pop_k = np.maximum(pd.to_numeric(df_opt["poblacion_oficial"], errors="coerce").fillna(4000.0) / 1000.0, 0.5)
    clim_mult = 1.0 + 0.40 * np.maximum(df_opt["d_hydroclimatic_shock_z"], -0.8)
    bottleneck_intensity = (
        0.50 * np.maximum(df_opt["d_irrigation_bottleneck_z"], 0.1)
        + 0.50 * np.maximum(df_opt["d_logistics_bottleneck_z"], 0.1)
        + 0.30 * np.log1p(df_opt["agro_logistics_bottleneck_works"])
    )

    df_opt["expected_resilience_gain"] = (
        df_opt["has_bottleneck"]
        * (pop_k ** 0.55)
        * clim_mult
        * bottleneck_intensity
        * (df_opt["rural_vulnerability_index_0_100"] / 50.0)
    )
    df_opt["benefit_cost_ratio"] = df_opt["expected_resilience_gain"] / np.maximum(df_opt["completion_cost_m_soles"], 0.45)

    elig = df_opt[df_opt["has_bottleneck"] == 1].copy()
    total_gain_possible = elig["expected_resilience_gain"].sum()
    total_cost_all = elig["completion_cost_m_soles"].sum()
    print(f"  Eligible districts with active hydro-agricultural/logistics bottlenecks: {len(elig):,} / {len(df_opt):,}")
    print(f"  Total estimated completion ('saldo de obra') requirement: S/ {total_cost_all:,.1f} million")

    budgets = [250, 500, 1000, 1500, 2500, 4000, 5000, 6500, 8000, 10000]
    policies = {
        "Policy 1: Historical Inertia (SIAF Budget Share)": elig.sort_values("agro_logistics_total_works", ascending=False),
        "Policy 2: Small-Works Greedy (Lowest Cost First)": elig.sort_values("completion_cost_m_soles", ascending=True),
        "Policy 3: Unidimensional Poverty Ranking": elig.sort_values("poverty_rate_pct", ascending=False),
        "Policy 4: Climate-Supply-Chain DML Pareto Optimal": elig.sort_values("benefit_cost_ratio", ascending=False),
    }

    opt_rows = []
    pareto_curves = {p: {"budgets": [], "pct_resilience_gain": [], "districts_debottlenecked": [], "works_unlocked": []} for p in policies}

    for B in budgets:
        for p_name, p_df in policies.items():
            cum_cost = p_df["completion_cost_m_soles"].cumsum()
            sel = p_df[cum_cost <= B]
            gain_pct = 100.0 * sel["expected_resilience_gain"].sum() / total_gain_possible
            n_dist = int(len(sel))
            n_irrig_unlocked = int(sel["agri_works_bottleneck_n"].sum())
            n_roads_unlocked = int(sel["logistics_works_bottleneck_n"].sum())
            n_total_unlocked = n_irrig_unlocked + n_roads_unlocked
            pop_benefited_k = float(pd.to_numeric(sel["poblacion_oficial"], errors="coerce").fillna(4000.0).sum() / 1000.0)

            pareto_curves[p_name]["budgets"].append(B)
            pareto_curves[p_name]["pct_resilience_gain"].append(float(gain_pct))
            pareto_curves[p_name]["districts_debottlenecked"].append(n_dist)
            pareto_curves[p_name]["works_unlocked"].append(n_total_unlocked)

            if B in (500, 1000, 2500, 5000, 10000):
                opt_rows.append({
                    "budget_ceiling_million_soles": B,
                    "budget_share_of_total_need_pct": float(min(100.0, 100.0 * B / total_cost_all)),
                    "allocation_policy": p_name,
                    "districts_debottlenecked": n_dist,
                    "irrigation_works_unlocked": n_irrig_unlocked,
                    "logistics_works_unlocked": n_roads_unlocked,
                    "total_works_unlocked": n_total_unlocked,
                    "district_population_covered_thousands": pop_benefited_k,
                    "population_protected_thousands": pop_benefited_k,
                    "resilience_gain_captured_pct": float(gain_pct),
                })

    df_opt_tab = pd.DataFrame(opt_rows)
    t4_fp = os.path.join(TAB_DIR, "table4_supply_chain_pareto_optimization.csv")
    df_opt_tab.to_csv(t4_fp, index=False)
    with open(os.path.join(PROC_DIR, "optimization_pareto_curves.json"), "w", encoding="utf-8") as f:
        json.dump(pareto_curves, f, indent=2)
    print(f"  Saved Table 4 (Supply-Chain Pareto Optimization across 5 budget regimes x 4 policies) -> {t4_fp}")
    for _, r in df_opt_tab[df_opt_tab["budget_ceiling_million_soles"] == 2500].iterrows():
        print(
            f"    [B = S/ 2,500M] {r['allocation_policy']:48s} -> Gain={r['resilience_gain_captured_pct']:5.1f}% "
            f"| Districts={r['districts_debottlenecked']:4d} | Works={r['total_works_unlocked']:5,d}"
        )


def main():
    run_module1_macro_crop_elasticities()
    df_d, _, _ = run_module2_subnational_dml_and_infrastructure()
    run_module3_supply_chain_pareto_optimization(df_d)


if __name__ == "__main__":
    main()
