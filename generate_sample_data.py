"""Generate sample Twitter support dataset for testing Phase 1-8."""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timedelta
import random

def generate_sample_dataset(output_path: str = "data/raw/customer_support_twitter.csv", n_tweets: int = 2000):
    """Generate sample Twitter support dataset."""
    
    brands = ["amazonhelp", "applsupport", "spotifyhelp", "twitterhelp", "slackhelp", "microsofthelp"]
    support_phrases = [
        "order not received",
        "billing issue",
        "account locked",
        "refund request",
        "technical issue",
        "password reset",
        "subscription problem",
        "app crashed",
        "payment failed",
        "delivery delay",
        "product defective",
        "customer service",
        "need assistance",
        "can't login",
        "update failed",
    ]
    
    positive_replies = [
        "Thank you for your patience. We've resolved the issue.",
        "Great! We're glad we could help.",
        "Your refund has been processed.",
        "The issue is now fixed. Please try again.",
        "Thanks for contacting us. Please check your email for details.",
    ]
    
    negative_replies = [
        "Still no response after 3 days...",
        "This is still not resolved!",
        "Very disappointed with service.",
        "Still waiting for help...",
        "Not helpful at all.",
    ]
    
    data = []
    current_time = datetime.now() - timedelta(days=365)
    tweet_id = 1000000000
    
    for i in range(n_tweets):
        brand = random.choice(brands)
        
        # Root tweet (customer complaint)
        issue = random.choice(support_phrases)
        text = f"Hi @{brand}, I have a {issue}. Can someone help? #{random.randint(1,100)}"
        
        is_resolved = random.choice([True, True, False])  # 67% resolved
        
        root_id = tweet_id
        tweet_id += 1
        
        data.append({
            "tweet_id": root_id,
            "author_id": f"user_{random.randint(1000, 9999)}",
            "text": text,
            "created_at": current_time.isoformat(),
            "in_response_to_tweet_id": None,
            "response_tweet_id": None,
        })
        
        current_time += timedelta(hours=random.randint(1, 24))
        
        # Brand reply (support response)
        if random.random() > 0.3:  # 70% get company reply
            reply_text = f"Hi, thanks for reaching out. We're looking into this issue and will update you shortly."
            company_id = tweet_id
            tweet_id += 1
            
            data.append({
                "tweet_id": company_id,
                "author_id": brand,
                "text": reply_text,
                "created_at": current_time.isoformat(),
                "in_response_to_tweet_id": root_id,
                "response_tweet_id": None,
            })
            
            current_time += timedelta(hours=random.randint(2, 24))
            
            # Customer follow-up
            if random.random() > 0.4:  # 60% get follow-up
                if is_resolved:
                    followup_text = random.choice(positive_replies)
                else:
                    followup_text = random.choice(negative_replies)
                
                followup_id = tweet_id
                tweet_id += 1
                
                data.append({
                    "tweet_id": followup_id,
                    "author_id": f"user_{random.randint(1000, 9999)}",
                    "text": followup_text,
                    "created_at": current_time.isoformat(),
                    "in_response_to_tweet_id": company_id,
                    "response_tweet_id": None,
                })
    
    df = pd.DataFrame(data)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✓ Generated sample dataset: {output_path}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    return df

if __name__ == "__main__":
    generate_sample_dataset()
