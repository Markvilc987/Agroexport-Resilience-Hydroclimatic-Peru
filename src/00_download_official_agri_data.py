#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_download_official_agri_data.py
Queries official BCRP API (Banco Central de Reserva del Peru) and World Bank / FAO
Open Data APIs for real Peruvian agricultural production, crop-specific output,
traditional & non-traditional agro-exports, and macro-agricultural indicators
(2000-2025), saving them into data/raw/.
"""

import os
import json
import ssl
import urllib.request

BASE_DIR = "/Users/marcos/Personal/1. PROYECTOS/1. ARTICULOS CIENTIFICOS"
PROJ_DIR = os.path.join(BASE_DIR, "15_Resiliencia_Agroexportadora_Hidroclimatica_Peru")
RAW_DIR = os.path.join(PROJ_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
}


def fetch_json(url, timeout=25):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="replace"))


def main():
    print("=== 1. Discovering & Downloading Official BCRP Agricultural GDP, Crop & Agroexport Series ===")
    # Probe key BCRP series ranges:
    # PN01710BM..PN01749BM (PBI y Produccion Agropecuaria mensual)
    # PN01750BM..PN01799BM (Indices y volumenes agropecuarios / exportaciones)
    # PN01470BM..PN01510BM (Exportaciones por sector economico: Tradicionales agricolas y No tradicionales agropecuarias)
    # PN01750AM..PN01795AM (Series mensuales adicionales de comercio exterior y produccion)
    candidate_codes = (
        [f"PN{i:05d}BM" for i in range(1710, 1775)]
        + [f"PN{i:05d}BM" for i in range(1470, 1515)]
        + [f"PN{i:05d}AM" for i in range(1750, 1795)]
    )

    keywords = [
        "agropecuari", "agrícol", "agricol", "pecuari", "papa", "arroz", "maíz", "maiz",
        "café", "cafe", "caña", "espárrago", "esparrago", "uva", "palta", "arándano",
        "arandano", "mango", "cacao", "algodón", "algodon", "azúcar", "azucar",
        "exportacion", "tradicional", "no tradicional", "pbi", "pesca", "manufactura"
    ]

    full_bcrp_series = {}
    # Query in batches of 15 directly over 2000-1 to 2025-12
    for i in range(0, len(candidate_codes), 15):
        batch = candidate_codes[i : i + 15]
        url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{'-'.join(batch)}/json/2000-1/2025-12/esp"
        try:
            data = fetch_json(url, timeout=25)
            series_meta = data.get("config", {}).get("series", [])
            periods = data.get("periods", [])
            if not series_meta or not periods:
                continue
            for idx, s_obj in enumerate(series_meta):
                s_name = s_obj.get("name", "")
                if any(k in s_name.lower() for k in keywords):
                    # Extract series values across all periods
                    s_periods = []
                    for p in periods:
                        vals = p.get("values", [])
                        v = vals[idx] if idx < len(vals) else "n.d."
                        s_periods.append({"name": p.get("name"), "value": v})
                    key_id = f"BCRP_S{len(full_bcrp_series)+1:03d}"
                    full_bcrp_series[key_id] = {
                        "id": key_id,
                        "name": s_name,
                        "periods": s_periods,
                    }
                    print(f"  [BCRP] {key_id}: {s_name} ({len(s_periods)} months)")
        except Exception as e:
            print(f"  Batch {i} note: {e}")

    with open(os.path.join(RAW_DIR, "bcrp_full_agro_export_series_2000_2025.json"), "w", encoding="utf-8") as f:
        json.dump(full_bcrp_series, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(full_bcrp_series)} BCRP monthly series (2000-2025).")

    print("\n=== 2. Downloading World Bank / FAOSTAT Official Agricultural Series for Peru (1990-2024) ===")
    wb_indicators = {
        "AG.PRD.CROP.XD": "Crop production index (2014-2016 = 100)",
        "AG.PRD.FOOD.XD": "Food production index (2014-2016 = 100)",
        "AG.PRD.LVSK.XD": "Livestock production index (2014-2016 = 100)",
        "AG.YLD.CREL.KG": "Cereal yield (kg per hectare)",
        "AG.LND.CREL.HA": "Land under cereal production (hectares)",
        "NV.AGR.TOTL.CD": "Agriculture, forestry, and fishing, value added (current US$)",
        "NV.AGR.TOTL.KD": "Agriculture, forestry, and fishing, value added (constant 2015 US$)",
        "NV.AGR.TOTL.ZS": "Agriculture, forestry, and fishing, value added (% of GDP)",
        "AG.LND.IRIG.AG.ZS": "Agricultural irrigated land (% of total agricultural land)",
        "AG.CON.FERT.ZS": "Fertilizer consumption (kilograms per hectare of arable land)",
        "SL.AGR.EMPL.ZS": "Employment in agriculture (% of total employment)",
        "TX.VAL.FOOD.ZS.UN": "Food exports (% of merchandise exports)",
        "TX.VAL.AGRI.ZS.UN": "Agricultural raw materials exports (% of merchandise exports)",
        "ER.H2O.FWAG.ZS": "Annual freshwater withdrawals, agriculture (% of total freshwater withdrawal)",
    }
    wb_data = {}
    for ind_code, ind_label in wb_indicators.items():
        url = f"https://api.worldbank.org/v2/country/PER/indicator/{ind_code}?date=1990:2024&format=json&per_page=100"
        try:
            res = fetch_json(url, timeout=20)
            if isinstance(res, list) and len(res) > 1 and isinstance(res[1], list):
                obs = [
                    {"year": int(item["date"]), "value": item["value"]}
                    for item in res[1]
                    if item.get("value") is not None
                ]
                obs.sort(key=lambda x: x["year"])
                wb_data[ind_code] = {"indicator": ind_label, "observations": obs}
                print(f"  [WB/FAO] {ind_code} ({len(obs)} yrs): {ind_label}")
        except Exception as e:
            print(f"  [WB/FAO] Error {ind_code}: {e}")

    with open(os.path.join(RAW_DIR, "worldbank_fao_peru_agriculture_1990_2024.json"), "w", encoding="utf-8") as f:
        json.dump(wb_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(wb_data)} World Bank / FAOSTAT series.")


if __name__ == "__main__":
    main()
