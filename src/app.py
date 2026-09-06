import streamlit as st
import pandas as pd
import json
from pyvis.network import Network
import streamlit.components.v1 as components
import io
import datetime
from fpdf import FPDF

# Import backend modules
from data_generator import generate_dataset
from graph_builder import build_signal_graph
from cluster_scorer import score_clusters
from explanation_layer import explain_cluster
from evaluation import evaluate_performance

# Configuration
st.set_page_config(page_title="GraphSentinel AI", layout="wide", page_icon="🛡️")

# Initialize Session State for Human Overrides, Audit Log & Explanation Cache
if 'human_overrides' not in st.session_state:
    st.session_state.human_overrides = {}
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []
if 'explanations' not in st.session_state:
    st.session_state.explanations = {}

def log_action(cluster_id, action, density, signals):
    st.session_state.audit_log.append({
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Cluster ID": cluster_id,
        "Action Taken": action,
        "Density": density,
        "Shared Signals": ", ".join(signals)
    })

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
st.sidebar.title("🛡️ GraphSentinel AI")
st.sidebar.markdown("Live Simulation Controls")

with st.sidebar.form("detection_controls"):
    st.header("Signal Weights")
    weight_card = st.slider("Card Fingerprint", 0.0, 5.0, 4.0, step=0.5)
    weight_device = st.slider("Device ID", 0.0, 5.0, 3.0, step=0.5)
    weight_shipping = st.slider("Shipping Address", 0.0, 5.0, 2.0, step=0.5)
    weight_ip = st.slider("IP Subnet", 0.0, 5.0, 1.0, step=0.5)

    st.header("Detection Thresholds")
    auto_flag_threshold = st.slider("Auto-Flag Density", 1.0, 5.0, 2.5, step=0.1)

    st.header("Adversarial Stress Test")
    simulate_evasion = st.toggle("🥷 Simulate Ring Evasion", value=False, help="Simulate a sophisticated attack where fraudsters actively scramble their IP subnets and Device IDs to evade detection.")

    re_run_clicked = st.form_submit_button("🚀 Re-run Detection Engine", use_container_width=True)

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

# Apply Adversarial Evasion
if simulate_evasion:
    import random
    import uuid
    # Create a copy so we don't mutate the cached dataframe
    df = df.copy()
    ring_indices = df[df['is_ring_member'] == True].index.tolist()
    
    # Scramble ~40% of the true fraudsters
    random.seed(42)
    evaders = random.sample(ring_indices, int(len(ring_indices) * 0.4))
    for idx in evaders:
        df.at[idx, 'ip_subnet'] = f"192.168.{random.randint(0,255)}.{random.randint(0,255)}"
        df.at[idx, 'device_id'] = str(uuid.uuid4())

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
# Sidebar: What-If Business Impact Calculator
# ---------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("What-If Business Impact")
st.sidebar.markdown("<small>Estimated Rupee trade-off at current threshold</small>", unsafe_allow_html=True)

actual_ring_count = int(df['is_ring_member'].sum())
fraud_savings = metrics['recall'] * actual_ring_count * 25000  # Dynamically derived ring count × avg ₹25,000 saved
review_cost = metrics['false_positive_cost_inr']
net_impact = fraud_savings - review_cost

st.sidebar.markdown(f"**Fraud Blocked Savings:** <span style='color:#4ade80'>+₹{fraud_savings:,.0f}</span>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Manual Review Cost:** <span style='color:#f87171'>-₹{review_cost:,.0f}</span>", unsafe_allow_html=True)

color = "#4ade80" if net_impact >= 0 else "#f87171"
st.sidebar.markdown(f"**Net Business Impact:** <span style='color:{color}'>₹{net_impact:,.0f}</span>", unsafe_allow_html=True)

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
                    log_action(c['cluster_id'], "CONFIRMED FRAUD", c['density_score'], c['shared_signals'])
                    st.rerun()
            with col3:
                if st.button("❌ Dismiss (FP)", key=f"dismiss_{c['cluster_id']}", use_container_width=True):
                    st.session_state.human_overrides[c['cluster_id']] = "LOW_RISK"
                    log_action(c['cluster_id'], "DISMISSED (FP)", c['density_score'], c['shared_signals'])
                    st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# UI Layout: Cluster Investigation Table & Modals
