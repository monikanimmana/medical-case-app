"""
Phase 1 Run: Complete data preparation pipeline

Usage:
  python phase1_run.py --brand amazonhelp --sample-size 5000

This script:
1. Loads raw CSV
2. Filters to selected brand
3. Reconstructs threads
4. Cleans text
5. Deduplicates
6. Marks resolved/unresolved
7. Subsamples with fixed seed
8. Saves to processed/ directory
9. Generates summary report
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime

from src.ingest import (
    load_raw_csv,
    extract_brand,
    reconstruct_threads,
    subsample_and_clean,
    is_thread_resolved,
    save_processed_data,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_phase1(
    csv_path: str,
    brand: str,
    sample_size: int = 5000,
    random_seed: int = 42,
    output_dir: str = "data/processed"
) -> Dict:
    """
    Execute Phase 1: Complete data preparation pipeline.
    
    Returns:
        dict: Summary statistics and metadata
    """
    logger.info("="*80)
    logger.info("PHASE 1: DATA PREPARATION")
    logger.info("="*80)
    
    # Load raw data
    logger.info(f"Loading raw CSV from: {csv_path}")
    df = load_raw_csv(csv_path)
    logger.info(f"Loaded {len(df):,} rows")
    
    # Extract brand and standardize
    logger.info(f"Extracting brand field...")
    df["brand"] = df.get("author_id", df.get("author", None)).apply(extract_brand)
    
    brand_lower = brand.lower()
    logger.info(f"Filtering to brand: {brand_lower}")
    brand_df = df[df["brand"] == brand_lower].copy()
    
    if len(brand_df) == 0:
        logger.error(f"No tweets found for brand: {brand_lower}")
        logger.error(f"Available brands: {df['brand'].unique()[:20]}")
        raise ValueError(f"Brand not found: {brand_lower}")
    
    logger.info(f"Found {len(brand_df):,} tweets from {brand_lower}")
    
    # Subsample and clean
    logger.info(f"Cleaning and subsampling...")
    brand_clean_df, clean_stats = subsample_and_clean(
        brand_df,
        brand_lower,
        sample_size=sample_size,
        random_seed=random_seed
    )
    
    logger.info(f"After cleaning: {len(brand_clean_df):,} tweets")
    
    # Reconstruct threads
    logger.info(f"Reconstructing conversation threads...")
    threads = reconstruct_threads(brand_clean_df)
    logger.info(f"Reconstructed {len(threads):,} threads")
    
    # Mark resolved/unresolved
    logger.info(f"Marking threads as resolved/unresolved...")
    resolved_count = 0
    for thread in threads:
        thread["is_resolved"] = is_thread_resolved(thread, brand_lower)
        if thread["is_resolved"]:
            resolved_count += 1
    
    logger.info(f"Resolved threads: {resolved_count:,} / {len(threads):,} ({100*resolved_count/len(threads):.1f}%)")
    
    # Save outputs
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save threads as JSONL (one thread per line)
    threads_path = Path(output_dir) / "threads.jsonl"
    logger.info(f"Saving threads to: {threads_path}")
    with open(threads_path, "w") as f:
        for thread in threads:
            f.write(json.dumps(thread) + "\n")
    
    # Save cleaned CSV
    csv_path_out = Path(output_dir) / "sample_cleaned.csv"
    logger.info(f"Saving cleaned CSV to: {csv_path_out}")
    brand_clean_df.to_csv(csv_path_out, index=False)
    
    # Summary statistics
    stats = {
        "timestamp": datetime.now().isoformat(),
        "brand": brand_lower,
        "source_csv": csv_path,
        
        # Counts
        "n_rows_raw": len(df),
        "n_rows_brand": len(brand_df),
        "n_rows_cleaned": len(brand_clean_df),
        "n_threads": len(threads),
        "n_resolved": resolved_count,
        "pct_resolved": round(100 * resolved_count / len(threads), 1),
        
        # Data quality
        "unique_users": int(brand_clean_df.get("author_id", pd.Series()).nunique()),
        "date_range_start": str(brand_clean_df["created_at"].min()),
        "date_range_end": str(brand_clean_df["created_at"].max()),
        
        # Parameters
        "sample_size": sample_size,
        "random_seed": random_seed,
        
        # Outputs
        "output_dir": output_dir,
        "threads_file": str(threads_path),
        "cleaned_csv_file": str(csv_path_out),
    }
    
    # Save stats
    stats_path = Path(output_dir) / "stats.json"
    logger.info(f"Saving stats to: {stats_path}")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    logger.info("="*80)
    logger.info("PHASE 1: SUMMARY")
    logger.info("="*80)
    logger.info(f"Brand: {brand_lower}")
    logger.info(f"Tweets processed: {len(brand_clean_df):,}")
    logger.info(f"Threads reconstructed: {len(threads):,}")
    logger.info(f"Resolved threads: {resolved_count:,} ({stats['pct_resolved']:.1f}%)")
    logger.info(f"Unique users: {stats['unique_users']:,}")
    logger.info(f"Date range: {stats['date_range_start']} to {stats['date_range_end']}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("="*80)
    logger.info("✓ Phase 1 complete!")
    logger.info("Next: Review outputs in data/processed/")
    logger.info("="*80)
    
    return stats

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: Data preparation pipeline"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="data/raw/customer_support_twitter.csv",
        help="Path to raw Kaggle CSV"
    )
    parser.add_argument(
        "--brand",
        type=str,
        required=True,
        help="Brand to filter to (e.g., 'amazonhelp', 'applsupport')"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5000,
        help="Number of tweets to sample (default: 5000)"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for processed data"
    )
    
    args = parser.parse_args()
    
    try:
        stats = run_phase1(
            csv_path=args.csv,
            brand=args.brand,
            sample_size=args.sample_size,
            random_seed=args.random_seed,
            output_dir=args.output_dir
        )
        print(json.dumps(stats, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Phase 1 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
