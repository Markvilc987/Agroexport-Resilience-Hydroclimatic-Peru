#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00b_fetch_bcrp_exports_usd.py
Fetches official BCRP monthly series of Peruvian Traditional Agricultural Exports
and Non-Traditional Agro-Exports (in US$ millions, 2000-2025), handling BCRP's
Latin-1 encoding and any non-existent code responses cleanly.
"""

import os
import re
import json
import ssl
import urllib.request

BASE_DIR = "/Users/marcos/Personal/1. PROYECTOS/1. ARTICULOS CIENTIFICOS"
PROJ_DIR = os.path.join(BASE_DIR, "15_Resiliencia_Agroexportadora_Hidroclimatica_Peru")
RAW_DIR = os.path.join(PROJ_DIR, "data", "raw")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
}


def fetch_bcrp_safe(codes_list, start_p="2000-1", end_p="2025-12"):
    url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{'-'.join(codes_list)}/json/{start_p}/{end_p}/esp"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        raw = resp.read()
    # BCRP sometimes encodes Spanish characters in iso-8859-1
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("latin-1", errors="replace")
    txt = txt.strip()
    if not txt.startswith("{"):
        return None
    return json.loads(txt)


def main():
    # Let's probe export series in small chunks of 5 across PN01470BM..PN01530BM and PN01775AM..PN01835AM
    ranges = (
        [f"PN{i:05d}BM" for i in range(1470, 1530)]
        + [f"PN{i:05d}AM" for i in range(1775, 1835)]
    )
    export_series = {}
    for i in range(0, len(ranges), 5):
        batch = ranges[i : i + 5]
        try:
            d = fetch_bcrp_safe(batch, "2000-1", "2025-12")
            if not d:
                continue
            series_meta = d.get("config", {}).get("series", [])
            periods = d.get("periods", [])
            for idx, s_obj in enumerate(series_meta):
                s_name = s_obj.get("name", "")
                s_periods = []
                for p in periods:
                    vals = p.get("values", [])
                    v = vals[idx] if idx < len(vals) else "n.d."
                    s_periods.append({"name": p.get("name"), "value": v})
                key_id = f"BCRP_EXP_{len(export_series)+1:03d}"
                export_series[key_id] = {
                    "id": key_id,
                    "name": s_name,
                    "periods": s_periods,
                }
                print(f"  [{key_id}] {s_name} ({len(s_periods)} months)")
        except Exception:
            # Try individual codes in batch if batch had a malformed code
            for code in batch:
                try:
                    d1 = fetch_bcrp_safe([code], "2000-1", "2025-12")
                    if not d1:
                        continue
                    s_meta = d1.get("config", {}).get("series", [])
                    periods = d1.get("periods", [])
                    if s_meta and periods:
                        s_name = s_meta[0].get("name", "")
                        s_periods = [
                            {"name": p.get("name"), "value": (p.get("values") or ["n.d."])[0]}
                            for p in periods
                        ]
                        key_id = f"BCRP_EXP_{len(export_series)+1:03d}"
                        export_series[key_id] = {
                            "id": key_id,
                            "code": code,
                            "name": s_name,
                            "periods": s_periods,
                        }
                        print(f"  [{key_id}] ({code}) {s_name} ({len(s_periods)} months)")
                except Exception:
                    pass

    out_fp = os.path.join(RAW_DIR, "bcrp_exports_and_crops_extra_2000_2025.json")
    with open(out_fp, "w", encoding="utf-8") as f:
        json.dump(export_series, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(export_series)} additional BCRP export/crop series to {out_fp}.")


if __name__ == "__main__":
    main()
