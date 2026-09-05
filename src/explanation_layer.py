import os
import json
from typing import Dict, Any

def get_template_explanation(cluster: Dict[str, Any], error_msg: str) -> str:
    """Fallback template engine when API fails."""
    cluster_id = cluster['cluster_id']
    node_count = cluster['cluster_size']
    density_score = cluster['density_score']
    confidence_tier = cluster['confidence_tier']
    shared_signals = ", ".join(cluster.get('shared_signals', []))
    
    action = "AUTO_FLAG / HOLD ACCOUNTS" if density_score >= 2.5 else "ROUTE TO HUMAN REVIEW QUEUE"
    
    fallback_report = f"""[AUTOMATED SYSTEM FALLBACK REPORT]
Cluster ID: {cluster_id}
Risk Level: {confidence_tier} (Density Score: {density_score})
Connected Accounts: {node_count}

Automated Analysis:
This cluster exhibits tight structural connectivity with a density score of {density_score}. The primary shared signals detected across members include: {shared_signals}. 

Recommended Action:
- {action}

(Note: Generated via deterministic backup pipeline)"""
    
    return fallback_report

def explain_cluster(cluster_data: Dict[str, Any]) -> str:
    """
    Calls Anthropic's Claude API to generate a human-readable explanation for the cluster.
    """
    cluster_id = cluster_data['cluster_id']
    node_count = cluster_data['cluster_size']
    density_score = cluster_data['density_score']
    confidence_tier = cluster_data['confidence_tier']
    shared_signals = ", ".join(cluster_data.get('shared_signals', []))
    
    member_details = ""
    subgraph = cluster_data.get('subgraph')
    if subgraph:
        sample_nodes = list(subgraph.nodes(data=True))[:3]
        for node_id, data in sample_nodes:
            member_details += f"- {data.get('name')} ({data.get('email')})\n"
        if len(subgraph.nodes()) > 3:
            member_details += f"... and {len(subgraph.nodes()) - 3} more.\n"

    system_prompt = """You are a Senior Fraud Operations Analyst for a global payments platform. 
Your task is to analyze connected account clusters flagged by our graph-based detection engine and produce a concise, actionable report for human review.

Analyze the provided cluster data and output a response using this exact JSON structure:
{
  "summary": "<1-2 sentence high-level overview of the ring and its shared infrastructure>",
  "primary_signals": ["<list of key shared attributes, e.g., Card Fingerprint, Device ID>"],
  "risk_assessment": "<Explanation why this connection pattern is suspicious versus innocent>",
  "recommended_action": "<AUTO_BLOCK | MANUAL_REVIEW | MONITOR>",
  "analyst_notes": "<Brief advice on what a human investigator should verify next>"
}

Maintain a professional, objective tone. Base your evaluation solely on the provided signal density and shared attributes."""

    user_prompt = f"""[CLUSTER DETECTED]
- Cluster ID: {cluster_id}
- Account Count: {node_count}
- Cluster Density Score: {density_score}
- Assigned Confidence Tier: {confidence_tier}

[SHARED SIGNALS & EDGES]
{shared_signals}

[MEMBER ACCOUNT SUMMARY]
{member_details}

Please analyze this cluster and generate the fraud analysis JSON report."""

    try:
        api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
            
        from groq import Groq
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            # Using the latest supported Llama 3 model on Groq since 3.1 was deprecated
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        json.loads(content) 
        return content
        
    except Exception as e:
        return get_template_explanation(cluster_data, str(e))
