import networkx as nx
from typing import List, Dict, Any

def score_clusters(G: nx.Graph, auto_flag_threshold: float = 2.5) -> List[Dict[str, Any]]:
    """
    Extracts connected components from the graph, computes density scores,
    and applies confidence tiering.
    """
    # 1. Extract connected components
    components = list(nx.connected_components(G))
    
    scored_clusters = []
    
    for i, comp in enumerate(components):
        # We only care about clusters with > 1 node
        if len(comp) > 1:
            subgraph = G.subgraph(comp)
            cluster_size = subgraph.number_of_nodes()
            
            # 2. Compute Density: Sum of edge weights / Cluster size
            total_edge_weight = sum([d['weight'] for u, v, d in subgraph.edges(data=True)])
            density = total_edge_weight / cluster_size
            
            # 3. Apply Confidence Tiering logic
            if density >= auto_flag_threshold:
                tier = "HIGH_CONFIDENCE"
                action = "AUTO_FLAG"
            elif density >= 1.0:
                tier = "REVIEW"
                action = "ROUTE_TO_HUMAN"
            else:
                tier = "LOW_RISK"
                action = "IGNORE"
                
            # Compile shared signals for reporting
            all_shared_signals = set()
            for u, v, d in subgraph.edges(data=True):
                all_shared_signals.update(d['shared_signals'])
            
            # Compute hub node via betweenness centrality
            centrality = nx.betweenness_centrality(subgraph, weight='weight')
            hub_node_id = max(centrality, key=centrality.get) if centrality else list(comp)[0]
                
            scored_clusters.append({
                'cluster_id': f"C-{i+1}",
                'node_ids': list(comp),
                'cluster_size': cluster_size,
                'total_edge_weight': total_edge_weight,
                'density_score': round(density, 2),
                'confidence_tier': tier,
                'recommended_action': action,
                'shared_signals': list(all_shared_signals),
                'hub_node_id': hub_node_id,
                # Storing subgraph reference for later deep-dives if needed
                'subgraph': subgraph
            })
            
    # Sort clusters by density score descending
    scored_clusters.sort(key=lambda x: x['density_score'], reverse=True)
    return scored_clusters

if __name__ == "__main__":
    from data_generator import generate_dataset
    from graph_builder import build_signal_graph
    
    df = generate_dataset()
    G = build_signal_graph(df)
    clusters = score_clusters(G)
    
    print(f"Found {len(clusters)} clusters (size > 1).")
    for c in clusters:
        print(f"{c['cluster_id']}: Size={c['cluster_size']}, Density={c['density_score']}, Tier={c['confidence_tier']}")
