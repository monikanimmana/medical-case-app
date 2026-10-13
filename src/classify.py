"""
Phase 3: Intent classification
Three classifiers: majority baseline, TF-IDF + LR, and LLM-based.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, List
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import os
import json

from src.taxonomy import INTENT_KEYWORDS, TAXONOMY, INTENT_LIST

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    intent: str
    intent_name: str
    confidence: float
    classifier: str  # "keyword", "tfidf_lr", "llm"
    reasoning: Optional[str] = None


class KeywordClassifier:
    """Baseline: keyword matching classifier."""
    
    def __init__(self):
        self.keywords = INTENT_KEYWORDS
    
    def classify(self, text: str) -> ClassificationResult:
        """Classify by keyword matching."""
        text_lower = text.lower()
        
        # Score each intent
        scores = {}
        for intent_id, keywords in self.keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[intent_id] = matches / max(len(keywords), 1)
        
        best_intent = max(scores.items(), key=lambda x: x[1])
        intent_id = best_intent[0]
        confidence = min(best_intent[1], 1.0)
        
        if confidence == 0:
            # Default to general info if no keywords match
            intent_id = "GENERAL_INFO"
            confidence = 0.5
        
        intent_name = TAXONOMY[intent_id].name
        
        return ClassificationResult(
            intent=intent_id,
            intent_name=intent_name,
            confidence=confidence,
            classifier="keyword",
            reasoning=f"Matched {int(best_intent[1] * max(len(INTENT_KEYWORDS[intent_id]), 1))} keywords"
        )


class TFIDFClassifier:
    """TF-IDF + Logistic Regression classifier."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=1.0
        )
        self.model = LogisticRegression(max_iter=1000, random_state=42)
        self.intent_ids = [intent.id for intent in INTENT_LIST]
        self._is_trained = False
    
    def train(self, texts: List[str], labels: List[str]):
        """Train the classifier on provided texts and labels."""
        X = self.vectorizer.fit_transform(texts)
        label_indices = [self.intent_ids.index(label) for label in labels]
        self.model.fit(X, label_indices)
        self._is_trained = True
        logger.info(f"TF-IDF classifier trained on {len(texts)} examples")
    
    def classify(self, text: str) -> ClassificationResult:
        """Classify using TF-IDF + LR."""
        if not self._is_trained:
            logger.warning("TF-IDF classifier not trained, using keyword fallback")
            return KeywordClassifier().classify(text)
        
        X = self.vectorizer.transform([text])
        prediction = self.model.predict(X)[0]
        confidence = self.model.predict_proba(X)[0][prediction]
        
        intent_id = self.intent_ids[prediction]
        intent_name = TAXONOMY[intent_id].name
        
        return ClassificationResult(
            intent=intent_id,
            intent_name=intent_name,
            confidence=float(confidence),
            classifier="tfidf_lr",
            reasoning="TF-IDF + Logistic Regression"
        )


class LLMClassifier:
    """LLM-based classifier using Gemini."""
    
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            logger.warning("google.generativeai not available, LLM classifier disabled")
            self.genai = None
    
    def classify(self, text: str) -> ClassificationResult:
        """Classify using LLM."""
        if not self.genai or not os.getenv("GEMINI_API_KEY"):
            logger.warning("Gemini API key not set, using keyword fallback")
            return KeywordClassifier().classify(text)
        
        # Build intent options
        options_str = "\n".join([
            f"- {intent.id}: {intent.name} - {intent.definition}"
            for intent in INTENT_LIST
        ])
        
        prompt = f"""Classify the following customer support message into one of these categories:

{options_str}

Message: "{text}"

Respond with JSON:
{{
    "intent": "<INTENT_ID>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief reason>"
}}"""
        
        try:
            model = self.genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            
            # Parse response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                intent_id = result.get("intent", "GENERAL_INFO")
                confidence = float(result.get("confidence", 0.5))
                reasoning = result.get("reasoning", "LLM classification")
                
                if intent_id not in TAXONOMY:
                    intent_id = "GENERAL_INFO"
                
                return ClassificationResult(
                    intent=intent_id,
                    intent_name=TAXONOMY[intent_id].name,
                    confidence=min(confidence, 1.0),
                    classifier="llm",
                    reasoning=reasoning
                )
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
        
        # Fallback to keyword
        return KeywordClassifier().classify(text)


# Global classifiers
keyword_clf = KeywordClassifier()
tfidf_clf = TFIDFClassifier()
llm_clf = LLMClassifier()


def classify(text: str, method: str = "keyword") -> ClassificationResult:
    """
    Classify a message into an intent.
    
    Args:
        text: Message text to classify
        method: Classification method ("keyword", "tfidf_lr", "llm", or "ensemble")
    
    Returns:
        ClassificationResult with intent and confidence
    """
    if method == "keyword":
        return keyword_clf.classify(text)
    elif method == "tfidf_lr":
        return tfidf_clf.classify(text)
    elif method == "llm":
        return llm_clf.classify(text)
    elif method == "ensemble":
        # Average the top 2 classifiers
        kw_result = keyword_clf.classify(text)
        llm_result = llm_clf.classify(text)
        
        if kw_result.intent == llm_result.intent:
            combined_conf = (kw_result.confidence + llm_result.confidence) / 2
            return ClassificationResult(
                intent=kw_result.intent,
                intent_name=kw_result.intent_name,
                confidence=combined_conf,
                classifier="ensemble",
                reasoning="Keyword + LLM agreement"
            )
        else:
            # Take higher confidence
            if kw_result.confidence >= llm_result.confidence:
                return kw_result
            else:
                return llm_result
    else:
        raise ValueError(f"Unknown classification method: {method}")
