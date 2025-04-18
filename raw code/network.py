import pandas as pd
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# 读取CSV数据
def build_collaboration_networks(main_authors_collaborations_csv = 'main_authors_collaborations.csv', faculty_csv = 'Faculty.csv'):

    df = pd.read_csv(main_authors_collaborations_csv)
    faculty_info = pd.read_csv(faculty_csv)
    
    # Merge faculty information with collaboration data

    # Merge on author_pid = pid, keeping only the needed columns
    df = pd.merge(
        df,
        faculty_info[['pid', 'Area', 'Management', 'Position']],
        left_on='author_pid',
        right_on='pid',
        how='left'
    )
    df = df.rename(columns={
        'Area': 'author_area',
        'Management': 'author_management',
        'Position': 'author_position'
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
        'Position': 'collaborator_position'
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
                year_graph.add_node(author1, name=row['author_name'], area=row['author_area'], management=row['author_management'], position = row['author_position'])
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

        nx.write_graphml(year_graph, f"graphs/collaboration_network_{year}.graphml")
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

    # 5 top degree
    top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
    top_node_ids = [node for node, _ in top_nodes]

    # node size and color
    node_sizes = []
    node_colors = []
    for node in graph.nodes():
        if node in top_node_ids:
            # make the top 5 nodes bigger
            node_sizes.append(5 * degrees[node] + 5)
            node_colors.append('red')
        else:
            # other nodes
            node_sizes.append(5 * degrees[node] + 5)
            if node in isolated_nodes:
                # grey for isolated nodes
                node_colors.append('grey')
            else:
                node_colors.append(plt.cm.Blues(degrees[node] * 0.5 / max_degree + 0.5))

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

    # annotate the top 5 nodes
    for i, (node, degree) in enumerate(top_nodes):
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


def create_network_dashboard(networks):# for code run on notebook
    """create a dashboaed to show the evolution of the network"""
    import ipywidgets as widgets
    from IPython.display import display, clear_output

    # get all availiable years
    years = sorted(networks.keys())

    # year slider
    year_slider = widgets.SelectionSlider(
        options=years,
        value=years[-1],  # default the latest year
        description='year:',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True
    )

    # info output area
    info_output = widgets.Output()

    # graph output area
    graph_output = widgets.Output()

    # the overall layout
    dashboard = widgets.VBox([
        graph_output,
        widgets.HBox([year_slider]),
        info_output
    ])

    # define update function
    def update_dashboard(year):
        # clear the output area
        with info_output:
            clear_output(wait=True)
            # network info
            graph = networks[year]
            print(f"year: {year}")
            print(f"number of nodes: {graph.number_of_nodes()}")
            print(f"edges: {graph.number_of_edges()}")

            # node with largest degree
            if graph.number_of_nodes() > 0:
                degrees = dict(graph.degree())
                top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]

                print("\nnode with largest degree:")
                for i, (node, degree) in enumerate(top_nodes):
                    name = graph.nodes[node].get('name', node)
                    print(f"  {i + 1}. {name}: {degree}")

                # the most weighted edge
                if graph.number_of_edges() > 0:
                    max_weight_edge = max(graph.edges(data=True), key=lambda x: x[2]['weight'])
                    author1, author2 = max_weight_edge[0], max_weight_edge[1]
                    weight = max_weight_edge[2]['weight']

                    author1_name = graph.nodes[author1].get('name', author1)
                    author2_name = graph.nodes[author2].get('name', author2)

                    print(
                        f"\nthe most frequently collaborated authors: {author1_name} and {author2_name} (for {weight} times)")

        # the graph
        with graph_output:
            clear_output(wait=True)
            visualize_network(graph, title=f"collaboration network of {year}")

    # connect the update function and slider
    year_slider.observe(lambda change: update_dashboard(change['new']), names='value')

    # initial output
    update_dashboard(year_slider.value)

    return dashboard

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

def visualize_years_network_grid(networks, start_year=2000, end_year=2025, save_path=None):
    """Visualize network evolution across multiple years using a grid layout"""
    years = [year for year in range(start_year, end_year + 1) if year in networks]
    
    if not years:
        print(f"No network data available between {start_year} and {end_year}")
        return
    
    # Calculate appropriate grid layout
    n_years = len(years)
    cols = int(np.ceil(np.sqrt(n_years)))
    rows = int(np.ceil(n_years / cols))
    
    # Create figure with appropriate size
    fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3*rows))
    axes = axes.flatten() if n_years > 1 else [axes]
    
    for i, year in enumerate(years):
        if i >= len(axes):
            break  # Safety check
            
        graph = networks[year]
        ax = axes[i]
        
        # Separate connected nodes and isolated nodes
        connected_nodes = [n for n in graph.nodes() if graph.degree(n) > 0]
        isolated_nodes = [n for n in graph.nodes() if graph.degree(n) == 0]
        
        # Layout for connected nodes
        pos = {}
        if connected_nodes:
            connected_graph = graph.subgraph(connected_nodes)
            connected_pos = nx.spring_layout(connected_graph, seed=42)
            pos.update(connected_pos)
        
        # Clustered layout for isolated nodes
        if isolated_nodes:
            # Initialize the position of isolated zone
            if connected_nodes:
                max_x = max(p[0] for p in pos.values()) + 0.2
                min_y = min(p[1] for p in pos.values()) - 0.2
            else:
                max_x, min_y = 0, 0
            
            # Calculate the size of grid
            n_isolated = len(isolated_nodes)
            iso_cols = max(1, min(int(np.sqrt(n_isolated)), 10))  # at most 10 columns
            iso_rows = (n_isolated + iso_cols - 1) // iso_cols
            
            # Place isolated nodes
            for j, node in enumerate(isolated_nodes):
                row, col = j // iso_cols, j % iso_cols
                pos[node] = (max_x + col * 0.1, min_y - row * 0.1)
        
        # Degree and node sizing
        degrees = dict(graph.degree())
        max_degree = max(degrees.values()) if degrees else 1
        
        # Find top nodes by degree
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        top_node_ids = [node for node, _ in top_nodes]
        
        # Node size and color
        node_sizes = []
        node_colors = []
        for node in graph.nodes():
            if node in top_node_ids:
                # Make top 5 nodes bigger
                node_sizes.append(2 * degrees[node] + 2)
                node_colors.append('red')
            else:
                node_sizes.append(2 * degrees[node] + 2)
                if node in isolated_nodes:
                    # Grey for isolated nodes
                    node_colors.append('grey')
                else:
                    node_colors.append(plt.cm.Blues(degrees[node] * 0.5 / max_degree + 0.5))
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=node_sizes, 
                               node_color=node_colors, alpha=0.8)
        
        # Draw edges
        if graph.edges():
            edge_weights = [graph[u][v]['weight'] * 0.03 + 0.3 for u, v in graph.edges()]
            nx.draw_networkx_edges(graph, pos, ax=ax, width=edge_weights,
                                   alpha=0.6, edge_color='gray')
        


        

    
    # Hide empty subplots
    for i in range(len(years), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    plt.suptitle(f"Network Evolution from {start_year} to {end_year}", fontsize=16, y=1.02)
    plt.subplots_adjust(top=0.95)
    
    # Save figure
    plt.savefig( f"Network Evolution from {start_year} to {end_year}.png",dpi=300, bbox_inches='tight')
        
    plt.show()

if __name__ == "__main__":
    networks = build_collaboration_networks('main_authors_collaborations.csv')
    #print_network_info(networks)
    #analyze_specific_year(networks, 2020)
    #visualize_year_network(networks, 2025)
    #visualize_network_evolution(networks, [2009, 2010, 2011])
    # visualize_years_network_grid(networks, 2001, 2025)