# ---------------------------------------------------------------------
def generate_sar_pdf(cluster, explanation):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Header
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(200, 10, txt="Suspicious Activity Report (SAR)", ln=True, align="C")
    pdf.ln(5)
    
    # Cluster Details
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(200, 10, txt=f"Cluster ID: {cluster['cluster_id']}", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 8, txt=f"Assigned Risk Tier: {cluster['confidence_tier']}", ln=True)
    pdf.cell(200, 8, txt=f"Density Score: {cluster['density_score']} (Accounts: {cluster['cluster_size']})", ln=True)
    pdf.ln(5)
    
    # Shared Signals
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(200, 10, txt="Shared Infrastructure / Attributes:", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, txt=", ".join(cluster['shared_signals']))
    pdf.ln(5)
    
    # Member Accounts
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(200, 10, txt="Identified Member Accounts:", ln=True)
    pdf.set_font("Helvetica", size=10)
    for node_id, data in cluster['subgraph'].nodes(data=True):
        # Sanitize to ascii to avoid FPDF core font unicode errors, and truncate UUID
        safe_name = str(data.get('name', 'Unknown')).encode('ascii', 'ignore').decode()
        safe_email = str(data.get('email', 'Unknown')).encode('ascii', 'ignore').decode()
        short_id = str(node_id)[:8]
        line = f"- ID: {short_id}... | Name: {safe_name} | Email: {safe_email}"
        pdf.write(6, line)
        pdf.ln(6)
    pdf.ln(5)
    
    # AI Explanation
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(200, 10, txt="AI Analyst Rationale:", ln=True)
    pdf.set_font("Helvetica", size=10)
    try:
        exp_data = json.loads(explanation)
        for k, v in exp_data.items():
            pdf.set_font("Helvetica", style="B", size=10)
            pdf.cell(200, 8, txt=f"{k.replace('_', ' ').title()}:", ln=True)
            pdf.set_font("Helvetica", size=10)
            val_str = ", ".join(v) if isinstance(v, list) else str(v)
            val_str = val_str.encode('ascii', 'ignore').decode().replace('\n', ' ')
            pdf.multi_cell(0, 6, txt=val_str)
            pdf.ln(2)
    except:
        safe_exp = str(explanation).encode('ascii', 'ignore').decode().replace('\n', ' ')
        pdf.multi_cell(0, 6, txt=safe_exp)
        
    return bytes(pdf.output())

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
                # Cache explanations in session_state so API doesn't re-fire on every rerun
                if selected_cluster_id not in st.session_state.explanations:
                    with st.spinner("Querying AI Analyst..."):
                        st.session_state.explanations[selected_cluster_id] = explain_cluster(selected_cluster)
                selected_cluster['explanation'] = st.session_state.explanations[selected_cluster_id]
                
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
            
            # Action Buttons & PDF Download
            action_cols = st.columns(2)
            
            with action_cols[0]:
                if selected_cluster['confidence_tier'] != "HIGH_CONFIDENCE":
                    if st.button(f"🚫 Confirm Block ({selected_cluster['cluster_size']} accounts)", type="primary", use_container_width=True, key="block_deepdive"):
                        st.session_state.human_overrides[selected_cluster_id] = "HIGH_CONFIDENCE"
                        log_action(selected_cluster_id, "CONFIRMED FRAUD", selected_cluster['density_score'], selected_cluster['shared_signals'])
                        st.rerun()
                else:
                    pdf_bytes = generate_sar_pdf(selected_cluster, selected_cluster['explanation'])
                    st.download_button(
                        label="📄 Download Suspicious Activity Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"SAR_{selected_cluster_id}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
            
            with action_cols[1]:
                if selected_cluster['confidence_tier'] != "LOW_RISK":
                    if st.button("✅ Dismiss Flag (Mark False Positive)", use_container_width=True):
                        st.session_state.human_overrides[selected_cluster_id] = "LOW_RISK"
                        log_action(selected_cluster_id, "DISMISSED (FP)", selected_cluster['density_score'], selected_cluster['shared_signals'])
                        st.rerun()
                else:
                    json_bundle = {
                        "cluster_id": selected_cluster['cluster_id'],
                        "size": selected_cluster['cluster_size'],
                        "density_score": selected_cluster['density_score'],
                        "shared_signals": selected_cluster['shared_signals'],
                        "members": [
                            {"node_id": str(n), "name": str(d.get('name')), "email": str(d.get('email'))} 
                            for n, d in selected_cluster['subgraph'].nodes(data=True)
                        ],
                        "ai_rationale": selected_cluster['explanation']
                    }
                    st.download_button(
                        label="📦 Download Evidence Bundle (.JSON)",
                        data=json.dumps(json_bundle, indent=2),
                        file_name=f"Evidence_{selected_cluster_id}.json",
                        mime="application/json",
                        use_container_width=True
                    )

# ---------------------------------------------------------------------
# UI Layout: Analyst Audit History
# ---------------------------------------------------------------------
st.markdown("---")
with st.expander("📋 Analyst Audit History", expanded=False):
    if len(st.session_state.audit_log) == 0:
        st.info("No actions taken yet during this session.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.audit_log), use_container_width=True)
