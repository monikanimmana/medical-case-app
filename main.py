#!/usr/bin/env python3
"""
Twitter Support Agent - Main Entry Point

Usage:
    python main.py "Customer message here" [--classify-method keyword|tfidf_lr|llm|ensemble]
    
    Or run interactive demo:
    python main.py --demo
"""

import sys
import argparse
import logging
from src.pipeline import run_pipeline, PipelineInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def process_message(message: str, classify_method: str = "keyword"):
    """Process a single customer message through the pipeline."""
    input_data = PipelineInput(
        customer_message=message,
        thread_history=None,
        brand="support"
    )
    
    output = run_pipeline(input_data, classify_method=classify_method)
    
    # Print results
    print("\n" + "="*80)
    print("SUPPORT AGENT DECISION")
    print("="*80)
    print(f"Customer Message: {output.customer_message}")
    print(f"Intent: {output.intent_name} ({output.intent})")
    print(f"Intent Confidence: {output.intent_confidence:.1%}")
    print(f"Decision: {output.decision.upper()}")
    print(f"Reason: {output.reason}")
    print(f"Grounding Score: {output.grounding_score:.2f}" if output.grounding_score else "Grounding: N/A")
    
    if output.decision == "auto_handle" and output.draft_reply:
        print(f"\nDrafted Reply:")
        print("-" * 80)
        print(output.draft_reply)
        print("-" * 80)
    elif output.decision == "escalate":
        print(f"\n⚠️  This message requires human review")
    
    if output.supporting_cases:
        print(f"\nSupporting Cases: {len(output.supporting_cases)}")
        for case in output.supporting_cases[:2]:
            print(f"  - {case[:60]}...")
    
    print("="*80 + "\n")
    return output


def demo():
    """Run interactive demo with test messages."""
    test_messages = [
        "Where is my order? I ordered it 2 weeks ago and still haven't received it!",
        "I was charged twice for my subscription. Please refund the extra charge.",
        "Can't log into my account. Password reset isn't working.",
        "The app keeps crashing when I try to upload files.",
        "How do I cancel my subscription?",
        "The product I received is broken. This is unacceptable!",
        "What is this feature? How do I use it?",
        "I've been a customer for 5 years and this service has become TERRIBLE. I'm thinking of leaving.",
    ]
    
    print("\n" + "="*80)
    print("TWITTER SUPPORT AGENT - DEMO")
    print("="*80)
    print(f"Running {len(test_messages)} test messages through pipeline...\n")
    
    results = []
    for i, message in enumerate(test_messages, 1):
        print(f"\n[{i}/{len(test_messages)}] Processing: {message[:60]}...")
        try:
            output = process_message(message, classify_method="keyword")
            results.append(output)
        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
    
    # Summary
    print("\n" + "="*80)
    print("DEMO SUMMARY")
    print("="*80)
    auto_handled = sum(1 for r in results if r.decision == "auto_handle")
    escalated = sum(1 for r in results if r.decision == "escalate")
    
    print(f"Total messages: {len(results)}")
    print(f"Auto-handled: {auto_handled} ({100*auto_handled/len(results):.1f}%)")
    print(f"Escalated: {escalated} ({100*escalated/len(results):.1f}%)")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Twitter Support Agent - AI-powered customer support classifier"
    )
    parser.add_argument(
        "message",
        nargs="?",
        default=None,
        help="Customer message to process"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run interactive demo with test messages"
    )
    parser.add_argument(
        "--classify-method",
        choices=["keyword", "tfidf_lr", "llm", "ensemble"],
        default="keyword",
        help="Classification method to use (default: keyword)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.demo:
        demo()
    elif args.message:
        process_message(args.message, classify_method=args.classify_method)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
