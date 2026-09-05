# 🛡️ GraphSentinel AI

**GraphSentinel AI** (formerly Abuse-Ring Sentinel) is an intelligent, human-in-the-loop graph network analysis platform designed to detect, visualize, and explain coordinated fraud rings in real-time. 

Built for the **Razorpay AI Buildathon 2026**, this project leverages graph theory (NetworkX), interactive physics-based visualizations (Pyvis + Streamlit), and large language models (Groq + Llama-3.3-70b-versatile) to give fraud analysts superpower capabilities.

---

## ✨ Key Features

- **🕸️ Graph-Based Ring Detection**: Automatically clusters users based on shared infrastructure (Card Fingerprints, Device IDs, IP Subnets, and Shipping Addresses) using deterministic graph algorithms.
- **🔴 Interactive Network Visualization**: A fully interactive, physics-based 2D network graph. Red nodes indicate high-confidence fraud rings, Yellow indicates review-tier clusters, and Blue indicates legitimate independent accounts.
- **🤖 AI Fraud Analyst**: Uses Groq's lightning-fast inference and the Llama 3.3 70B model to generate human-readable explanations and risk assessments for every flagged cluster. 
- **⚖️ Human-in-the-Loop Queue**: Analysts can manually "Confirm" or "Dismiss" flagged clusters in real-time, instantly updating system metrics (Precision, Recall, False Positive Cost) to demonstrate how human feedback improves model performance.
- **⚡ Live Simulation Controls**: Dynamically tweak signal weights and density thresholds via the Streamlit sidebar and watch the network topology rebuild itself instantly.

---

## 🛠️ Tech Stack
- **Frontend & UI**: Streamlit, HTML/CSS (Glassmorphism design)
- **Graph Processing**: NetworkX, Pyvis
- **Data Generation**: Pandas, Faker (seeded for reproducibility)
- **AI/LLM Engine**: Groq SDK (`llama-3.3-70b-versatile`)

---

## 🚀 How to Run Locally

### 1. Install Dependencies
Make sure you have Python 3.11+ installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Set API Keys
GraphSentinel AI uses Groq to generate intelligent explanations for fraud rings. Set your Groq API key in your terminal:
```bash
# On Windows PowerShell
$env:GROQ_API_KEY="your-groq-api-key-here"

# On Mac/Linux
export GROQ_API_KEY="your-groq-api-key-here"
```
*(Note: The system features a deterministic fallback engine. If no API key is provided, the dashboard will still fully function using a templated response system!)*

### 3. Launch the Streamlit Dashboard
Navigate to the `src` directory and spin up the server:
```bash
cd src
python -m streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 📊 Pipeline Architecture
1. **Data Generation (`data_generator.py`)**: Synthesizes 432 customer records, embedding 7 dense abuse rings and 5 tricky "hard negative" groups to test the algorithm's precision.
2. **Graph Builder (`graph_builder.py`)**: Constructs an undirected network where nodes are customers and edges are shared signals (weighted dynamically).
3. **Cluster Scorer (`cluster_scorer.py`)**: Extracts connected components, calculates subgraph density, and assigns a risk tier (High Confidence, Review, or Low Risk).
4. **Explanation Layer (`explanation_layer.py`)**: Passes graph topologies to the Groq LLM to generate plain-text analyst reports.
5. **Streamlit App (`app.py`)**: Orchestrates the pipeline and renders the interactive physics graph and Analyst Review Queue.

---
*Developed with ❤️ for the Razorpay AI Buildathon 2026*
