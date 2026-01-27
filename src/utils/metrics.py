"""Evaluation metrics for compiler error explanation."""
from typing import Dict, List
import numpy as np
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction


def compute_rouge_scores(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """
    Compute ROUGE scores for predictions against references.
    
    Args:
        predictions: List of predicted explanations
        references: List of reference explanations
        
    Returns:
        Dictionary with rouge-1, rouge-2, and rouge-l scores
    """
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = {'rouge1': [], 'rouge2': [], 'rougeL': []}
    
    for pred, ref in zip(predictions, references):
        score = scorer.score(ref, pred)
        scores['rouge1'].append(score['rouge1'].fmeasure)
        scores['rouge2'].append(score['rouge2'].fmeasure)
        scores['rougeL'].append(score['rougeL'].fmeasure)
    
    return {
        'rouge1': np.mean(scores['rouge1']),
        'rouge2': np.mean(scores['rouge2']),
        'rougeL': np.mean(scores['rougeL'])
    }


def compute_bleu_score(predictions: List[str], references: List[str]) -> float:
    """
    Compute BLEU score for predictions against references.
    
    Args:
        predictions: List of predicted explanations
        references: List of reference explanations
        
    Returns:
        Average BLEU score
    """
    smoothing = SmoothingFunction().method1
    bleu_scores = []
    
    for pred, ref in zip(predictions, references):
        pred_tokens = pred.lower().split()
        ref_tokens = ref.lower().split()
        score = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoothing)
        bleu_scores.append(score)
    
    return np.mean(bleu_scores)


def compute_metrics(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """
    Compute all evaluation metrics.
    
    Args:
        predictions: List of predicted explanations
        references: List of reference explanations
        
    Returns:
        Dictionary with all computed metrics
    """
    rouge_scores = compute_rouge_scores(predictions, references)
    bleu_score = compute_bleu_score(predictions, references)
    
    return {
        **rouge_scores,
        'bleu': bleu_score
    }

