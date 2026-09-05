import streamlit as st
import pandas as pd
import json
from pyvis.network import Network
import streamlit.components.v1 as components

# Import backend modules
from data_generator import generate_dataset
from graph_builder import build_signal_graph
from cluster_scorer import score_clusters
from explanation_layer import explain_cluster
from evaluation import evaluate_performance

# Configuration
st.set_page_config(page_title="Abuse-Ring Sentinel", layout="wide", page_icon="🛡️")

# Initialize Session State for Human Overrides
if 'human_overrides' not in st.session_state:
    st.session_state.human_overrides = {}

# Custom CSS for glassmorphism and modern UI elements
st.markdown("""
<style>
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .cost-value {
        color: #f87171 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------------------
st.sidebar.title("🛡️ Abuse-Ring Sentinel")
st.sidebar.markdown("Live Simulation Controls")

st.sidebar.header("Signal Weights")
weight_card = st.sidebar.slider("Card Fingerprint", 0.0, 10.0, 4.0, step=0.5)
weight_device = st.sidebar.slider("Device ID", 0.0, 10.0, 3.0, step=0.5)
weight_shipping = st.sidebar.slider("Shipping Address", 0.0, 10.0, 2.0, step=0.5)
weight_ip = st.sidebar.slider("IP Subnet", 0.0, 10.0, 1.0, step=0.5)

st.sidebar.header("Detection Thresholds")
auto_flag_threshold = st.sidebar.slider("Auto-Flag Density", 1.0, 5.0, 2.5, step=0.1)

re_run_clicked = st.sidebar.button("🚀 Re-run Detection Engine", use_container_width=True)

signal_weights = {
    'card_fingerprint': weight_card,
    'device_id': weight_device,
    'shipping_address': weight_shipping,
    'ip_subnet': weight_ip
}

# ---------------------------------------------------------------------
# Caching & Pipeline Execution
# ---------------------------------------------------------------------
@st.cache_data
def load_dataset():
    # Fixed seed guarantees reproducibility
    return generate_dataset(seed=42)

df = load_dataset()

# Run Graph Building
G = build_signal_graph(df, signal_weights=signal_weights)

# Score Clusters
clusters = score_clusters(G, auto_flag_threshold=auto_flag_threshold)

# Apply human overrides
for c in clusters:
    cid = c['cluster_id']
    if cid in st.session_state.human_overrides:
        c['confidence_tier'] = st.session_state.human_overrides[cid]

# Evaluate Performance
metrics = evaluate_performance(clusters, df)

# ---------------------------------------------------------------------
# UI Layout: Header and Metrics
# ---------------------------------------------------------------------
st.title("Fraud Detection Network Analysis")

cols = st.columns(5)
metric_data = [
    ("System Precision", f"{metrics['precision'] * 100:.1f}%", False),
    ("System Recall", f"{metrics['recall'] * 100:.1f}%", False),
    ("F1 Score", f"{metrics['f1_score'] * 100:.1f}%", False),
    ("Auto-Flag Precision", f"{metrics['high_confidence_precision'] * 100:.1f}%", False),
    ("False Positive Cost", f"₹{metrics['false_positive_cost_inr']:,}", True)
]

for col, (label, value, is_cost) in zip(cols, metric_data):
    val_class = "metric-value cost-value" if is_cost else "metric-value"
    col.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="{val_class}">{value}</div>
        </div>
    """, unsafe_allow_html=True)
    
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# UI Layout: Network Graph Visualization (Pyvis)
# ---------------------------------------------------------------------
st.subheader("Network Topology")

def render_pyvis_graph(G, clusters):
    # Initialize Pyvis network (Dark Mode)
    net = Network(height="500px", width="100%", bgcolor="#0f172a", font_color="white")
    
    # Map nodes to colors based on cluster tiers
    node_colors = {}
    for c in clusters:
        tier = c['confidence_tier']
        # Red for HIGH_CONFIDENCE, Yellow for REVIEW
        color = "#f87171" if tier == "HIGH_CONFIDENCE" else "#facc15" if tier == "REVIEW" else "#3b82f6"
        for node_id in c['node_ids']:
            node_colors[node_id] = color
            
    # Add nodes
    for node_id, data in G.nodes(data=True):
        # Nodes not in any flagged cluster are Blue for Independent Accounts
        color = node_colors.get(node_id, "#3b82f6") 
        net.add_node(node_id, label=str(node_id), title=f"Name: {data.get('name')}\\nEmail: {data.get('email')}", color=color)
        
    # Add edges
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 1.0)
        shared = ", ".join(data.get('shared_signals', []))
        net.add_edge(u, v, value=weight, title=f"Shared: {shared} (Weight: {weight})", color="#334155")
        
    # Set physics layout for better visual clustering
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)
    
    # Generate HTML string
    return net.generate_html()

