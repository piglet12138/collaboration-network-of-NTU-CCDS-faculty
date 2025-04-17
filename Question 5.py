# -*- coding: utf-8 -*-
"""
Answering Question 5 using this script
 
"""
# Import necessary libraries for data handling, network analysis, and visualisation
import pandas as pd
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# Compute the average value of a given centrality metric for a specific subset of nodes
def avg_metric(metric_dict, node_set):
    values = [metric_dict[n] for n in node_set if n in metric_dict]
    return np.mean(values) if values else 0 

# Read collaboration and faculty data, merge relevant metadata, and construct yearly collaboration networks (accumulative).
def build_collaboration_networks(main_authors_collaborations_csv = 'main_authors_collaborations.csv', faculty_csv = 'Faculty_with_excellence_v2.csv'):

    df = pd.read_csv(main_authors_collaborations_csv)
    faculty_info = pd.read_csv(faculty_csv)
    print(faculty_info['Excellence'].value_counts())
    print(faculty_info['Top_10_Excellence'].value_counts())
    print(faculty_info['Excellence'].unique())
    print(faculty_info['Top_10_Excellence'].unique())

    # Merge faculty information with collaboration data

    # Merge on author_pid = pid, keeping only the needed columns
    df = pd.merge(
        df,
        faculty_info[['pid', 'Area', 'Management', 'Position','Excellence',
                      'Top_10_Excellence'
                      ]],
        left_on='author_pid',
        right_on='pid',
        how='left'
    )
    df = df.rename(columns={
        'Area': 'author_area',
        'Management': 'author_management',
        'Position': 'author_position',
        'Excellence': 'author_excellence',
        'Top_10_Excellence': 'author_top_excellence'
    })
    # Drop the redundant pid column from the merge
    df = df.drop(columns=['pid'])


    df = pd.merge(
        df,
        faculty_info[['pid', 'Area', 'Management', 'Position']],
        left_on='collaborator_pid',
        right_on='pid',
        how='left'
    )
    
    df = df.rename(columns={
        'Area': 'collaborator_area',
        'Management': 'collaborator_management',
        'Position': 'collaborator_position',
    })
    # Drop the redundant pid column from the second merge
    df = df.drop(columns=['pid'])
    years = sorted(df['year'].unique())

    # initialize networks, networks for each year
    networks = {}

    # construct accumelative network
    for year in years:

        year_df = df[df['year'] <= year]

        # 创建新的图以存储累积数据
        year_graph = nx.Graph()

        # count the collaboration between authors
        collaboration_counts = defaultdict(int)

        # add nodes and edges
        for _, row in year_df.iterrows():
            author1 = row['author_pid']
            author2 = row['collaborator_pid']

            # add nodes(if not exists)
            if not year_graph.has_node(author1):
                year_graph.add_node(author1, name=row['author_name'], area=row['author_area'], management=row['author_management'], position = row['author_position'],
                                    excellence=row['author_excellence'],
                                    top_10_excellence=row['author_top_excellence']
                                    )
            if not year_graph.has_node(author2):
                year_graph.add_node(author2, name=row['collaborator_name'], area=row['collaborator_area'], management=row['collaborator_management'], position = row['collaborator_position'])

            # update colab count

            if author1 == author2:
                continue
            else:
                collab_pair = tuple(sorted([author1, author2]))
                collaboration_counts[collab_pair] += 0.5
                year_graph.add_edge(author1, author2, weight=collaboration_counts[collab_pair])
            # add edge (no self edge)



        networks[year] = year_graph

    return networks

# Print basic statistics of the collaboration network for each year (nodes, edges, most frequent collaboration).
def print_network_info(networks):
    for year, graph in sorted(networks.items()):
        print(f"\nyear: {year} ")
        print(f"  number of nodes: {graph.number_of_nodes()}")
        print(f"  number of edges: {graph.number_of_edges()}")

        # find the most weighted edge
        if graph.number_of_edges() > 0:
            max_weight_edge = max(graph.edges(data=True), key=lambda x: x[2]['weight'])
            author1, author2 = max_weight_edge[0], max_weight_edge[1]
            weight = max_weight_edge[2]['weight']


            author1_name = graph.nodes[author1].get('name', author1)
            author2_name = graph.nodes[author2].get('name', author2)

            print(f"  the most frequent colaboration(cumulative): {author1_name} and {author2_name} (for {weight} times)")

