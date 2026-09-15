"""
Phase 1 EDA: Profile brands and show candidate shortlist.

Run with:
  python phase1_eda.py <path/to/customer_support_twitter.csv>

This will output a table of top brands for you to choose from.
"""

import sys
import pandas as pd
from src.ingest import load_raw_csv, profile_brands

def main():
    if len(sys.argv) < 2:
        print("Usage: python phase1_eda.py <path/to/csv>")
        print("\nExample:")
        print("  python phase1_eda.py data/raw/customer_support_twitter.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    try:
        df = load_raw_csv(csv_path)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    print("\n" + "="*100)
    print("PHASE 1: BRAND PROFILING & SELECTION")
    print("="*100)
    print(f"\nDataset info:")
    print(f"  Total rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    
    # Profile brands
    print(f"\nProfiling brands (min 100 tweets)...")
    stats_df = profile_brands(df, min_tweets=100)
    
    print(f"\nTop 15 brands by volume:")
    print("-"*100)
    top_15 = stats_df.head(15).copy()
    
    # Pretty print
    print(top_15.to_string(index=False))
    
    print("\n" + "-"*100)
    print("NEXT STEP:")
    print("  Pick one brand from the table above (e.g., 'AmazonHelp')")
    print("  Reply with the brand name, and I'll proceed to Phase 1 implementation:")
    print("    1. Thread reconstruction")
    print("    2. Data cleaning (English filter, dedup, PII removal)")
    print("    3. Subsample (5k-20k tweets, fixed seed)")
    print("    4. Define 'resolved' heuristic")
    print("    5. Save processed data + summary stats")
    print("\n")

if __name__ == "__main__":
    main()
