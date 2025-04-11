import pandas as pd
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt

# 读取CSV数据
def build_collaboration_networks(csv_file):

    df = pd.read_csv(csv_file)

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
                year_graph.add_node(author1, name=row['author_name'])
            if not year_graph.has_node(author2):
                year_graph.add_node(author2, name=row['collaborator_name'])

            # update colab count
            collab_pair = tuple(sorted([author1, author2]))
            collaboration_counts[collab_pair] += 0.5

            # add edge
            year_graph.add_edge(author1, author2, weight=collaboration_counts[collab_pair])


        networks[year] = year_graph

    return networks



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


def analyze_specific_year(networks, year):
    if year not in networks:
        print(f"no network of {year} ")
        return

    graph = networks[year]

    # centrality
    degree_centrality = nx.degree_centrality(graph)
    top_authors = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]

    print(f"\n{year} the most influenced falcuty:")
    for author_id, centrality in top_authors:
        author_name = graph.nodes[author_id].get('name', author_id)
        print(f"  {author_name}: {centrality:.4f}")


def visualize_network(graph, title="Collaboration network"):
    plt.figure(figsize=(12, 10))

    # spring layout
    pos = nx.spring_layout(graph, seed=42)

    # weight -> edge width
    edge_weights = [graph[u][v]['weight'] * 0.2 for u, v in graph.edges()]

    # degree -> node size
    node_sizes = [20 * nx.degree(graph, node) for node in graph.nodes()]

    # degree -> node color (higher degree, darker color)
    degrees = dict(graph.degree())
    max_degree = max(degrees.values()) if degrees else 1
    node_colors = [plt.cm.Blues(degrees[node]*0.5 / max_degree + 0.5) for node in graph.nodes()]

    # draw network
    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)
    nx.draw_networkx_edges(graph, pos, width=edge_weights, alpha=0.8, edge_color='gray')

    # label
    if len(graph) < 50:
        labels = {node: graph.nodes[node].get('name', node) for node in graph.nodes()}
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8)

    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def visualize_year_network(networks, year):
    if year not in networks:
        print(f"no network data of {year}")
        return

    graph = networks[year]
    visualize_network(graph, title=f"{year} collaboration network")


def visualize_network_evolution(networks, years=None):
    """可视化网络随时间的演化"""
    if years is None:
        years = sorted(networks.keys())

    fig, axes = plt.subplots(len(years), 1, figsize=(12, 5 * len(years)))
    if len(years) == 1:
        axes = [axes]

    # 计算所有年份的全局中心性范围，保持视觉一致性
    all_degrees = []
    for year in years:
        graph = networks[year]
        all_degrees.extend([d for _, d in graph.degree()])

    max_degree = max(all_degrees) if all_degrees else 1

    # 使用相同的布局方案
    combined_graph = nx.Graph()
    for year in years:
        combined_graph = nx.compose(combined_graph, networks[year])

    pos = nx.spring_layout(combined_graph, seed=42)

    for i, year in enumerate(years):
        graph = networks[year]
        ax = axes[i]

        # 节点大小按度数设置
        node_sizes = [50 * (graph.degree(node) / max_degree) + 50 for node in graph.nodes()]

        # degree -> node color (higher degree, darker color)
        degrees = dict(graph.degree())
        max_degree = max(degrees.values()) if degrees else 1
        node_colors = [plt.cm.Blues(degrees[node] * 0.5 / max_degree + 0.5) for node in graph.nodes()]

        # 可视化
        nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)

        # 边宽度按权重设置
        edge_widths = [graph[u][v]['weight'] * 0.05 for u, v in graph.edges()]
        nx.draw_networkx_edges(graph, pos, ax=ax, width=edge_widths,
                               alpha=0.8, edge_color='gray')

        # 仅为较大节点添加标签
        if len(graph) < 200:
            labels = {node: graph.nodes[node].get('name', node)
                      for node in graph.nodes() if graph.degree(node) > max_degree / 3}
            nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=8)

        ax.set_title(f"{year} (nodes: {graph.number_of_nodes()}, edges: {graph.number_of_edges()})")
        ax.axis('off')

    plt.tight_layout()
    plt.show()

networks = build_collaboration_networks('main_authors_collaborations.csv')
#print_network_info(networks)
#analyze_specific_year(networks, 2020)
#visualize_year_network(networks, 2000)
visualize_network_evolution(networks, [2009, 2010, 2011])