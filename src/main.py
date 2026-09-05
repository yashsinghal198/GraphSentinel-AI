import json
from data_generator import generate_dataset
from graph_builder import build_signal_graph
from cluster_scorer import score_clusters
from explanation_layer import explain_cluster
from evaluation import evaluate_performance

def generate_html_dashboard(metrics, clusters):
    """
    Generates a standalone static HTML dashboard displaying metrics and cluster details.
    """
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Abuse-Ring Sentinel | Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
                --glass-bg: rgba(255, 255, 255, 0.05);
                --glass-border: rgba(255, 255, 255, 0.1);
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
                --accent-blue: #38bdf8;
                --accent-red: #f87171;
                --accent-orange: #fb923c;
                --accent-green: #4ade80;
            }}
            body {{
                font-family: 'Outfit', sans-serif;
                background: var(--bg-gradient);
                color: var(--text-primary);
                margin: 0;
                padding: 40px;
                min-height: 100vh;
            }}
            .header {{
                text-align: center;
                margin-bottom: 50px;
                animation: fadeInDown 0.8s ease-out;
            }}
            h1 {{
                font-size: 3rem;
                font-weight: 800;
                background: linear-gradient(to right, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0;
            }}
            .subtitle {{
                color: var(--text-secondary);
                font-size: 1.2rem;
                margin-top: 10px;
            }}
            .metrics-container {{
                display: flex;
                justify-content: space-between;
                gap: 20px;
                margin-bottom: 50px;
                flex-wrap: wrap;
                animation: fadeInUp 0.8s ease-out 0.2s both;
            }}
            .metric-card {{
                flex: 1;
                min-width: 200px;
                background: var(--glass-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--glass-border);
                border-radius: 16px;
                padding: 30px 20px;
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                border-color: rgba(255,255,255,0.2);
            }}
            .metric-card h3 {{
                margin: 0;
                font-size: 0.9rem;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
            .metric-card .value {{
                font-size: 2.5rem;
                font-weight: 800;
                margin-top: 15px;
                color: var(--accent-blue);
            }}
            .metric-card.cost .value {{ color: var(--accent-red); }}
            
            .clusters-section {{
                animation: fadeInUp 0.8s ease-out 0.4s both;
            }}
            .clusters-section h2 {{
                font-size: 2rem;
                margin-bottom: 25px;
                font-weight: 600;
            }}
            .cluster-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0 10px;
            }}
            .cluster-table th {{
                text-align: left;
                padding: 0 20px 10px;
                color: var(--text-secondary);
                font-weight: 400;
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 1px;
            }}
            .cluster-table td {{
                padding: 20px;
                background: var(--glass-bg);
                backdrop-filter: blur(12px);
                border-top: 1px solid var(--glass-border);
                border-bottom: 1px solid var(--glass-border);
                color: var(--text-primary);
                vertical-align: top;
            }}
            .cluster-table tr td:first-child {{
                border-left: 1px solid var(--glass-border);
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                font-weight: 600;
            }}
            .cluster-table tr td:last-child {{
                border-right: 1px solid var(--glass-border);
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
            .cluster-table tr {{
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            .cluster-table tr:hover td {{
                background: rgba(255, 255, 255, 0.08);
            }}
            .tier-badge {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
            }}
            .tier-high {{ background: rgba(248, 113, 113, 0.15); color: var(--accent-red); border: 1px solid rgba(248,113,113,0.3); }}
            .tier-review {{ background: rgba(251, 146, 60, 0.15); color: var(--accent-orange); border: 1px solid rgba(251,146,60,0.3); }}
            .tier-low {{ background: rgba(148, 163, 184, 0.15); color: var(--text-secondary); border: 1px solid rgba(148,163,184,0.3); }}
            
            .explanation-box {{
                font-size: 0.9rem;
                line-height: 1.5;
                color: #cbd5e1;
            }}
            .explanation-box strong {{
                color: #e2e8f0;
            }}
            
            @keyframes fadeInDown {{
                from {{ opacity: 0; transform: translateY(-20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes fadeInUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Abuse-Ring Sentinel</h1>
            <div class="subtitle">AI-Powered Graph Network Analysis Dashboard</div>
        </div>
        
        <div class="metrics-container">
            <div class="metric-card">
                <h3>System Precision</h3>
                <div class="value">{metrics['precision'] * 100:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>System Recall</h3>
                <div class="value">{metrics['recall'] * 100:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>F1 Score</h3>
                <div class="value">{metrics['f1_score'] * 100:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>Auto-Flag Precision</h3>
                <div class="value">{metrics['high_confidence_precision'] * 100:.1f}%</div>
            </div>
            <div class="metric-card cost">
                <h3>False Positive Cost</h3>
                <div class="value">₹{metrics['false_positive_cost_inr']:,}</div>
            </div>
        </div>

        <div class="clusters-section">
            <h2>Detected Threat Clusters</h2>
            <table class="cluster-table">
                <thead>
                    <tr>
                        <th>Cluster ID</th>
                        <th>Confidence Tier</th>
                        <th>Density</th>
                        <th>Size</th>
                        <th>Shared Attributes</th>
                        <th style="width: 40%">AI Explanation & Action</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for c in clusters:
        tier_class = "tier-low"
        tier_label = "Low Risk"
        if c['confidence_tier'] == "HIGH_CONFIDENCE":
            tier_class = "tier-high"
            tier_label = "Auto-Flag (High)"
        elif c['confidence_tier'] == "REVIEW":
            tier_class = "tier-review"
            tier_label = "Manual Review"
            
        explanation_html = c['explanation']
        try:
            exp_data = json.loads(c['explanation'])
            explanation_html = f"<div class='explanation-box'><strong>Assessment:</strong> {exp_data.get('summary', '')}<br><br>"
            explanation_html += f"<strong>Recommended Action:</strong> <span style='color: var(--accent-red); font-weight: 600;'>{exp_data.get('recommended_action', '')}</span></div>"
        except:
            explanation_html = f"<div class='explanation-box'>{explanation_html}</div>"

        row = f"""
                    <tr>
                        <td>{c['cluster_id']}</td>
                        <td><span class="tier-badge {tier_class}">{tier_label}</span></td>
                        <td><strong style="color: var(--accent-blue)">{c['density_score']}</strong></td>
                        <td>{c['cluster_size']} accounts</td>
                        <td><span style="color: #cbd5e1; font-size: 0.9rem;">{', '.join(c['shared_signals'])}</span></td>
                        <td>{explanation_html}</td>
                    </tr>
        """
        html_template += row
        
    html_template += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Dashboard generated successfully: dashboard.html")

def main():
    print("1. Generating Synthetic Data...")
    df = generate_dataset()
    
    print("2. Building Signal Graph...")
    G = build_signal_graph(df)
    
    print("3. Extracting and Scoring Clusters...")
    clusters = score_clusters(G)
    
    print("4. Generating AI Explanations for Clusters (with deterministic fallback)...")
    for c in clusters:
        c['explanation'] = explain_cluster(c)
        
    print("5. Evaluating Performance against Ground Truth...")
    metrics = evaluate_performance(clusters, df)
    
    print("6. Generating HTML Dashboard...")
    generate_html_dashboard(metrics, clusters)
    
    print("Pipeline Execution Complete.")

if __name__ == "__main__":
    main()
