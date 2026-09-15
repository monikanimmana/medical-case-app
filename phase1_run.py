"""
Phase 1 Implementation: Data Acquisition & Cleaning
- Load Kaggle CSV
- Filter to brand (amazonhelp) conversations
- Subsample (5k-20k, fixed seed) - FIRST for speed
- Clean data (dedup)
- Reconstruct threads
- Apply "resolved" heuristic
- Save processed data + stats

Run with:
  python phase1_run.py
"""

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from src.ingest import (
    load_raw_csv,
    extract_brand,
    reconstruct_threads,
    is_thread_resolved,
    clean_text,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configuration
BRAND = "amazonhelp"
CSV_PATH = "data/raw/twcs/twcs.csv"
SAMPLE_SIZE = 10000
RANDOM_SEED = 42
OUTPUT_DIR = Path("data/processed")


def get_brand_conversation_threads(df: pd.DataFrame, brand: str) -> pd.DataFrame:
    """
    Get all tweets (inbound + outbound) that are part of conversations with a brand.
    Uses tweet_id and response_tweet_id/in_response_to_tweet_id relationships.
    """
    brand_lower = brand.lower()
    
    # Step 1: Get all tweets FROM the brand
    brand_tweets = df[df["author_id"].str.lower() == brand_lower]
    brand_tweet_ids = set(brand_tweets["tweet_id"].tolist())
    logger.info(f"  Found {len(brand_tweet_ids)} brand tweets")
    
    # Step 2: Get all tweets that are IN RESPONSE TO brand tweets
    responses_to_brand = df[df["in_response_to_tweet_id"].isin(brand_tweet_ids)]
    responses_ids = set(responses_to_brand["tweet_id"].tolist())
    logger.info(f"  Found {len(responses_ids)} customer responses to brand")
    
    # Step 3: Get all tweets that the brand replied to (for context)
    customer_tweet_ids = responses_to_brand["tweet_id"].tolist()
    brand_replies_to_customer = df[
        (df["in_response_to_tweet_id"].isin(customer_tweet_ids)) & 
        (df["author_id"].str.lower() == brand_lower)
    ]
    brand_reply_ids = set(brand_replies_to_customer["tweet_id"].tolist())
    logger.info(f"  Found {len(brand_reply_ids)} brand replies")
    
    # Combine all tweet IDs
    all_conversation_ids = brand_tweet_ids | responses_ids | brand_reply_ids
    logger.info(f"  Total tweets in brand conversations: {len(all_conversation_ids)}")
    
    # Return dataframe with all related tweets
    conversation_df = df[df["tweet_id"].isin(all_conversation_ids)].copy()
    return conversation_df


def main():
    logger.info("="*80)
    logger.info(f"PHASE 1: Data Acquisition & Processing for {BRAND.upper()}")
    logger.info("="*80)
    
    # Step 1: Load CSV
    logger.info("\n[1/5] Loading dataset...")
    try:
        df = load_raw_csv(CSV_PATH)
    except FileNotFoundError:
        logger.error(f"CSV not found at {CSV_PATH}")
        logger.error("Please download the Kaggle dataset first. See DOWNLOAD_DATASET.md")
        return
    
    # Step 2: Get all brand conversations
    logger.info(f"\n[2/5] Extracting {BRAND} conversations...")
    brand_df = get_brand_conversation_threads(df, BRAND)
    
    if len(brand_df) == 0:
        logger.error(f"No tweets found for {BRAND}")
        return
    
    logger.info(f"  ✓ Total conversation tweets: {len(brand_df)}")
    
    # Step 3: Subsample FIRST (faster to process smaller dataset)
    logger.info(f"\n[3/5] Subsampling ({SAMPLE_SIZE} tweets, seed={RANDOM_SEED})...")
    if len(brand_df) > SAMPLE_SIZE:
        brand_df = brand_df.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED)
    logger.info(f"  ✓ Sample size: {len(brand_df)} tweets")
    
    # Step 4: Clean text
    logger.info(f"\n[4/5] Cleaning text and deduplicating...")
    brand_df["text_clean"] = brand_df["text"].apply(clean_text)
    brand_df = brand_df[brand_df["text_clean"].str.len() > 0].copy()
    logger.info(f"  ✓ Removed empty tweets: {len(brand_df)} remaining")
    
    # Drop duplicates
    n_before = len(brand_df)
    brand_df = brand_df.drop_duplicates(subset=["text_clean"])
    logger.info(f"  ✓ Dropped duplicates: {n_before - len(brand_df)} removed")
    
    # Step 5: Reconstruct threads and check resolution
    logger.info(f"\n[5/5] Reconstructing threads and checking resolution...")
    threads = reconstruct_threads(brand_df)
    
    # Mark resolved threads
    resolved_count = 0
    thread_list = []
    for thread in threads:
        is_resolved = is_thread_resolved(thread, BRAND)
        if is_resolved:
            resolved_count += 1
        
        # Flatten thread into a dict for analysis
        thread_dict = {
            "thread_id": thread[0].get("tweet_id") if thread else None,
            "n_messages": len(thread),
            "is_resolved": is_resolved,
            "messages": [
                {
                    "tweet_id": msg.get("tweet_id"),
                    "author_id": msg.get("author_id"),
                    "text": msg.get("text_clean", msg.get("text", "")),
                    "created_at": msg.get("created_at"),
                    "inbound": msg.get("inbound"),
                }
                for msg in thread
            ]
        }
        thread_list.append(thread_dict)
    
    logger.info(f"  ✓ Reconstructed {len(threads)} threads")
    logger.info(f"  ✓ Resolved threads: {resolved_count}/{len(threads)} ({100*resolved_count/max(len(threads),1):.1f}%)")
    
    # Save processed data
    logger.info(f"\n[Save] Saving processed data to {OUTPUT_DIR}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save cleaned tweets
    tweets_output = OUTPUT_DIR / "cleaned_tweets.csv"
    brand_df.to_csv(tweets_output, index=False)
    logger.info(f"  ✓ Saved {len(brand_df)} tweets to {tweets_output}")
    
    # Save threads (as JSONL)
    threads_output = OUTPUT_DIR / "threads.jsonl"
    with open(threads_output, "w") as f:
        for thread in thread_list:
            f.write(json.dumps(thread) + "\n")
    logger.info(f"  ✓ Saved {len(thread_list)} threads to {threads_output}")
    
    # Summary stats
    logger.info(f"\n{'='*80}")
    logger.info("PHASE 1 SUMMARY")
    logger.info(f"{'='*80}")
    
    summary = {
        "brand": BRAND,
        "total_tweets_processed": len(brand_df),
        "inbound_tweets": int(brand_df["inbound"].sum()),
        "outbound_tweets": int((~brand_df["inbound"]).sum()),
        "unique_customer_ids": int(brand_df[brand_df["inbound"]]["author_id"].nunique()),
        "date_range_start": str(brand_df["created_at"].min()),
        "date_range_end": str(brand_df["created_at"].max()),
        "total_threads": len(thread_list),
        "resolved_threads": resolved_count,
        "resolved_pct": round(100 * resolved_count / max(len(thread_list), 1), 1),
        "avg_thread_length": round(np.mean([t["n_messages"] for t in thread_list]), 2) if thread_list else 0,
        "random_seed": RANDOM_SEED,
    }
    
    for key, val in summary.items():
        logger.info(f"  {key}: {val}")
    
    # Save summary
    summary_output = OUTPUT_DIR / "summary.json"
    with open(summary_output, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"\n✓ Saved summary to {summary_output}")
    
    logger.info(f"\n{'='*80}")
    logger.info("PHASE 1 COMPLETE ✓")
    logger.info(f"{'='*80}")
    logger.info("\nNext: Phase 2 - Intent Taxonomy")
    logger.info("  Run: python phase2_clustering.py")
    logger.info("\n")


if __name__ == "__main__":
    main()
