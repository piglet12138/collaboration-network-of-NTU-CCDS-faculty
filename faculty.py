import json
import networkx as nx
import pandas as pd
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

#PageRank 1000 faculty extraction with degree betweeness for comparison:
def pageRankNetWork():
    # Define file paths
    base_path = r"" #subsitute with relative path
    papers_file = r"papers_by_key_cleaned.json"
    main_authors_file = r"main_authors.json"

    # Load data
    with open(papers_file, "r", encoding="utf-8") as f:
        papers = json.load(f)

    with open(main_authors_file, "r", encoding="utf-8") as f:
        main_authors_data = json.load(f)

    # Extract main author pids
    main_author_pids = {author['pid'] for author in main_authors_data}

    # Build co-authorship graph
    G = nx.Graph()
    pid_to_name = {}

    for paper in papers.values():
        pids = [author["pid"] for author in paper["authors"]]
        for author in paper["authors"]:
            pid_to_name[author["pid"]] = author["name"]
        for i in range(len(pids)):
            for j in range(i + 1, len(pids)):
                G.add_edge(pids[i], pids[j])

    # Helper to get top nodes
    def get_top_nodes(centrality_dict, exclude_pids, top_n=1000):
        filtered = {pid: score for pid, score in centrality_dict.items() if pid not in exclude_pids}
        return sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Compute and save Degree Centrality
    degree_centrality = nx.degree_centrality(G)
    top_degree = get_top_nodes(degree_centrality, main_author_pids)
    df_degree = pd.DataFrame([
        {"pid": pid, "name": pid_to_name.get(pid, "Unknown"), "degree_score": score}
        for pid, score in top_degree
    ])
    df_degree.to_csv(r"top_1000_degree_centrality.csv", index=False)

    # Compute and save PageRank
    pagerank = nx.pagerank(G)
    top_pagerank = get_top_nodes(pagerank, main_author_pids)
    df_pagerank = pd.DataFrame([
        {"pid": pid, "name": pid_to_name.get(pid, "Unknown"), "pagerank_score": score}
        for pid, score in top_pagerank
    ])
    df_pagerank.to_csv(r"top_1000_pagerank.csv", index=False)

    print("CSV files saved successfully:")
    print("- top_1000_degree_centrality.csv")
    print("- top_1000_pagerank.csv")

def new1000Network():

    # Define file paths
    base_path = r""
    papers_file = r"papers_by_key_cleaned.json"
    main_authors_file = r"main_authors.json"

    # Load data
    with open(papers_file, "r", encoding="utf-8") as f:
        papers = json.load(f)

    with open(main_authors_file, "r", encoding="utf-8") as f:
        main_authors_data = json.load(f)

    # Extract main author pids
    main_author_pids = {author['pid'] for author in main_authors_data}

    # Build co-authorship graph with weights
    G = nx.Graph()
    pid_to_name = {}

    for paper in papers.values():
        pids = [author["pid"] for author in paper["authors"]]
        for author in paper["authors"]:
            pid_to_name[author["pid"]] = author["name"]
        for i in range(len(pids)):
            for j in range(i + 1, len(pids)):
                pid1, pid2 = pids[i], pids[j]
                if G.has_edge(pid1, pid2):
                    G[pid1][pid2]['weight'] += 1
                else:
                    G.add_edge(pid1, pid2, weight=1)

    # Helper to get top nodes
    def get_top_nodes(centrality_dict, exclude_pids, top_n=1000):
        filtered = {pid: score for pid, score in centrality_dict.items() if pid not in exclude_pids}
        return sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Weighted Degree Centrality (not normalized)
    weighted_degree = {node: sum(weight for _, _, weight in G.edges(node, data='weight')) for node in G.nodes}
    top_degree = get_top_nodes(weighted_degree, main_author_pids)
    df_degree = pd.DataFrame([
        {"pid": pid, "name": pid_to_name.get(pid, "Unknown"), "weighted_degree": score}
        for pid, score in top_degree
    ])
    df_degree.to_csv(r"top_1000_weighted_degree.csv", index=False)

    # Weighted PageRank
    pagerank = nx.pagerank(G, weight='weight')
    top_pagerank = get_top_nodes(pagerank, main_author_pids)
    df_pagerank = pd.DataFrame([
        {"pid": pid, "name": pid_to_name.get(pid, "Unknown"), "pagerank_score": score}
        for pid, score in top_pagerank
    ])
    df_pagerank.to_csv( r"top_1000_weighted_pagerank.csv", index=False)

    # -------- Filter the graph to keep only top 1000 pagerank + main authors --------
    top_1000_pagerank_pids = {pid for pid, _ in top_pagerank}
    nodes_to_keep = top_1000_pagerank_pids.union(main_author_pids)
    nodes_to_remove = set(G.nodes()) - nodes_to_keep

    G.remove_nodes_from(nodes_to_remove)

    # Optional: Save the filtered graph as GraphML or GEXF (for Gephi visualization)
    nx.write_graphml(G, r"filtered_collab_network.graphml")
    # Or save in another format:
    # nx.write_gexf(G, base_path + r"\filtered_collab_network.gexf")

    print("CSV files saved successfully:")
    print("- top_1000_weighted_degree.csv")
    print("- top_1000_weighted_pagerank.csv")
    print("Filtered graph saved as 'filtered_collab_network.graphml'")

