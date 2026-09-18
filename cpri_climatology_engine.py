#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
CPRI CLIMATOLOGY & ECONOMETRIC ENGINE (cpri_climatology_engine.py)
Standardized Replication Module based on Nature s41599-025-05275-z
(Guo et al., 2024 / Ji et al., 2025)

Core Scientific Capabilities:
  1. LocalClimatologyEngine  : Station-specific quantile threshold estimation.
  2. ExtremeEventsClassifier : Vectorized labeling of LTD, HTD, ERD, EDD days.
  3. CPRIAggregator          : City-Year composite climate physical risk index.
  4. KYCAuditValidator       : 5-stage automated scientific consistency verification.
  5. EconometricReporter     : Table 2 Summary Statistics generator.
================================================================================
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any

class LocalClimatologyEngine:
    """Computes city/station-specific baseline quantiles to avoid latitudinal bias."""
    @staticmethod
    def compute_thresholds(df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for city, grp in df.groupby('city'):
            p10_temp = grp['avgtemp_c'].quantile(0.10)
            p90_temp = grp['avgtemp_c'].quantile(0.90)
            p95_precip = grp['totalprecip_mm'].quantile(0.95)
            p05_humid = grp['avghumidity'].quantile(0.05)

            records.append({
                'city': city,
                'p10_temp_ltd': round(float(p10_temp), 2),
                'p90_temp_htd': round(float(p90_temp), 2),
                'p95_precip_erd': round(float(p95_precip), 2),
                'p05_humid_edd': round(float(p05_humid), 2),
                'mean_temp': round(float(grp['avgtemp_c'].mean()), 2),
                'mean_precip': round(float(grp['totalprecip_mm'].mean()), 2),
                'mean_humid': round(float(grp['avghumidity'].mean()), 2),
                'obs_count': len(grp)
            })
        return pd.DataFrame(records)


class ExtremeEventsClassifier:
    """Vectorized tagging of extreme events and mutual exclusivity enforcement."""
    @staticmethod
    def classify(df: pd.DataFrame, thresholds_df: pd.DataFrame) -> pd.DataFrame:
        # Clean any prior flag columns
        flag_cols = ['is_ltd', 'is_htd', 'is_erd', 'is_edd', 'daily_cpri', 
                     'p10_temp_ltd', 'p90_temp_htd', 'p95_precip_erd', 'p05_humid_edd']
        df = df.drop(columns=[c for c in flag_cols if c in df.columns])

        # Merge local thresholds
        merged = df.merge(thresholds_df[['city', 'p10_temp_ltd', 'p90_temp_htd', 'p95_precip_erd', 'p05_humid_edd']], on='city', how='left')

        # Compute extreme days
        merged['is_ltd'] = (merged['avgtemp_c'] <= merged['p10_temp_ltd']).astype(int)
        merged['is_htd'] = (merged['avgtemp_c'] >= merged['p90_temp_htd']).astype(int)
        merged['is_erd'] = ((merged['totalprecip_mm'] >= merged['p95_precip_erd']) & (merged['totalprecip_mm'] > 0)).astype(int)
        merged['is_edd'] = (merged['avghumidity'] <= merged['p05_humid_edd']).astype(int)

        # Collision prevention: LTD and HTD cannot co-occur on the same day
        collision = (merged['is_ltd'] == 1) & (merged['is_htd'] == 1)
        if collision.any():
            merged.loc[collision, 'is_ltd'] = 0
            merged.loc[collision, 'is_htd'] = 0

        # Daily composite risk count [0..4]
        merged['daily_cpri'] = merged['is_ltd'] + merged['is_htd'] + merged['is_erd'] + merged['is_edd']

        # Drop temporary merge columns
        output_cols = [c for c in merged.columns if c not in ['p10_temp_ltd', 'p90_temp_htd', 'p95_precip_erd', 'p05_humid_edd']]
        return merged[output_cols]


class CPRIAggregator:
    """Aggregates daily observations to City-Year level and computes CPRI indices."""
    @staticmethod
    def aggregate(df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        df_copy['year'] = pd.to_datetime(df_copy['date']).dt.year

        agg = df_copy.groupby(['country', 'country_code', 'city', 'year']).agg(
            total_days=('date', 'count'),
            LTD_days=('is_ltd', 'sum'),
            HTD_days=('is_htd', 'sum'),
            ERD_days=('is_erd', 'sum'),
            EDD_days=('is_edd', 'sum'),
            avg_temp=('avgtemp_c', 'mean'),
            total_precip=('totalprecip_mm', 'sum'),
            avg_humidity=('avghumidity', 'mean')
        ).reset_index()

        # Annualization factor for partial years
        agg['annual_factor'] = np.where(agg['total_days'] < 360, 365.25 / agg['total_days'], 1.0)
        agg['LTD_days_norm'] = agg['LTD_days'] * agg['annual_factor']
        agg['HTD_days_norm'] = agg['HTD_days'] * agg['annual_factor']
        agg['ERD_days_norm'] = agg['ERD_days'] * agg['annual_factor']
        agg['EDD_days_norm'] = agg['EDD_days'] * agg['annual_factor']

        # Composite CPRI formula from Nature Table 2:
        # CPRI = (LTD + HTD + ERD + EDD) / 4
        agg['CPRI_raw'] = (agg['LTD_days'] + agg['HTD_days'] + agg['ERD_days'] + agg['EDD_days']) / 4.0
        agg['CPRI_annualized'] = (agg['LTD_days_norm'] + agg['HTD_days_norm'] + agg['ERD_days_norm'] + agg['EDD_days_norm']) / 4.0

        # Z-score standardization
        mean_c = agg['CPRI_annualized'].mean()
        std_c = agg['CPRI_annualized'].std()
        agg['CPRI_zscore'] = (agg['CPRI_annualized'] - mean_c) / std_c

        # 0-100 normalized score
        min_c = agg['CPRI_annualized'].min()
        max_c = agg['CPRI_annualized'].max()
        agg['CPRI_score_100'] = ((agg['CPRI_annualized'] - min_c) / (max_c - min_c)) * 100.0

        return agg


class KYCAuditValidator:
    """Performs rigorous 5-stage academic verification of the dataset and calculations."""
    @staticmethod
    def audit(daily_df: pd.DataFrame, thresholds_df: pd.DataFrame, agg_df: pd.DataFrame) -> Tuple[bool, list]:
        results = []

        # 1. Schema check
        zero_nulls = daily_df[['is_ltd', 'is_htd', 'is_erd', 'is_edd', 'daily_cpri']].isnull().sum().sum() == 0
        t1_pass = (len(daily_df) > 0) and zero_nulls
        results.append(('KYC-01', 'Schema Integrity & Zero Nulls', 'PASSED' if t1_pass else 'FAILED', f'{len(daily_df):,} rows verified.'))

        # 2. Climatological boundaries
        temp_ok = (thresholds_df['p10_temp_ltd'] < thresholds_df['p90_temp_htd']).all()
        rain_ok = (thresholds_df['p95_precip_erd'] > 0).all()
        humid_ok = ((thresholds_df['p05_humid_edd'] >= 0) & (thresholds_df['p05_humid_edd'] <= 100)).all()
        t2_pass = temp_ok and rain_ok and humid_ok
        results.append(('KYC-02', 'Climatological Quantile Boundaries', 'PASSED' if t2_pass else 'FAILED', 'P10<P90, P95>0, 0<=P5<=100 across all cities.'))

        # 3. Collision impossibility
        collision = (daily_df['is_ltd'] * daily_df['is_htd']).sum()
        sum_ok = (daily_df['daily_cpri'] == (daily_df['is_ltd'] + daily_df['is_htd'] + daily_df['is_erd'] + daily_df['is_edd'])).all()
        t3_pass = (collision == 0) and sum_ok
        results.append(('KYC-03', 'Mutual Exclusivity (LTD * HTD == 0)', 'PASSED' if t3_pass else 'FAILED', f'Collision count: {collision}. Daily sum equivalence: {sum_ok}.'))

        # 4. Empirical calibration
        ltd_r = daily_df['is_ltd'].mean() * 100.0
        htd_r = daily_df['is_htd'].mean() * 100.0
        erd_r = daily_df['is_erd'].mean() * 100.0
        edd_r = daily_df['is_edd'].mean() * 100.0
        t4_pass = (abs(ltd_r - 10.0) < 1.5) and (abs(htd_r - 10.0) < 1.5) and (abs(erd_r - 5.0) < 1.5) and (abs(edd_r - 5.0) < 1.5)
        results.append(('KYC-04', 'Empirical Quantile Convergence', 'PASSED' if t4_pass else 'FAILED', f'LTD:{ltd_r:.2f}%, HTD:{htd_r:.2f}%, ERD:{erd_r:.2f}%, EDD:{edd_r:.2f}%.'))

        # 5. Benchmark congruence
        mean_cpri = agg_df['CPRI_raw'].mean()
        paper_benchmark = 27.2679
        dev = abs(mean_cpri - paper_benchmark) / paper_benchmark * 100.0
        t5_pass = dev < 15.0
        results.append(('KYC-05', 'Nature Table 2 Benchmark Match', 'PASSED' if t5_pass else 'FAILED', f'Sample Mean CPRI: {mean_cpri:.4f} vs Nature Benchmark: {paper_benchmark:.4f} (Dev: {dev:.2f}%).'))

        all_passed = all(r[2] == 'PASSED' for r in results)
        return all_passed, results


class EconometricReporter:
    """Generates publication-ready Table 2 Summary Statistics."""
    @staticmethod
    def generate_table2(agg_df: pd.DataFrame) -> pd.DataFrame:
        metrics = {
            'CPRI (Annualized)': agg_df['CPRI_annualized'],
            'CPRI (Raw Days)': agg_df['CPRI_raw'],
            'LTD (Low Temp Days)': agg_df['LTD_days_norm'],
            'HTD (High Temp Days)': agg_df['HTD_days_norm'],
            'ERD (Rainfall Days)': agg_df['ERD_days_norm'],
            'EDD (Drought Days)': agg_df['EDD_days_norm'],
            'Avg Temp (C)': agg_df['avg_temp'],
            'Total Precip (mm)': agg_df['total_precip'] * agg_df['annual_factor'],
            'Avg Humidity (%)': agg_df['avg_humidity']
        }
        rows = []
        for name, s in metrics.items():
            rows.append({
                'Variable': name,
                'N': int(s.count()),
                'Mean': round(float(s.mean()), 4),
                'SD': round(float(s.std()), 4),
                'Min': round(float(s.min()), 4),
                'P25': round(float(s.quantile(0.25)), 4),
                'Median': round(float(s.median()), 4),
                'P75': round(float(s.quantile(0.75)), 4),
                'Max': round(float(s.max()), 4)
            })
        return pd.DataFrame(rows)
