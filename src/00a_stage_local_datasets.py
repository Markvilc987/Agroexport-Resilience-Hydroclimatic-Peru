#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00a_stage_local_datasets.py
Stages local official satellite ERA5-HEAT NetCDF grids (yearly and monthly UTCI
and Tropical Nights 2000-2025), Copernicus ERA5 climate covariates (including
volumetric soil moisture), NOAA ONI index, and harmonized subnational datasets
into data/raw/ and data/spatial/.
"""

import os
import shutil

BASE_DIR = "/Users/marcos/Personal/1. PROYECTOS/1. ARTICULOS CIENTIFICOS"
PROJ_DIR = os.path.join(BASE_DIR, "15_Resiliencia_Agroexportadora_Hidroclimatica_Peru")
RAW_DIR = os.path.join(PROJ_DIR, "data", "raw")
SPATIAL_DIR = os.path.join(PROJ_DIR, "data", "spatial")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(SPATIAL_DIR, exist_ok=True)


def main():
    era5_base = os.path.join(BASE_DIR, "Thermal comfort indices derived from ERA5 reanalysis")
    utci_yr_dst = os.path.join(RAW_DIR, "ECMWF_utci_yearly_stats")
    tn_yr_dst = os.path.join(RAW_DIR, "ECMWF_tropical_nights_yearly_stats")
    utci_mo_dst = os.path.join(RAW_DIR, "ECMWF_utci_monthly_stats")
    tn_mo_dst = os.path.join(RAW_DIR, "ECMWF_tropical_nights_monthly_stats")
    for d in [utci_yr_dst, tn_yr_dst, utci_mo_dst, tn_mo_dst]:
        os.makedirs(d, exist_ok=True)

    counts = {"utci_yr": 0, "tn_yr": 0, "utci_mo": 0, "tn_mo": 0}
    for fn in sorted(os.listdir(era5_base)):
        if not fn.endswith(".nc"):
            continue
        src = os.path.join(era5_base, fn)
        if fn.startswith("ECMWF_utci_yearly_stats_"):
            dst = os.path.join(utci_yr_dst, fn)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            counts["utci_yr"] += 1
        elif fn.startswith("ECMWF_thermal_comfort_yearly_statistics_tropical_nights_"):
            dst = os.path.join(tn_yr_dst, fn)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            counts["tn_yr"] += 1
        elif fn.startswith("ECMWF_utci_monthly_stats_"):
            dst = os.path.join(utci_mo_dst, fn)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            counts["utci_mo"] += 1
        elif fn.startswith("ECMWF_thermal_comfort_monthly_statistics_tropical_nights_"):
            dst = os.path.join(tn_mo_dst, fn)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            counts["tn_mo"] += 1

    print(f"Staged ERA5 NetCDF files: {counts}")

    other_sources = [
        (
            os.path.join(BASE_DIR, "01_Dengue_SpatioTemporal_AI_Peru/data/raw/copernicus_era5_climate_covariates.csv"),
            os.path.join(RAW_DIR, "copernicus_era5_climate_covariates.csv"),
        ),
        (
            os.path.join(BASE_DIR, "01_Dengue_SpatioTemporal_AI_Peru/data/raw/oni.ascii.txt"),
            os.path.join(RAW_DIR, "noaa_oni_monthly_1950_2025.txt"),
        ),
        (
            os.path.join(BASE_DIR, "14_Atlas_Multidominio_Subnacional_Peru_SciData/data/harmonized_fair/Data_Record_1_District_Master_Atlas_1873.parquet"),
            os.path.join(RAW_DIR, "district_master_atlas_1873.parquet"),
        ),
        (
            os.path.join(BASE_DIR, "14_Atlas_Multidominio_Subnacional_Peru_SciData/data/harmonized_fair/Data_Record_4_Public_Works_Registry_191180.parquet"),
            os.path.join(RAW_DIR, "public_works_registry_191180.parquet"),
        ),
    ]
    for src, dst in other_sources:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
        print(f"Staged {os.path.basename(dst)} ({os.path.getsize(dst)/1e6:.2f} MB)")

    shp_dir = os.path.join(BASE_DIR, "14_Atlas_Multidominio_Subnacional_Peru_SciData/data/spatial")
    for fn in os.listdir(shp_dir):
        if fn.startswith("v_distritos_2023"):
            s, d = os.path.join(shp_dir, fn), os.path.join(SPATIAL_DIR, fn)
            if not os.path.exists(d):
                shutil.copy2(s, d)
    print("Staged INEI 2023 district boundaries shapefile in data/spatial/.")


if __name__ == "__main__":
    main()
