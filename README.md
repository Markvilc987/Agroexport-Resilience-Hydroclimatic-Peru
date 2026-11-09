# Hydroclimatic Anomalies, First-Mile Supply-Chain Bottlenecks, and Crop Resilience: Multi-Scale Evidence from 26-Year Satellite Reanalysis, 40,538 Infrastructure Works, and Debiased Machine Learning in Peru

**Author:** Juan Marcos Vilchez-Canchari $^{a,b,*}$  
$^a$ *Escuela de Posgrado, Universidad César Vallejo, Lima, Peru*  
$^b$ *Universidad Privada San Juan Bautista, Lima, Peru*  
$^*$ *Corresponding author. Email address: jvilchezc@ucvvirtual.edu.pe*

**Target Q1 Journal:** *Agricultural Systems* (Elsevier, Q1) / *Socio-Economic Planning Sciences* (Elsevier, Q1)

---

## 1. Repository Architecture & 100% Real Datasets

- `data/raw/`:
  - `ECMWF_utci_monthly_stats/` & `ECMWF_utci_yearly_stats/`: 319 monthly and 26 annual official ECMWF Copernicus ERA5-HEAT Universal Thermal Climate Index (`UTCI`) NetCDF-4/HDF5 grids (`2000–2025`, $0.25^\circ \times 0.25^\circ$ resolution across Peru, downscaled with district elevation lapse rates from 67,145 georeferenced locales).
  - `ECMWF_tropical_nights_monthly_stats/` & `ECMWF_tropical_nights_yearly_stats/`: 319 monthly and 26 annual official ECMWF Copernicus ERA5-HEAT Nocturnal Heat Stress (`Tropical Nights >20°C`) NetCDF-4/HDF5 grids (`2000–2025`).
  - `bcrp_full_agro_export_series_2000_2025.json` & `bcrp_exports_and_crops_extra_2000_2025.json`: 59 official monthly time series downloaded directly from the Central Reserve Bank of Peru (`BCRP`) / `MIDAGRI` API (`2000–2025`, $N = 312$ months), covering 24 modeled series in Table 1: 3 macro-sectoral GDP indices (`Agricultural GDP`, `Livestock GDP`, `Primary Processing Manufacturing GDP`), 3 composite baskets (`Core Agro-Export Basket`, `Total High-Value Agro-Export Basket`, `Domestic Food-Security Staple Basket`), and 18 individual crop production volume series (`Mango`, `Tahiti/Sutil Lime`, `Table Grapes`, `Asparagus`, `Mandarin Citrus`, `Sweet Orange`, `Olive`, `Coffee`, `Cocoa`, `Quinoa`, `Yellow/Red Onion`, `Garlic`, `Tomato`, `Sugarcane`, `Potato`, `Paddy Rice`, `Starchy Maize`, and `Hard Yellow Maize`).
  - `worldbank_fao_peru_agriculture_1990_2024.json`: 13 official annual macro-agricultural indicators from the World Bank / FAOSTAT API (`1990–2024`).
  - `noaa_oni_monthly_1950_2025.txt` & `copernicus_era5_climate_covariates.csv`: Official NOAA Oceanic Niño Index (`ONI`) monthly SST anomalies and Copernicus ERA5 covariates.
  - `public_works_registry_191180.parquet` & `district_master_atlas_1873.parquet`: Geo-referenced public works registry ($N = 191,180$ total works, from which $N = 40,538$ hydro-agricultural and rural transport works are extracted across 1,497 bottlenecked districts) and district master atlas ($N = 1,873$ districts).
- `data/processed/`:
  - `macro_monthly_agroexport_era5_panel_2000_2025.csv` ($N = 312$ months $\times 63$ variables)
  - `macro_annual_agroexport_era5_wb_2000_2025.csv` ($N = 26$ years $\times 73$ variables)
  - `district_agro_logistics_resilience_1873.csv` & `.parquet` ($N = 1,873$ districts)
  - `agro_and_logistics_public_works_40537.parquet` ($N = 40,538$ hydro-agricultural and rural transport projects)
  - `optimization_pareto_curves.json` (Multi-objective knapsack Pareto curves across 10 budget ceilings and 4 policy rules)
