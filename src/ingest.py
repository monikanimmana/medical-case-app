"""
Phase 1: Data ingestion and brand selection
Loads Kaggle CSV, filters by brand, reconstructs threads.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Optional
from langdetect import detect, LangDetectException
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)


def load_raw_csv(csv_path: str) -> pd.DataFrame:
    """Load the raw Kaggle CSV."""
    logger.info(f"Loading CSV from {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows, columns: {list(df.columns)}")
    return df


def extract_brand(author: str) -> str:
    """
    Extract brand name from author field.
    Assumes author is like '@AmazonHelp', '@AppleSupport', etc.
    """
    if pd.isna(author):
        return None
    author = str(author).strip()
    # Remove leading @ and lowercase
    if author.startswith("@"):
        author = author[1:]
    return author.lower()


def profile_brands(df: pd.DataFrame, min_tweets: int = 100) -> pd.DataFrame:
    """
    Profile brands by:
    - Tweet volume
    - Average thread depth
    - Fraction with company reply
    - Fraction that look resolved
    """
    df["brand"] = df.get("author_id", df.get("author", None)).apply(extract_brand)
    
    # Filter out nulls
    df = df[df["brand"].notna()].copy()
    
    brand_stats = []
    
    for brand, group in df.groupby("brand"):
        n_tweets = len(group)
        
        if n_tweets < min_tweets:
            continue
        
        # Thread depth: count replies per thread (estimate via in_response_to)
        has_response_to = group[group.get("in_response_to_tweet_id", pd.Series()).notna()].shape[0]
        avg_thread_depth = has_response_to / max(n_tweets, 1)
        
        # Fraction with company reply (if response_tweet_id is not null)
        has_company_reply = group[group.get("response_tweet_id", pd.Series()).notna()].shape[0]
        frac_with_reply = has_company_reply / max(n_tweets, 1)
        
        # Fraction resolved (heuristic: will refine after seeing data)
        frac_resolved = 0.0  # Placeholder; will implement after seeing thread structure
        
        brand_stats.append({
            "brand": brand,
            "n_tweets": n_tweets,
            "avg_thread_depth": round(avg_thread_depth, 3),
            "frac_with_company_reply": round(frac_with_reply, 3),
            "frac_resolved_est": round(frac_resolved, 3),
        })
    
    stats_df = pd.DataFrame(brand_stats).sort_values("n_tweets", ascending=False)
    return stats_df


def is_english(text: str, threshold: float = 0.8) -> bool:
    """
    Fast language detection using simple heuristics.
    This is a simplified check; we assume most tweets are English by default.
    """
    if pd.isna(text) or not isinstance(text, str) or len(text.strip()) < 5:
        return True
    
    text_lower = str(text).lower()
    
    # Common non-English indicators (very simple, fast)
    non_english_markers = {
        "por favor", "gracias", "hola", "adiós",  # Spanish
        "merci", "bonjour", "au revoir",  # French
        "danke", "guten", "auf wiedersehen",  # German
        "ciao", "grazie", "arrivederci",  # Italian
        "olá", "obrigado", "adeus",  # Portuguese
    }
    
    # If text contains known non-English words, filter out
    for marker in non_english_markers:
        if marker in text_lower:
            return False
    
    # Otherwise assume English (Twitter support is mostly English)
    return True


def clean_text(text: str) -> str:
    """
    Clean tweet text:
    - Remove @mentions (except brand handles which are preserved for context)
    - Remove URLs
    - Strip extra whitespace
    - Keep only printable chars
    """
    if pd.isna(text):
        return ""
    
    text = str(text)
    
    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)
    
    # Remove @mentions (optional: keep for context, but flag for review)
    # For now, replace with [MENTION] for analysis
    text = re.sub(r"@\w+", "[MENTION]", text)
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Strip non-printable
    text = "".join(c for c in text if c.isprintable())
    
    return text.strip()


def reconstruct_threads(df: pd.DataFrame) -> List[Dict]:
    """
    Reconstruct conversation threads from tweet IDs.
    
    Assumes columns:
    - tweet_id: unique tweet ID
    - in_response_to_tweet_id: ID of tweet this replies to (null if root)
    - response_tweet_id: IDs of tweets that replied to this (null if none)
    - text: tweet text
    - author_id: who tweeted this
    - created_at: timestamp
    """
    # Build a map: tweet_id -> tweet data
    tweet_map = {}
    for _, row in df.iterrows():
        tweet_id = row.get("tweet_id")
        if pd.notna(tweet_id):
            tweet_map[tweet_id] = row
    
    # Find root tweets (no in_response_to_tweet_id)
    threads = []
    visited = set()
    
    for tweet_id, tweet_row in tweet_map.items():
        if tweet_id in visited:
            continue
        
        # Check if this is a root tweet
        in_response_to = tweet_row.get("in_response_to_tweet_id")
        if pd.isna(in_response_to) or in_response_to not in tweet_map:
            # This is a root; build thread forward
            thread = _build_thread_forward(tweet_id, tweet_map, visited)
            if len(thread) > 0:
                threads.append(thread)
    
    return threads


def _build_thread_forward(root_id, tweet_map: Dict, visited: set) -> Dict:
    """
    Recursively build a thread starting from a root tweet.
    Returns: dict with messages list and metadata
    """
    messages = []
    
    def traverse(tweet_id):
        if tweet_id in visited or tweet_id not in tweet_map:
            return
        visited.add(tweet_id)
        tweet_row = tweet_map[tweet_id]
        # Convert pandas Series to dict
        msg = dict(tweet_row)
        messages.append(msg)
        
        # Find replies to this tweet
        response_ids = tweet_row.get("response_tweet_id")
        if pd.notna(response_ids):
            # response_tweet_id might be a string representation of list or comma-separated
            if isinstance(response_ids, str):
                resp_list = [int(x.strip()) for x in response_ids.split(",") if x.strip().isdigit()]
            elif isinstance(response_ids, (list, np.ndarray)):
                resp_list = list(response_ids)
            else:
                resp_list = []
            
            for resp_id in resp_list:
                traverse(resp_id)
    
    traverse(root_id)
    
    return {
        "messages": messages,
        "root_id": root_id,
        "n_messages": len(messages),
    }


def is_thread_resolved(thread: Dict, brand: str) -> bool:
    """
    Heuristic: thread is "resolved" if:
    1. Company has replied (the brand account itself responded)
    2. Last meaningful message is from company OR customer sent positive follow-up
    3. No escalation signals (all caps, repeated ??/!!!!, "still waiting", etc.)
    
    This is deliberately noisy; limitations will be documented.
    """
    messages = thread.get("messages", [])
    
    if len(messages) < 2:
        return False
    
    brand_lower = brand.lower()
    
    # Check if brand replied at all
    brand_replied = any(
        str(msg.get("author_id", "")).lower() == brand_lower 
        for msg in messages
    )
    
    if not brand_replied:
        return False
    
    # Find last message from brand
    last_brand_msg_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if str(messages[i].get("author_id", "")).lower() == brand_lower:
            last_brand_msg_idx = i
            break
    
    # Check if customer sent follow-up after brand's last reply
    if last_brand_msg_idx == len(messages) - 1:
        # Brand has last word
        return True
    elif last_brand_msg_idx >= 0:
        # Customer replied after brand
        # Check last customer message for escalation signals
        last_customer_msg = messages[-1].get("text", "").lower()
        
        # Escalation patterns (unresolved)
        escalation_patterns = [
            "still waiting",
            "not resolved",
            "not helpful",
            "where is",
            "still broken",
            "still not",
            "refuse",
            "cancel my",
            "this is unacceptable",
            "this is horrible",
        ]
        has_escalation = any(pattern in last_customer_msg for pattern in escalation_patterns)
        
        # Positive patterns (resolved)
        positive_patterns = [
            "thank",
            "thanks",
            "appreciate",
            "solved",
            "fixed",
            "working now",
            "great",
            "perfect",
            "problem solved",
        ]
        has_positive = any(pattern in last_customer_msg for pattern in positive_patterns)
        
        # If has escalation signals, not resolved; if has positive, resolved
        if has_escalation:
            return False
        elif has_positive:
            return True
        else:
            # Neutral follow-up: assume resolved (brand had last substantive reply)
            return True
    
    return False


def subsample_and_clean(
    df: pd.DataFrame,
    brand: str,
    sample_size: int = 5000,
    random_seed: int = 42,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Filter to brand, subsample, clean, and return stats.
    """
    logger.info(f"Filtering to brand: {brand}")
    brand_df = df[df["brand"] == brand].copy()
    
    if len(brand_df) == 0:
        raise ValueError(f"No tweets found for brand: {brand}")
    
    logger.info(f"Found {len(brand_df)} tweets for {brand}")
    
    # Subsample with fixed seed
    if len(brand_df) > sample_size:
        brand_df = brand_df.sample(n=sample_size, random_state=random_seed)
        logger.info(f"Subsampled to {sample_size} tweets")
    
    # Filter to English
    logger.info("Filtering to English...")
    brand_df["is_english"] = brand_df["text"].apply(is_english)
    n_english = brand_df["is_english"].sum()
    brand_df = brand_df[brand_df["is_english"]]
    logger.info(f"Kept {n_english} English tweets")
    
    # Clean text
    logger.info("Cleaning text...")
    brand_df["text_clean"] = brand_df["text"].apply(clean_text)
    brand_df = brand_df[brand_df["text_clean"].str.len() > 0]
    logger.info(f"Kept {len(brand_df)} non-empty tweets")
    
    # Drop duplicates
    n_before = len(brand_df)
    brand_df = brand_df.drop_duplicates(subset=["text_clean"])
    logger.info(f"Dropped duplicates: {n_before - len(brand_df)} removed")
    
    # Summary stats
    stats = {
        "n_tweets": len(brand_df),
        "n_unique_users": brand_df.get("author_id", pd.Series()).nunique(),
        "date_range": f"{brand_df['created_at'].min()} to {brand_df['created_at'].max()}",
    }
    
    return brand_df, stats


def save_processed_data(df: pd.DataFrame, output_dir: str = "data/processed"):
    """Save cleaned data to processed directory."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "cleaned_tweets.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved to {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage for Phase 1 EDA
    import sys
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/customer_support_twitter.csv"
    
    print(f"Loading dataset from: {csv_path}")
    df = load_raw_csv(csv_path)
    
    print("\n" + "="*80)
    print("BRAND PROFILING")
    print("="*80)
    stats_df = profile_brands(df, min_tweets=100)
    print(stats_df.head(20).to_string())
    print(f"\nTop 20 brands shown above. Total: {len(stats_df)} brands with >=100 tweets")
    
    print("\nReady for Phase 1: Pick a brand from the above table and confirm.")
