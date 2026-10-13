"""
Helper script to check if Kaggle dataset exists and guide download if needed.

Usage:
  python check_dataset.py

This will:
  1. Check if data/raw/customer_support_twitter.csv exists
  2. If not, show download instructions
  3. If yes, show dataset info
"""

import sys
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def check_dataset(csv_path: str = "data/raw/customer_support_twitter.csv") -> bool:
    """Check if dataset exists and is valid."""
    
    path = Path(csv_path)
    
    print("\n" + "="*80)
    print("DATASET CHECK")
    print("="*80)
    
    if not path.exists():
        print(f"\n❌ Dataset not found at: {csv_path}")
        print("\nTo download, follow these steps:\n")
        
        print("Option 1: Kaggle CLI (Fastest)")
        print("-" * 80)
        print("""
1. Install Kaggle CLI:
   pip install kaggle

2. Set up API credentials:
   - Visit: https://www.kaggle.com/settings/account
   - Click "Create New Token" (downloads kaggle.json)
   - Place kaggle.json at: C:\\Users\\MONIKA\\.kaggle\\kaggle.json

3. Download dataset:
   kaggle datasets download -d thoughtvector/customer-support-on-twitter -p data/raw/

4. Extract:
   cd data\\raw
   Expand-Archive customer-support-on-twitter.zip -DestinationPath .
   cd ..\\.
""")
        
        print("\nOption 2: Manual Download")
        print("-" * 80)
        print("""
1. Visit: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
2. Click blue "Download" button (top right)
3. Extract ZIP to: data/raw/
4. Rename file to: customer_support_twitter.csv
""")
        
        return False
    
    # File exists, load and show info
    print(f"\n✓ Dataset found at: {csv_path}")
    
    try:
        print("\nLoading dataset info...")
        df = pd.read_csv(csv_path, nrows=1000)  # Load first 1000 for speed
        
        print(f"\n✓ Successfully loaded sample")
        print(f"  Total rows (estimated): {len(df):,}+")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Data types:")
        for col in df.columns:
            print(f"    - {col}: {df[col].dtype}")
        
        # Check key columns
        required_cols = {"text", "author_id", "created_at"}
        available_cols = set(df.columns)
        
        if required_cols.issubset(available_cols):
            print(f"\n✓ All required columns present")
        else:
            missing = required_cols - available_cols
            print(f"\n❌ Missing columns: {missing}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        return False

def main():
    success = check_dataset()
    
    print("\n" + "="*80)
    
    if success:
        print("✓ Dataset is ready!")
        print("\nNext step: Run Phase 1 EDA")
        print("  python phase1_eda.py data/raw/customer_support_twitter.csv")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ Dataset setup required (see instructions above)")
        print("="*80 + "\n")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
