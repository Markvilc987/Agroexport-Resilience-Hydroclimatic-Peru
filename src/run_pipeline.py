#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py
Executes the full empirical data assembly, econometric/DML modeling, supply-chain
Pareto optimization, 300 DPI figure generation, and manuscript compilation + verification pipeline.
"""

import os
import sys
import importlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

m01 = importlib.import_module("01_build_agroexport_hydroclimatic_dataset")
m02 = importlib.import_module("02_econometric_dml_and_supply_chain_optimization")
m03 = importlib.import_module("03_generate_figures_300dpi")
m04 = importlib.import_module("04_build_manuscript_package")

if __name__ == "__main__":
    m01.main()
    m02.main()
    m03.main()
    m04.main()
    print("\n=== ALL DATA ASSEMBLY, ECONOMETRICS, DML, PARETO OPTIMIZATION, FIGURES & MANUSCRIPT PACKAGE COMPLETED SUCCESSFULLY ===")