# Visualise a collaboration network with node size, color coding, and annotations based on centrality and excellence.
def visualize_network(graph, title="Collaboration network"):
    plt.figure(figsize=(12, 10))

    # separate connected nodes and isolated nodes
    connected_nodes = [n for n in graph.nodes() if graph.degree(n) > 0]
    isolated_nodes = [n for n in graph.nodes() if graph.degree(n) == 0]

    # spring layout for connected nodes
    pos = {}
    if connected_nodes:
        connected_graph = graph.subgraph(connected_nodes)
        connected_pos = nx.spring_layout(connected_graph, seed=42)
        pos.update(connected_pos)

    # clusterd layout for isolated nodes(right corner)
    if isolated_nodes:
        # initialize the position of isolated zone
        if connected_nodes:
            max_x = max(p[0] for p in pos.values()) + 0.2
            min_y = min(p[1] for p in pos.values()) - 0.2
        else:
            max_x, min_y = 0, 0

        # calculate the size of web
        n_isolated = len(isolated_nodes)
        cols = max(1, min(int(np.sqrt(n_isolated)), 10))  # at most 10 col
        rows = (n_isolated + cols - 1) // cols

        # place isolated nodes
        for i, node in enumerate(isolated_nodes):
            row, col = i // cols, i % cols
            pos[node] = (max_x + col * 0.1, min_y - row * 0.1)

    # weight -> edge width
    edge_weights = [graph[u][v]['weight'] * 0.03 + 0.3 for u, v in graph.edges()]

    # degree
    degrees = dict(graph.degree())
    max_degree = max(degrees.values()) if degrees else 1

    # Degree Centrality
    degree_centrality = nx.degree_centrality(graph)

    # Betweenness Centrality
    betweenness_centrality = nx.betweenness_centrality(graph)

    # Store top 10% central nodes
    N = int(0.10 * len(degree_centrality))
    top_degree_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:N]
    top_betweenness_nodes = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:N]
    central_degree_nodes = set([pid for pid, _ in top_degree_nodes]) | set([pid for pid, _ in top_betweenness_nodes])
    
    # Printing average centrality measures
    avg_deg_cent_all = avg_metric(degree_centrality, graph.nodes)
    avg_deg_cent_central = avg_metric(degree_centrality, central_degree_nodes)
    print(avg_deg_cent_all, avg_deg_cent_central)

    avg_bet_cent_all = avg_metric(betweenness_centrality, graph.nodes)
    avg_bet_cent_central = avg_metric(betweenness_centrality, central_degree_nodes)
    print(avg_bet_cent_all, avg_bet_cent_central)
   

    # node size and color
    node_sizes = []
    node_colors = []
    for node in graph.nodes():
        degree = degrees.get(node, 0)
        node_sizes.append(5 * degree + 5)
        
        is_excellent = bool(graph.nodes[node].get('excellence', False))
        is_central = node in central_degree_nodes
        is_isolated = node in isolated_nodes
        
        if is_excellent and is_central:
            node_colors.append('orange')  # highlight nodes identified as both central and excellence
        elif is_excellent:
            node_colors.append('yellow')  # excellent nodes
        elif is_central:
            node_colors.append('red')  # central node
        elif is_isolated:
            node_colors.append('grey')  # color for isolated nodes
        else:
        # blue scale for others
          node_colors.append(plt.cm.Blues(degrees[node] * 0.5 / max_degree + 0.5))
          
    # --- Calculating overlap stats ---
    excellent_nodes = {node for node in graph.nodes() if graph.nodes[node].get('excellence', False)}

    num_excellent = len(excellent_nodes)
    num_central = len(central_degree_nodes)
    num_overlap = len(excellent_nodes & central_degree_nodes)

    pct_excellent_are_central = (num_overlap / num_excellent * 100) if num_excellent else 0
    pct_central_are_excellent = (num_overlap / num_central * 100) if num_central else 0

    print(f"Number of excellent nodes: {num_excellent}")
    print(f"Number of central nodes: {num_central}")
    print(f"Number of nodes that are both: {num_overlap}")
    print(f"Percentage of excellent nodes that are central: {pct_excellent_are_central:.2f}%")
    print(f"Percentage of central nodes that are excellent: {pct_central_are_excellent:.2f}%")
        
    # draw nodes
    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)

    # draw edges
    if graph.edges():
        nx.draw_networkx_edges(graph, pos, width=edge_weights, alpha=0.6, edge_color='gray')

    # annotate isolated nodes
    if isolated_nodes:
        plt.annotate(f" ({len(isolated_nodes)} isolated nodes)",
                     xy=(max_x, min_y),
                     xytext=(max_x, min_y - rows * 0.1 - 0.2),
                     ha='center', va='top',
                     bbox=dict(boxstyle="round,pad=0.3", fc="lightgray", alpha=0.8))

   #annotate excellent nodes 
    for node in graph.nodes():
        if graph.nodes[node].get('excellence', False):  # check if node is excellent
            name = graph.nodes[node].get('name', node)
            plt.annotate(name, xy=pos[node], textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, color='black')
    
    
   #annotate the top 5 nodes
    for i, (node, degree) in enumerate(central_degree_nodes):
        name = graph.nodes[node].get('name', node)
        plt.annotate(f"{i + 1}. {name} (degree: {degree})",
                     xy=pos[node], xytext=(50 + np.random.randint(-10, 10), 50 + i * 30 + np.random.randint(-10, 10)),
                     textcoords="offset points",
                     bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8),
                     arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"))

    plt.title(title)
    plt.axis('off')
    plt.tight_layout()

    #
    plt.gcf().canvas.toolbar_visible = True
    plt.gcf().canvas.header_visible = False
    plt.gcf().canvas.footer_visible = False

    #
    plt.figtext(0.5, 0.01, "click the tools to zoom in",
                ha="center", fontsize=12, bbox={"facecolor": "lightgray", "alpha": 0.5})

    plt.show()

def visualize_year_network(networks, year):
    if year not in networks:
        print(f"no network data of {year}")
        return

    graph = networks[year]


    visualize_network(graph, title=f"{year} collaboration network")



if __name__ == "__main__":
    networks = build_collaboration_networks('main_authors_collaborations.csv')
    print_network_info(networks)
    visualize_year_network(networks, 2025)
