import json
import networkx as nx
import pandas as pd
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import glob
from network import *

#PageRank 1000 faculty extraction with degree betweeness for comparison:
def page_rank_network():
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

def new_1000_network():

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

def overall_info():
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
    
def compare_with_random_network(year = 2025):
    graphml_path = f"graphs/collaboration_network_{str(year)}.graphml"
    collaboration_network = nx.read_graphml(graphml_path)

    # Compute statistics
    num_nodes = collaboration_network.number_of_nodes()
    num_edges = collaboration_network.number_of_edges()
    avg_degree = sum(dict(collaboration_network.degree()).values()) / num_nodes
    clustering_coefficient = nx.average_clustering(collaboration_network)
    # Generate an Erdős-Rényi random graph with same number of nodes and edges
    print("\nGenerating comparable random network...")
    random_network = nx.gnm_random_graph(num_nodes, num_edges)
    
    # Compute statistics for random graph
    random_avg_degree = sum(dict(random_network.degree()).values()) / num_nodes
    random_clustering_coefficient = nx.average_clustering(random_network)
    random_avg_path_length = nx.average_shortest_path_length(random_network) if nx.is_connected(random_network) else float('inf')
    # Compare with original graph
    print("\nRandom Graph Statistics:")
    print(f"Number of nodes: {random_network.number_of_nodes()}")
    print(f"Number of edges: {random_network.number_of_edges()}")
    print(f"Average degree: {random_avg_degree:.2f}")
    print(f"Clustering coefficient: {random_clustering_coefficient:.4f}")
    
    print("\nComparison ratios (real/random):")
    print(f"Clustering coefficient ratio: {clustering_coefficient/random_clustering_coefficient:.2f}x")
    # Print statistics
    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    print(f"Average degree: {avg_degree:.2f}")
    print(f"Clustering coefficient: {clustering_coefficient:.4f}")
    
    
    # visualization
    # Calculate degree distribution for real network
    degrees = [d for _, d in collaboration_network.degree()]
    degree_counts = Counter(degrees)

    # Convert to arrays for plotting
    unique_degrees = sorted(degree_counts.keys())
    count_values = [degree_counts[d] for d in unique_degrees]

    # Calculate degree distribution for random network
    random_degrees = [d for _, d in random_network.degree()]
    random_degree_counts = Counter(random_degrees)

    # Convert to arrays for plotting
    random_unique_degrees = sorted(random_degree_counts.keys())
    random_count_values = [random_degree_counts[d] for d in random_unique_degrees]

    # Calculate average degree for random network
    avg_degree_random = sum(dict(random_network.degree()).values()) / len(random_network)
    # Create a figure with two subplots: linear scale and log scale
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Subplot 1: Linear scale (original plot)
    ax1.scatter(unique_degrees, count_values, color='red', alpha=0.7, s=50)
    ax1.scatter(random_unique_degrees, random_count_values, color='blue', alpha=0.7, s=50)
    ax1.set_title("Degree Distribution - Linear Scale")
    ax1.set_xlabel("Degree (k)")
    ax1.set_ylabel("Number of Nodes with Degree k")
    ax1.grid(True, which="both", linestyle='--', alpha=0.7)
    ax1.legend(['Collaboration Network', 'Random Network'])

    # Subplot 2: Log-log scale
    ax2.scatter(unique_degrees, count_values, color='red', alpha=0.7, s=50)
    ax2.scatter(random_unique_degrees, random_count_values, color='blue', alpha=0.7, s=50)
    ax2.set_title("Degree Distribution - Log-Log Scale")
    ax2.set_xlabel("Degree (k)")
    ax2.set_ylabel("Number of Nodes with Degree k")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.grid(True, which="both", linestyle='--', alpha=0.7)
    ax2.legend(['Collaboration Network', 'Random Network'])

    plt.tight_layout()
    plt.show()
    
    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "avg_degree": avg_degree,
        "clustering_coefficient": clustering_coefficient
    }

