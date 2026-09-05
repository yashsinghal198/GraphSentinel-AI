import pandas as pd
from typing import List, Dict, Any

def evaluate_performance(flagged_clusters: List[Dict[str, Any]], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates system performance against ground truth (is_ring_member).
    This function is strictly the only place that accesses 'is_ring_member' post-detection.
    """
    
    # 1. Prepare Ground Truth
    actual_ring_members = set(df[df['is_ring_member'] == True]['customer_id'])
    
    # 2. Prepare Predictions
    predicted_ring_members = set()
    high_conf_predicted = set()
    
    for cluster in flagged_clusters:
        # Any cluster returned by score_clusters has tier HIGH_CONFIDENCE or REVIEW
        if cluster['confidence_tier'] in ["HIGH_CONFIDENCE", "REVIEW"]:
            predicted_ring_members.update(cluster['node_ids'])
            
        if cluster['confidence_tier'] == "HIGH_CONFIDENCE":
            high_conf_predicted.update(cluster['node_ids'])
            
    # True Positives: Predicted and actually a ring member
    tp = len(predicted_ring_members.intersection(actual_ring_members))
    # False Positives: Predicted but NOT a ring member
    fp = len(predicted_ring_members - actual_ring_members)
    # False Negatives: Actually a ring member but NOT predicted
    fn = len(actual_ring_members - predicted_ring_members)
    
    # Overall Metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # High-Confidence Precision (Should ideally be 100% / 0 false positives auto-actioned)
    hc_tp = len(high_conf_predicted.intersection(actual_ring_members))
    hc_fp = len(high_conf_predicted - actual_ring_members)
    hc_precision = hc_tp / (hc_tp + hc_fp) if (hc_tp + hc_fp) > 0 else 0.0
    
    # Financial Cost (False Positives * LTV ₹4,500)
    fp_cost = fp * 4500
    hc_fp_cost = hc_fp * 4500
    
    metrics = {
        'total_actual_ring_members': len(actual_ring_members),
        'total_predicted_ring_members': len(predicted_ring_members),
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1_score': round(f1, 4),
        'high_confidence_precision': round(hc_precision, 4),
        'high_confidence_false_positives': hc_fp,
        'false_positive_cost_inr': fp_cost,
        'hc_false_positive_cost_inr': hc_fp_cost
    }
    
    return metrics

if __name__ == "__main__":
    from data_generator import generate_dataset
    from graph_builder import build_signal_graph
    from cluster_scorer import score_clusters
    
    df = generate_dataset()
    G = build_signal_graph(df)
    clusters = score_clusters(G)
    metrics = evaluate_performance(clusters, df)
    
    print("--- Evaluation Metrics ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
