import networkx as nx
import pandas as pd

def build_signal_graph(df: pd.DataFrame, signal_weights: dict = None) -> nx.Graph:
    """
    Builds an undirected graph mapping customers as nodes and shared signals as weighted edges.
    Strictly ignores the 'is_ring_member' column to prevent data leakage.
    """
    G = nx.Graph()
    
    # 1. Add all customers as nodes
    for idx, row in df.iterrows():
        # Store metadata in the node for later extraction/reporting, EXCLUDING ground truth
        G.add_node(row['customer_id'], 
                   name=row['name'],
                   email=row['email'],
                   device_id=row['device_id'],
                   ip_subnet=row['ip_subnet'],
                   card_fingerprint=row['card_fingerprint'],
                   shipping_address=row['shipping_address'])
                   
    # Group accounts by signals to efficiently create edges
    # Weight mappings based on ADR 001
    if signal_weights is None:
        signal_weights = {
            'card_fingerprint': 4.0,
            'device_id': 3.0,
            'shipping_address': 2.0,
            'ip_subnet': 1.0
        }
    
    # 2. Add edges for shared attributes
    for signal_type, weight in signal_weights.items():
        # Group by the specific signal type
        # For example, all users with the same device_id
        grouped = df.groupby(signal_type)
        
        for signal_value, group_df in grouped:
            # We only care if more than 1 person shares the signal
            if len(group_df) > 1:
                customer_ids = group_df['customer_id'].tolist()
                # Create edges between all pairs in this group (clique)
                for i in range(len(customer_ids)):
                    for j in range(i + 1, len(customer_ids)):
                        u = customer_ids[i]
                        v = customer_ids[j]
                        
                        # If edge already exists (they share multiple attributes), add to the weight
                        if G.has_edge(u, v):
                            G[u][v]['weight'] += weight
                            G[u][v]['shared_signals'].append(signal_type)
                        else:
                            G.add_edge(u, v, weight=weight, shared_signals=[signal_type])
                            
    return G

if __name__ == "__main__":
    from data_generator import generate_dataset
    df = generate_dataset()
    G = build_signal_graph(df)
    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
