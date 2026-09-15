# How to Download the Kaggle Dataset

## Quick Start

### Option 1: Kaggle CLI (Recommended)

```bash
# Step 1: Install kaggle CLI
pip install kaggle

# Step 2: Get your Kaggle API credentials
#   - Go to https://www.kaggle.com/settings/account
#   - Scroll to "API" section
#   - Click "Create New Token"
#   - Save the downloaded kaggle.json to: C:\Users\MONIKA\.kaggle\kaggle.json

# Step 3: Download the dataset
kaggle datasets download -d thoughtvector/customer-support-on-twitter -p data/raw/

# Step 4: Unzip it
cd data/raw
Expand-Archive customer-support-on-twitter.zip -DestinationPath .
cd ../..
```

### Option 2: Manual Download

1. Go to: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
2. Click the blue **Download** button (top right)
3. Wait for the ZIP to download
4. Extract to `data/raw/` folder

## Verify Download

After downloading and unzipping, you should have:

```
data/raw/
└── customer_support_twitter.csv (or similar name, ~500-1000 MB)
```

Check columns:
```
tweet_id, text, author_id, created_at, in_response_to_tweet_id, response_tweet_id, ...
```

## Next Steps

Once you have the CSV, run the Phase 1 EDA:

```bash
python phase1_eda.py data/raw/customer_support_twitter.csv
```

This will show you a table of top brands by volume and engagement metrics. Pick one, and Phase 1 implementation begins!

---

**Questions?** The dataset is ~3M rows, ~500-1000 MB. If download is slow, you can also access it via Kaggle's web interface for a preview.
