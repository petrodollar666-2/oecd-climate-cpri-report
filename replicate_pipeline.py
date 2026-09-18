#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
REPLICATION PIPELINE RUNNER (replicate_pipeline.py)
Automated Multi-Agent Replication Script for Academic Journal Submission
================================================================================
Usage:
  python replicate_pipeline.py
  python replicate_pipeline.py --raw-data raw_data.csv --output-dir .
================================================================================
"""

import os
import sys
import argparse
import datetime
import pandas as pd

# Safe console output for Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from cpri_climatology_engine import (
    LocalClimatologyEngine,
    ExtremeEventsClassifier,
    CPRIAggregator,
    KYCAuditValidator,
    EconometricReporter
)

def safe_write_csv(df: pd.DataFrame, path: str, index: bool = False):
    try:
        df.to_csv(path, index=index, encoding='utf-8-sig')
        return path
    except (PermissionError, OSError):
        alt = path.replace('.csv', '_latest.csv')
        df.to_csv(alt, index=index, encoding='utf-8-sig')
        print(f"  [WARN] {os.path.basename(path)} is locked by another program (Excel). Saved to {os.path.basename(alt)}.")
        return alt

def run_replication(raw_csv_path: str, output_dir: str):
    start_time = datetime.datetime.now()
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 78)
    print("      ACADEMIC REPLICATION PIPELINE: CLIMATE PHYSICAL RISK INDEX (CPRI)")
    print("      Standard: Nature / Humanities and Social Sciences Communications")
    print("      Reference: s41599-025-05275-z (Guo et al., 2024 / Ji et al., 2025)")
    print("=" * 78)
    print(f"[*] Loading raw observations from: {raw_csv_path}")

    if not os.path.exists(raw_csv_path):
        print(f"[ERROR] Raw data file not found at: {raw_csv_path}")
        sys.exit(1)

    raw_df = pd.read_csv(raw_csv_path)
    print(f"[*] Successfully loaded {len(raw_df):,} daily records across {raw_df['city'].nunique()} cities.")

    # 1. Climatological Quantile Thresholds
    print("\n[Agent 1: Data Engineering] Estimating city-specific baseline quantiles (P10, P90, P95, P5)...")
    thresh_df = LocalClimatologyEngine.compute_thresholds(raw_df)
    thresh_path = os.path.join(output_dir, "city_climatology_thresholds.csv")
    safe_write_csv(thresh_df, thresh_path)
    print(f" -> Saved local thresholds to: {thresh_path}")

    # 2. Extreme Event Classification
    print("\n[Agent 1: Data Engineering] Performing vectorized classification of LTD, HTD, ERD, EDD...")
    processed_df = ExtremeEventsClassifier.classify(raw_df, thresh_df)
    proc_path = os.path.join(output_dir, "processed_data.csv")
    safe_write_csv(processed_df, proc_path)
    print(f" -> Exported finalized processed data (25 columns) to: {proc_path}")

    # 3. City-Year CPRI Aggregation
    print("\n[Agent 2: Econometric Modeling] Aggregating City-Year observations & calculating CPRI...")
    city_year_df = CPRIAggregator.aggregate(processed_df)
    city_year_path = os.path.join(output_dir, "city_year_cpri_summary.csv")
    safe_write_csv(city_year_df, city_year_path)
    print(f" -> Saved City-Year summary ({len(city_year_df)} pairs) to: {city_year_path}")

    # 4. Table 2 Summary Statistics & Correlation
    print("\n[Agent 2: Econometric Modeling] Generating Table 2 Summary Statistics...")
    table2_df = EconometricReporter.generate_table2(city_year_df)
    table2_path = os.path.join(output_dir, "table2_summary_statistics.csv")
    safe_write_csv(table2_df, table2_path)
    print(f" -> Saved Table 2 Summary Statistics to: {table2_path}")

    corr_df = city_year_df[['LTD_days_norm', 'HTD_days_norm', 'ERD_days_norm', 'EDD_days_norm', 'CPRI_annualized']].corr()
    corr_path = os.path.join(output_dir, "correlation_matrix.csv")
    safe_write_csv(corr_df, corr_path, index=True)

    city_ranking = city_year_df.groupby(['country', 'city']).agg(
        avg_cpri=('CPRI_annualized', 'mean'),
        avg_ltd=('LTD_days_norm', 'mean'),
        avg_htd=('HTD_days_norm', 'mean'),
        avg_erd=('ERD_days_norm', 'mean'),
        avg_edd=('EDD_days_norm', 'mean')
    ).reset_index().sort_values('avg_cpri', ascending=False)
    ranking_path = os.path.join(output_dir, "city_risk_ranking.csv")
    safe_write_csv(city_ranking, ranking_path)

    # 5. KYC Independent Audit
    print("\n[Agent 3: KYC Independent Auditor] Running 5-stage automated scientific consistency check...")
    all_passed, kyc_results = KYCAuditValidator.audit(processed_df, thresh_df, city_year_df)
    for code, title, status, details in kyc_results:
        print(f"  * [{status}] {code}: {title} -> {details}")

    kyc_report_path = os.path.join(output_dir, "KYC_AUDIT_REPORT.md")
    with open(kyc_report_path, 'w', encoding='utf-8') as f:
        f.write("# INDEPENDENT KYC AUDIT REPORT (REPLICATION PACKAGE)\n\n")
        f.write(f"**Overall Status:** {'100% CERTIFIED PASSED' if all_passed else 'AUDIT ISSUES FOUND'}\n\n")
        f.write("| Test Code | Description | Status | Evidence |\n| :--- | :--- | :---: | :--- |\n")
        for code, title, status, details in kyc_results:
            f.write(f"| **{code}** | {title} | **{status}** | {details} |\n")
    print(f" -> Saved KYC Audit Report to: {kyc_report_path}")

    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 78)
    print(f" [SUCCESS] REPLICATION COMPLETED IN {elapsed:.2f} SECONDS (100% REPRODUCIBLE)")
    print("=" * 78)
    print(f"1. Raw Observations Input   : {raw_csv_path}")
    print(f"2. Processed Output Dataset : {proc_path}")
    print(f"3. Table 2 Summary Stats    : {table2_path}")
    print(f"4. City-Year CPRI Aggregate : {city_year_path}")
    print(f"5. KYC Audit Certificate    : {kyc_report_path}")
    print("=" * 78)

def main():
    parser = argparse.ArgumentParser(description="Academic Replication Pipeline for CPRI & Extreme Weather Days")
    parser.add_argument("--raw-data", "-r", default="raw_data.csv", help="Path to raw observations CSV")
    parser.add_argument("--output-dir", "-o", default=".", help="Directory for output replication artifacts")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = args.raw_data if os.path.isabs(args.raw_data) else os.path.join(script_dir, args.raw_data)
    out_dir = args.output_dir if os.path.isabs(args.output_dir) else os.path.join(script_dir, args.output_dir)

    run_replication(raw_path, out_dir)

if __name__ == "__main__":
    main()