with st.spinner("Rendering network topology..."):
    graph_html = render_pyvis_graph(G, clusters)
    components.html(graph_html, height=515)

# ---------------------------------------------------------------------
# UI Layout: Analyst Review Queue
# ---------------------------------------------------------------------
st.subheader("Analyst Review Queue")

review_clusters = [c for c in clusters if c['confidence_tier'] == "REVIEW"]

if len(review_clusters) == 0:
    st.success("Queue is empty. No clusters currently require manual review!")
else:
    for c in review_clusters:
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{c['cluster_id']}** - Size: **{c['cluster_size']}** accounts | Density: <span style='color:#38bdf8'>**{c['density_score']}**</span> | Shared: {', '.join(c['shared_signals'])}", unsafe_allow_html=True)
            with col2:
                if st.button("✅ Confirm Fraud", key=f"confirm_{c['cluster_id']}", use_container_width=True):
                    st.session_state.human_overrides[c['cluster_id']] = "HIGH_CONFIDENCE"
                    st.rerun()
            with col3:
                if st.button("❌ Dismiss (FP)", key=f"dismiss_{c['cluster_id']}", use_container_width=True):
                    st.session_state.human_overrides[c['cluster_id']] = "LOW_RISK"
                    st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# UI Layout: Cluster Investigation Table & Modals
# ---------------------------------------------------------------------
st.subheader("All Detected Clusters Database")

if len(clusters) == 0:
    st.success("No suspicious clusters detected with the current thresholds.")
else:
    # Summary Table
    table_data = []
    for c in clusters:
        table_data.append({
            "Cluster ID": c['cluster_id'],
            "Size": c['cluster_size'],
            "Density": c['density_score'],
            "Tier": c['confidence_tier'],
            "Action": c['recommended_action'],
            "Shared Signals": ", ".join(c['shared_signals'])
        })
    st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    
    st.markdown("### Deep Dive & Action")
    cluster_ids = [c['cluster_id'] for c in clusters]
    selected_cluster_id = st.selectbox("Select a cluster to investigate:", cluster_ids)
    
    selected_cluster = next((c for c in clusters if c['cluster_id'] == selected_cluster_id), None)
    
    if selected_cluster:
        with st.expander(f"Investigate {selected_cluster_id} (Tier: {selected_cluster['confidence_tier']})", expanded=True):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Member Accounts**")
                subgraph = selected_cluster['subgraph']
                for node_id, data in subgraph.nodes(data=True):
                    st.markdown(f"- `{node_id}`: {data.get('name')} | {data.get('email')}")
                
                st.markdown("**Shared Infrastructure**")
                for sig in selected_cluster['shared_signals']:
                    st.markdown(f"- `{sig}`")
                    
            with col2:
                st.markdown("**AI Fraud Analyst Report**")
                # Generate AI Explanation on demand to save API costs, or pull from cache
                if 'explanation' not in selected_cluster:
                    with st.spinner("Querying AI Analyst..."):
                        selected_cluster['explanation'] = explain_cluster(selected_cluster)
                
                # Check if it's JSON or plaintext (fallback)
                try:
                    exp_data = json.loads(selected_cluster['explanation'])
                    st.info(f"**Summary:** {exp_data.get('summary', '')}")
                    st.error(f"**Risk Assessment:** {exp_data.get('risk_assessment', '')}")
                    st.warning(f"**Notes:** {exp_data.get('analyst_notes', '')}")
                    st.markdown(f"**Recommended Action:** `{exp_data.get('recommended_action', '')}`")
                except:
                    st.info(selected_cluster['explanation'])
                    
            st.divider()
            if selected_cluster['confidence_tier'] != "HIGH_CONFIDENCE":
                if st.button(f"🚫 Confirm Block ({selected_cluster['cluster_size']} accounts)", type="primary", use_container_width=True, key="block_deepdive"):
                    st.session_state.human_overrides[selected_cluster_id] = "HIGH_CONFIDENCE"
                    st.rerun()