def overallInfo():
    # Load filtered graph
    graphml_path = r"filtered_collab_network.graphml"
    G = nx.read_graphml(graphml_path)

    # Basic stats
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    # Clustering coefficient
    clustering_coeff = nx.average_clustering(G)

    # Handle disconnected graphs for distance
    if nx.is_connected(G):
        avg_shortest_path = nx.average_shortest_path_length(G)
    else:
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        avg_shortest_path = nx.average_shortest_path_length(subgraph)

    # Average degree
    avg_degree = sum(dict(G.degree()).values()) / num_nodes

    # Print results
    print(f" Graph Statistics:")
    print(f"- Number of nodes: {num_nodes}")
    print(f"- Number of edges: {num_edges}")
    print(f"- Average clustering coefficient: {clustering_coeff:.4f}")
    print(f"- Average shortest path length (largest component): {avg_shortest_path:.4f}")
    print(f"- Average degree: {avg_degree:.2f}")

def network_degree_plot():
    # Load your filtered graph
    graphml_path = r"filtered_collab_network.graphml"
    G = nx.read_graphml(graphml_path)

    # Compute degree distribution
    degrees = [d for _, d in G.degree()]
    degree_count = Counter(degrees)

    # Prepare data for plotting
    k = np.array(list(degree_count.keys()))
    pk = np.array(list(degree_count.values())) / sum(degree_count.values())  # normalize to get probabilities

    # Sort by degree
    sorted_idx = np.argsort(k)
    k = k[sorted_idx]
    pk = pk[sorted_idx]

    # Plot on log-log scale
    plt.figure(figsize=(8, 6))
    plt.scatter(k, pk, color='red', label='Empirical', s=10)
    plt.plot(k, pk, linestyle='None')  # dotted line optional

    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel(r"$k$ (Degree)", fontsize=12)
    plt.ylabel(r"$p_k$ (Probability)", fontsize=12)
    plt.title("Degree Distribution (Log-Log)", fontsize=14)
    plt.grid(True, which="both", ls="--", linewidth=0.5)
    plt.tight_layout()
    plt.show()
    
def get_network_statistics(year = 2025):
    # Load your filtered graph
    graphml_path = f"graphs/collaboration_network_{str(year)}.graphml"
    G = nx.read_graphml(graphml_path)

    # Compute statistics
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    avg_degree = sum(dict(G.degree()).values()) / num_nodes
    clustering_coefficient = nx.average_clustering(G)
    # Average path length (computed for the largest connected component if graph is not connected)
    if nx.is_connected(G):
        avg_path_length = nx.average_shortest_path_length(G)
    else:
        largest_cc = max(nx.connected_components(G), key=len)
        largest_cc_subgraph = G.subgraph(largest_cc)
        avg_path_length = nx.average_shortest_path_length(largest_cc_subgraph)

    # Print statistics
    print('Collaboration Network Statistics:')
    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    print(f"Average degree: {avg_degree:.2f}")
    print(f"Clustering coefficient: {clustering_coefficient:.4f}")
    print(f"Average path length: {avg_path_length:.4f}")
    
    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "avg_degree": avg_degree,
        "clustering_coefficient": clustering_coefficient,
        "avg_path_length": avg_path_length
    }
    
def get_comparable_random_network_statistics(year = 2025):
    graphml_path = f"graphs/collaboration_network_{str(year)}.graphml"
    G = nx.read_graphml(graphml_path)

    # Compute statistics
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    avg_degree = sum(dict(G.degree()).values()) / num_nodes
    clustering_coefficient = nx.average_clustering(G)
    # Generate an Erdős-Rényi random graph with same number of nodes and edges
    print("\nGenerating comparable random network...")
    random_G = nx.gnm_random_graph(num_nodes, num_edges)
    
    # Compute statistics for random graph
    random_avg_degree = sum(dict(random_G.degree()).values()) / num_nodes
    random_clustering_coefficient = nx.average_clustering(random_G)
    random_avg_path_length = nx.average_shortest_path_length(random_G) if nx.is_connected(random_G) else float('inf')
    # Compare with original graph
    print("\nRandom Graph Statistics:")
    print(f"Number of nodes: {random_G.number_of_nodes()}")
    print(f"Number of edges: {random_G.number_of_edges()}")
    print(f"Average degree: {random_avg_degree:.2f}")
    print(f"Clustering coefficient: {random_clustering_coefficient:.4f}")
    
    print("\nComparison ratios (real/random):")
    print(f"Clustering coefficient ratio: {clustering_coefficient/random_clustering_coefficient:.2f}x")
    # Print statistics
    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    print(f"Average degree: {avg_degree:.2f}")
    print(f"Clustering coefficient: {clustering_coefficient:.4f}")
    
    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "avg_degree": avg_degree,
        "clustering_coefficient": clustering_coefficient
    }
    
if __name__ == '__main__':
    # Uncomment the function you want to run
    # pageRankNetWork()
    # new1000Network()
    # overallInfo()
    # network_degree_plot()
    get_network_statistics(year=2025)
    get_comparable_random_network_statistics(=2025)
    # pass