def visualize_statistics_change():
    
    #create collaboration networks for each year
    networks = build_collaboration_networks('main_authors_collaborations.csv')
    
    #### Visualizing nodes and edges over time
    
    # Prepare data for plotting
    years = sorted(networks.keys())
    num_nodes = [networks[year].number_of_nodes() for year in years]
    num_edges = [networks[year].number_of_edges() for year in years]
    avg_degrees = [2 * num_edges[i] / num_nodes[i] if num_nodes[i] > 0 else 0 for i in range(len(years))]

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(years, num_nodes, label='Number of Nodes', marker='o')
    plt.plot(years, num_edges, label='Number of Edges', marker='s')
    # plt.plot(years, avg_degrees, label='Average Degree', marker='^')

    # Add labels, legend, and title
    plt.xlabel('Year')
    plt.ylabel('Value')
    plt.title('Change in Network Properties Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Show the plot
    plt.show()
    
    
    #### Visualizing average degree and ln(N) over time
    # Calculate average degrees and ln(N)
    avg_degrees = [2 * num_edges[i] / num_nodes[i] if num_nodes[i] > 0 else 0 for i in range(len(years))]
    ln_N = [np.log(n) for n in num_nodes]

    # Plot both metrics
    plt.figure(figsize=(10, 6))
    plt.plot(years, avg_degrees, label='Average Degree', marker='^', color='blue')
    plt.plot(years, ln_N, label='ln(N)', marker='o', color='green')

    # Add labels, legend, and title
    plt.xlabel('Year')
    plt.ylabel('Value')
    plt.title('Average Degree vs ln(N) Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Show the plot
    plt.show()
    
    
def analyze_faculty_collaboration(year = 2025, attribute_name="position"):
    """
    Analyze faculty collaboration network based on a specific attribute
    
    Parameters:
    - collaboration_network: NetworkX graph of faculty collaborations
    - attribute_name: The node attribute to analyze (e.g., "position", "area", "management")
    
    Returns:
    - Dictionary containing analysis results
    """
    # Extract attribute information for each node
    attribute_data = {}
    node_attributes = {}
    graphml_path = f"graphs/collaboration_network_{str(year)}.graphml"
    collaboration_network = nx.read_graphml(graphml_path)
    # Get attribute for each node
    for node in collaboration_network.nodes():
        attribute = collaboration_network.nodes[node].get(attribute_name, 'Unknown')
        node_attributes[node] = attribute

        if attribute not in attribute_data:
            attribute_data[attribute] = []
        attribute_data[attribute].append(node)

    # Count the number of nodes in each attribute category
    attribute_counts = {attr: len(nodes) for attr, nodes in attribute_data.items()}
    print(f"Distribution of faculty by {attribute_name}:")
    for attr, count in sorted(attribute_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{attr}: {count} faculty")

    # Calculate internal and external collaborations for each attribute value
    attribute_collaborations = defaultdict(lambda: {'internal': 0, 'external': 0, 'nodes': 0})

    for attribute, nodes in attribute_data.items():
        attribute_collaborations[attribute]['nodes'] = len(nodes)

        # Count internal collaborations (within same attribute value)
        for node in nodes:
            for neighbor in collaboration_network.neighbors(node):
                neighbor_attribute = node_attributes.get(neighbor, 'Unknown')

                if neighbor_attribute == attribute:
                    attribute_collaborations[attribute]['internal'] += 0.5  # Count each edge once
                else:
                    attribute_collaborations[attribute]['external'] += 0.5  # Count each edge once

    # Convert the defaultdict to a dataframe
    collab_df = pd.DataFrame.from_dict(attribute_collaborations, orient='index')
    collab_df['avg_internal'] = collab_df['internal'] / collab_df['nodes']
    collab_df['avg_external'] = collab_df['external'] / collab_df['nodes']
    collab_df['total_collaborations'] = collab_df['internal'] + collab_df['external']
    collab_df['avg_total'] = collab_df['total_collaborations'] / collab_df['nodes']
    collab_df['internal_ratio'] = collab_df['internal'] / collab_df['total_collaborations'].replace(0, np.nan)
    collab_df['internal_ratio'] = collab_df['internal_ratio'].fillna(0)

    # Sort by total collaborations
    collab_df = collab_df.sort_values('avg_total', ascending=False)

    # Analyze the collaboration across different attribute values
    cross_attribute_edges = []
    for u, v in collaboration_network.edges():
        attr_u = node_attributes.get(u, 'Unknown')
        attr_v = node_attributes.get(v, 'Unknown')
        if attr_u != attr_v and attr_u != 'Unknown' and attr_v != 'Unknown':
            cross_attribute_edges.append((attr_u, attr_v))

    # Count the frequency of each collaboration type
    cross_collab_counts = Counter(cross_attribute_edges)

    # Create an adjacency matrix for attribute collaborations
    unique_attributes = sorted(attribute_data.keys())
    attribute_matrix = pd.DataFrame(0, index=unique_attributes, columns=unique_attributes)

    for (attr1, attr2), count in cross_collab_counts.items():
        attribute_matrix.loc[attr1, attr2] += count
        attribute_matrix.loc[attr2, attr1] += count  # Make it symmetric

    return {
        'node_attributes': node_attributes,
        'attribute_data': attribute_data,
        'attribute_counts': attribute_counts,
        'attribute_collaborations': attribute_collaborations,
        'collab_df': collab_df,
        'cross_attribute_edges': cross_attribute_edges,
        'cross_collab_counts': cross_collab_counts,
        'attribute_matrix': attribute_matrix,
        'unique_attributes': unique_attributes
    }


def visualize_collaboration_patterns(results, attribute_name="position", min_faculty=3):
    """
    Create visualizations for faculty collaboration patterns
    
    Parameters:
    - results: Dictionary containing analysis results
    - attribute_name: The node attribute analyzed
    - min_faculty: Minimum number of faculty to include in visualizations
    """
    collab_df = results['collab_df']
    attribute_matrix = results['attribute_matrix']
    attribute_data = results['attribute_data']
    unique_attributes = results['unique_attributes']
    
    # Filter out attributes with very few faculty
    filtered_df = collab_df[collab_df['nodes'] >= min_faculty]
    attributes = filtered_df.index
    ind = np.arange(len(attributes))
    
    # 1. Enhanced stacked bar chart
    plt.figure(figsize=(14, 8))
    
    # First plot internal collaborations
    plt.bar(ind, filtered_df['avg_internal'], width=0.6, label=f'Average Internal Collaborations',
            color='#3274A1', edgecolor='white', linewidth=0.7)
    # Then stack external collaborations on top
    plt.bar(ind, filtered_df['avg_external'], width=0.6, bottom=filtered_df['avg_internal'],
            label='Average External Collaborations', color='#E1812C', edgecolor='white', linewidth=0.7)

    # Add total values on top of each bar
    for i, total in enumerate(filtered_df['avg_total']):
        plt.text(i, total + 0.1, f'{total:.1f}', ha='center', fontweight='bold')

    plt.xlabel(f'Faculty {attribute_name.title()}', fontsize=12)
    plt.ylabel('Average Number of Collaborations', fontsize=12)
    plt.title(f'Academic Collaboration Patterns by Faculty {attribute_name.title()}', fontsize=14, fontweight='bold')
    plt.xticks(ind, attributes, rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

    # 2. Improved visualization: Attribute Network Graph
    plt.figure(figsize=(14, 12))

    # Create a directed graph
    G = nx.Graph()

    # Add nodes for each attribute value with size based on faculty count
    for attribute in unique_attributes:
        G.add_node(attribute, size=len(attribute_data[attribute]))

    # Add edges with weights based on collaboration count
    for i, attr1 in enumerate(unique_attributes):
        for j, attr2 in enumerate(unique_attributes):
            if i < j and attribute_matrix.loc[attr1, attr2] > 0:
                G.add_edge(attr1, attr2, weight=attribute_matrix.loc[attr1, attr2])

    # Define node positions using spring layout
    pos = nx.spring_layout(G, seed=42, k=0.4)

    # Get edge weights for line thickness
    edge_weights = [G[u][v]['weight'] * 0.8 for u, v in G.edges()]
    max_weight = max(edge_weights) if edge_weights else 1

    # Get node sizes based on faculty count
    node_sizes = [G.nodes[node]['size'] * 100 for node in G.nodes()]

    # Draw the network
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='skyblue',
                           edgecolors='black', alpha=0.8)

    # Draw edges with thickness based on weight
    nx.draw_networkx_edges(G, pos, width=[w/max_weight * 5 for w in edge_weights],
                           edge_color='gray', alpha=0.7)

    # Draw labels with uniform font size
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')

    # Add edge labels showing the number of collaborations
    edge_labels = {(u, v): f"{G[u][v]['weight']:.0f}" for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

    plt.title(f'{attribute_name.title()} Collaboration Network', fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

    # 3. Heatmap visualization of collaboration counts
    import seaborn as sns
    plt.figure(figsize=(12, 10))
    mask = np.zeros_like(attribute_matrix)
    mask[np.triu_indices_from(mask, k=1)] = True  # Keep only the lower triangular part
    sns.heatmap(attribute_matrix, annot=True, fmt=".0f", cmap="YlOrRd",
                linewidths=1, mask=mask, cbar_kws={'label': 'Number of Collaborations'})
    plt.title(f'Cross-{attribute_name.title()} Collaboration Matrix', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()


# Main function to run the analysis
def analyze_and_visualize_collaboration(year = 2025, attribute_name="position", min_faculty=3):
    """
    Run full analysis and visualization of faculty collaboration network
    
    Parameters:
    - collaboration_network: NetworkX graph of faculty collaborations
    - attribute_name: The node attribute to analyze (e.g., "position", "area", "management")
    - min_faculty: Minimum number of faculty to include in visualizations
    """
    results = analyze_faculty_collaboration(year, attribute_name)
    visualize_collaboration_patterns(results, attribute_name, min_faculty)
    return results

if __name__ == '__main__':
    # Uncomment the function you want to run
    # pageRankNetWork()
    # new1000Network()
    # overallInfo()
    # network_degree_plot()
    analyze_and_visualize_collaboration()
    # pass