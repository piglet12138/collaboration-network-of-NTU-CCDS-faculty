import pandas as pd
import csv
import requests
import time
import argparse
import re
import xml.etree.ElementTree as ET
import json
import os
import csv
import pandas as pd
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import re
#---------------------------------------------------------begin of data preparation-------------------------------------------#

def download_dblp_xml(xlsx_file, output_dir="faculty_data"):
    """
    Description:
      - Downloads XML versions of DBLP profiles for each faculty member.
      - Extracts and saves the unique DBLP person ID (pid).
      - Saves the raw XML for further parsing.

    Time Complexity:
      - Reading CSV: O(N)
      - For each faculty:
          - HTTP request: O(1) I/O-bound
          - XML parsing: O(M) where M = size of XML
      - Overall: O(N * M), where N = number of faculty
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    df = pd.read_csv(xlsx_file)
    
    for idx, row in df.iterrows():
        dblp_url = row["DBLP"]
        name = row["Faculty"]
        dblp_url = requests.get(dblp_url).url # some url don't have the .html, so request the url to get the final url

        # Build XML URL (convert HTML page URL to XML API URL)
        xml_url = dblp_url.replace(".html",".xml")
        # Use faculty name for filename (replace spaces with underscores)
        safe_name = str(name).replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_file = os.path.join(output_dir, f"{safe_name}.xml")
        
        
        if os.path.exists(output_file):
            #print(f"skipping {name}: {output_file} already exists")
            continue
        try:
            print(f"Downloading XML data for {name}: {xml_url}")
            response = requests.get(xml_url)
            response.raise_for_status()  # Check if request was successful
            
            pid = None
            root = ET.fromstring(response.text)
            
            for person in root.findall(".//person"):
                author = person.find("author")
                if author is not None:
                    pid = author.get("pid")
                    break

            df.at[idx, 'pid'] = pid
            print(f"{name} : {pid}")    
            
            # Save XML file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            print(f"Successfully saved to: {output_file}")

            # Add delay to avoid too many requests
            time.sleep(1)
            
        except Exception as e:
            print(f"Failed to download XML data for {name}: {e}")

        df.to_csv(xlsx_file, index=False)

    print(f"All XML files downloaded to {output_dir}")


def add_pid_to_faculty_csv(input_csv, output_csv=None):
    """
    Description:
      - Extracts DBLP pid for each professor from their DBLP page.
      - Updates and saves to CSV with new pid column.

    Time Complexity:
      - O(N * M), same as above (one HTTP + XML parse per faculty)
    """
    if output_csv is None:
        output_csv = input_csv
    df = pd.read_csv(input_csv)
    df['pid'] = None

    for idx, row in df.iterrows():
        dblp_url = row["DBLP"]
        name = row["Faculty"]

        dblp_url = requests.get(dblp_url).url # some url don't have the .html, so request the url to get the final url
        xml_url = dblp_url.replace(".html", ".xml") 

        try:

            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.text)

            pid = None
            for person in root.findall(".//person"):
                author = person.find("author")
                if author is not None:
                    pid = author.get("pid")
                    break

            df.at[idx, 'pid'] = pid
            print(f"{name} : {pid}")
            time.sleep(0.05)

        except Exception as e:
            print(f"{name} : {e}")
    df.to_csv(output_csv, index=False)


def parse_collaborations(xml_file):
    """
    Description:
      - Parses an XML file and returns the main author's pid and name.
      - Gathers all co-authorships year by year.

    Time Complexity:
      - XML parsing: O(M) where M = size of XML tree
      - Iterating publications: O(P * A), where P = number of papers, A = authors/paper
      - Overall: O(P * A)
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    main_author = None
    for person in root.findall(".//person"):
        author = person.find("author")
        if author is not None:
            main_author = {
                "pid": author.get("pid"),
                "name": author.text
            }
            break

    # collect collaborator by year
    collaborations_by_year = defaultdict(list)

    # for all article and inproceedings
    for r in root.findall("./r"):
        publication = None
        for child in r:
            if child.tag in ["article", "inproceedings"]:
                publication = child
                break

        if publication is None:
            continue

        # get year
        year_elem = publication.find("year")
        if year_elem is None:
            continue

        year = year_elem.text

        # check if the main author in the list
        has_main_author = False
        for author in publication.findall("author"):
            if author.get("pid") == main_author["pid"]:
                has_main_author = True
                break

        if has_main_author:
            # collect all collaborators（including the mainauthor）
            for author in publication.findall("author"):
                pid = author.get("pid")
                name = author.text

                collaborations_by_year[year].append({
                    "pid": pid,
                    "name": name
                })

    result = {
        "author": main_author,
        "collaborations_by_year": dict(collaborations_by_year)
    }

    return result


def generate_raw_data():
    """
    Description:
      - Iterates over all XML files and extracts author/collaboration data.
      - Writes two JSON files: all_collaborations.json and main_authors.json.

    Time Complexity:
      - O(F * P * A), where F = number of XML files
    """
    directory = r"faculty_data"
    all_collaborations = {}
    main_authors = []

    # iterate all xml files
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            xml_file = os.path.join(directory, filename)
            print(f"processing file: {filename}")

            result = parse_collaborations(xml_file)

            # collect NTU faculty pid for filtering
            if result["author"]:
                all_collaborations[result["author"]["pid"]] = result

                main_authors.append({
                    "pid": result["author"]["pid"],
                    "name": result["author"]["name"]
                })

    with open("all_collaborations.json", "w", encoding="utf-8") as f:
        json.dump(all_collaborations, f, indent=2, ensure_ascii=False)

    with open("main_authors.json", "w", encoding="utf-8") as f:
        json.dump(main_authors, f, indent=2, ensure_ascii=False)

    print("data saved in all_collaborations.json and main_authors.json")


def generate_network_links():
    """
    Description:
      - Loads collaboration JSONs and writes all internal CCDS faculty collaborations to a CSV.

    Time Complexity:
      - O(N * Y * C), where N = number of authors, Y = number of years, C = collaborations per year
    """
    # read the CCDS faculties list
    with open('main_authors.json', 'r', encoding='utf-8') as f:
        main_authors = json.load(f)

    # CCDS faculty pid set
    main_author_pids = {author['pid'] for author in main_authors}

    # read all collaborators
    with open('all_collaborations.json', 'r', encoding='utf-8') as f:
        all_collaborations = json.load(f)

    # write in network links
    with open('main_authors_collaborations.csv', 'w', encoding='utf-8', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        csv_writer.writerow(['colab_id', 'author_pid', 'author_name', 'year', 'collaborator_pid', 'collaborator_name'])

        count = 0
        for author_pid, author_data in all_collaborations.items():
            # for every CCDS faculty
            if author_pid in main_author_pids:
                author_name = author_data['author']['name']

                # for each year
                for year, collaborators in author_data['collaborations_by_year'].items():
                    # filter the CCDS faculty
                    main_collaborators = [collab for collab in collaborators if collab['pid'] in main_author_pids]

                    # write in the info
                    for collaborator in main_collaborators:
                        count += 1
                        csv_writer.writerow([
                            count,
                            author_pid,
                            author_name,
                            year,
                            collaborator['pid'],
                            collaborator['name']
                        ])

    print("finished in main_authors_collaborations.csv ")

#---------------------------------------------------------end of data preparation-------------------------------------------#

#---------------------------------------------------------begin of network visualization-------------------------------------------#
def build_collaboration_networks(main_authors_collaborations_csv='main_authors_collaborations.csv',
                                 faculty_csv='Faculty.csv'):
    """
    Description:
      - Builds a yearly collaboration network.
      - Nodes = faculty, Edges = collaborations up to that year.
      - Saves each year's network as GraphML.

    Time Complexity:
      - O(T * R), where T = years, R = rows in CSV (collaboration records)
    """
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

        # graph for each year
        year_graph = nx.Graph()

        # count the collaboration between authors
        collaboration_counts = defaultdict(int)

        # add nodes and edges
        for _, row in year_df.iterrows():
            author1 = row['author_pid']
            author2 = row['collaborator_pid']

            # add nodes(if not exists)
            if not year_graph.has_node(author1):
                year_graph.add_node(author1, name=row['author_name'], area=row['author_area'],
                                    management=row['author_management'], position=row['author_position'])
            if not year_graph.has_node(author2):
                year_graph.add_node(author2, name=row['collaborator_name'], area=row['collaborator_area'],
                                    management=row['collaborator_management'], position=row['collaborator_position'])

            # update colab count

            if author1 == author2:
                continue
            else:
                collab_pair = tuple(sorted([author1, author2]))
                collaboration_counts[collab_pair] += 0.5
                year_graph.add_edge(author1, author2, weight=collaboration_counts[collab_pair])
            # add edge (no self edge)

        output_file = f"graphs/collaboration_network_{year}.graphml"
        if not os.path.exists(output_file):
            nx.write_graphml(year_graph, output_file)
        networks[year] = year_graph

    return networks

def print_network_info(networks):
    """
    Description:
      - Prints node/edge counts and heaviest edge for each network.

    Time Complexity:
      - O(Y * E), where Y = number of years, E = edges per year
    """
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
    """
    Description:
      - Analyzes centrality (top 5 by degree) for a specific year.

    Time Complexity:
      - Degree Centrality: O(V + E)
      - Sorting: O(V log V)
      - Overall: O(V log V)
    """
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
    """
    Description:
      - Visualizes the graph using spring layout for connected and grid layout for isolated nodes.

    Time Complexity:
      - Spring layout: O(V^2)
      - Drawing: O(V + E)
      - Overall: O(V^2)
    """
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
    """
    Description:
      - Wrapper to visualize a single year from pre-built networks.

    Time Complexity:
      - Same as visualize_network → O(V^2)
    """
    if year not in networks:
        print(f"no network data of {year}")
        return

    graph = networks[year]
    visualize_network(graph, title=f"{year} collaboration network")

def create_network_dashboard(networks):
    """
    Description:
      - Jupyter-based dashboard for navigating network visualizations year by year.

    Time Complexity:
      - Setup: O(1)
      - Each update: O(V^2) (uses visualize_network)
    """
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


def visualize_years_network_grid(networks, start_year=2000, end_year=2025):
    """
    Description:
      - Plots grid of networks over time.

    Time Complexity:
      - Per graph: O(V^2)
      - Total: O(Y * V^2), where Y = number of years
    """
    years = [year for year in range(start_year, end_year + 1) if year in networks]

    if not years:
        print(f"No network data available between {start_year} and {end_year}")
        return

    # Calculate appropriate grid layout
    n_years = len(years)
    cols = int(np.ceil(np.sqrt(n_years)))
    rows = int(np.ceil(n_years / cols))

    # Create figure with appropriate size
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
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
    plt.savefig(f"Network Evolution from {start_year} to {end_year}.png", dpi=300, bbox_inches='tight')

    plt.show()
#---------------------------------------------------------end of network visualization-------------------------------------------#
def extract_paper_data(xml_file_path):
    """
    Description:
      - Parses XML to extract paper metadata into a dictionary.

    Time Complexity:
      - O(P * A), P = papers, A = authors per paper
    """
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    papers = {}
    
    for record in root.findall('.//r/*'):  # <article>, <inproceedings>, etc.
        key = record.attrib.get("key")
        title_elem = record.find("title")
        year_elem = record.find("year")
        authors = record.findall("author")

        if not key or title_elem is None or year_elem is None or not authors:
            continue

        papers[key] = {
            "title": title_elem.text.strip() if title_elem.text else "",
            "year": year_elem.text.strip() if year_elem.text else "",
            "authors": [
                {
                    "pid": a.attrib.get("pid", ""),
                    "name": a.text.strip() if a.text else ""
                } for a in authors
            ]
        }

    return papers    

#---------------------------------------------------------preprocessing for section 3 Excellence nodes-------------------------------------------#
fields_dict = {
        "Artificial intelligence": "ai",
        "Computer vision": "vision",
        "Machine learning & data mining": "mlmining",
        "Natural language processing": "nlp",
        "Computer architecture": "arch",
        "Computer networks": "comm",
        "Computer security": "sec",
        "Databases": "mod",
        "Design automation": "da",
        "Embedded & real-time systems": "bed",
        "High-performance computing": "hpc",
        "Mobile computing": "mobile",
        "Measurement & perf. analysis": "metrics",
        "Operating systems": "ops",
        "Programming languages": "plan",
        "Software engineering": "soft",
        "Algorithms & complexity": "act",
        "Cryptography": "crypt",
        "Logic & verification": "log",
        "Comp. bio & bioinformatics": "bio",
        "Computer graphics": "graph",
        "Computer science education": "csed",
        "Economics & computation": "ecom",
        "Human-computer interaction": "chi",
        "Robotics": "robotics",
        "Visualization": "visualization"
        }
def clean_text(text):
    return re.sub(r"[^a-zA-Z ]+", "", text).strip()

# Remove all non-numeric characters from a string
def clean_number(num_text):
    return re.sub(r"[^0-9]+", "", num_text).strip()


def save_universities_to_csv(filename, universities):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "University Name",
                "Professor Name",
                "Home Page",
                "Google Scholar",
                "DBLP Link",
            ]
        )
        for university in universities:
            for professor in university.get("professors", []):
                writer.writerow(
                    [
                        university.get("name", ""),
                        professor.get("name", ""),
                        professor.get("home_page", ""),
                        professor.get("google_scholar", ""),
                        professor.get("dblp", ""),
                    ]
                )
# Extract list of professor data from a given university section
def parse_professors(tbody):
    professors = []
    prof_trs = tbody.find_all("tr", recursive=False)
    # Professors' info are stored in another tr list
    for prof_tr in prof_trs:
        professor_info = parse_professor_info(prof_tr)
        if professor_info:
            professors.append(professor_info)
    return professors

# Extract 3 relevant links (Home page, DBLP, Google Scholar) for a professor
def parse_professor_info(prof_tr):
    tds = prof_tr.find_all("td")
    if not tds:
        return None
    professor = {}
    for j, td in enumerate(tds):
        if j % 4 == 1:
            homepage = td.find("a", title="Click for author's home page.")
            if homepage:
                professor["name"] = clean_text(homepage.text)
                professor["home_page"] = homepage["href"]
            google_scholar = td.find(
                "a", title="Click for author's Google Scholar page."
                )
            if google_scholar:
                professor["google_scholar"] = google_scholar["href"]
            dblp_link = td.find("a", title="Click for author's DBLP entry.")
            if dblp_link:
                professor["dblp"] = dblp_link["href"]
        return professor

# Navigate to CSRankings, select a region, and extract university and professor info. The most complicated part...
def fetch_universities(url,region):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)

    button1 = driver.find_element(By.XPATH,'//select[@id="regions"]')
    action = ActionChains(driver)
    action.click(button1).perform()
    button2 = driver.find_element(By.XPATH,region).click()


    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    universities = []
    table = soup.find("table", id="ranking")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr", recursive=False)

    for i, tr in enumerate(trs):
        if i % 3 == 0:
            # Parse university info
            university_info = parse_university_info(tr)
        if i % 3 == 2 and university_info:
            # Parse professors
            university_info["professors"] = parse_professors(tr.find("tbody"))
            universities.append(university_info)
    return universities

# Extract rank and name of a university from the page
def parse_university_info(tr):
    tds = tr.find_all("td")
    if not tds:
        return None
    university_info = {}
    for j, td in enumerate(tds):
        if j % 4 == 0:
            university_info["rank"] = clean_number(td.text)
        if j % 4 == 1:
            university_info["name"] = clean_text(td.text)
    return university_info

# Command-line argument parser to configure the scraping parameters
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Fetch universities and professors data from CSRankings."
    )

    all_fields = ",".join(fields_dict.values())

    parser.add_argument(
        "--fields",
        type=str,
        default=all_fields,
        help='Code of relevant fields, using "," to split multiple fields (e.g., "sec,ai" for Security and Artificial Intelligence)',
    )
    parser.add_argument(
        "--start_year", type=int, default=2016, help="Start year (default 2016)"
    )
    parser.add_argument(
        "--end_year", type=int, default=time.localtime().tm_year, help="End year (default 2025)"
    )

    args = parser.parse_args()

    if args.start_year > args.end_year or args.end_year > time.localtime().tm_year:
        parser.error("Invalid year range.")

    if not all(field in set(fields_dict.values()) for field in args.fields.split(",")):
        parser.error("Invalid field code.")

    return (
        args.fields.replace(" ", "").replace(",", "&"),
        args.start_year,
        args.end_year,
    )
def csrankings_scrape():
    """
    Description:
      - Uses Selenium to scrape CSRankings.org for faculty + publication data.

    Time Complexity:
      - DOM parsing: O(U * P), U = universities, P = professors/univ
      - Request overhead dominates
    """

   # XPath values for selecting Asia in the CSRankings dropdown menu
    ranking_asia ='//*[@id="regions"]/optgroup[2]/option[4]'

   # Remove all non-alphabetic characters from a string

    from_year = 2016
    to_year = 2025
    url = f"https://csrankings.org/#/fromyear/{from_year}/toyear/{to_year}/&world"
    print(f"Your URL: {url}")

    universities = fetch_universities(url,ranking_asia)
    filename = f'CSRankings_Scrapped_{from_year}-{to_year}.csv'
    save_universities_to_csv(filename, universities)
    print(f"Data has been saved to {filename}")
    df = pd.read_csv(filename)
    return df


def add_excellence_to_faculty_csv(df, input_csv, output_csv):
    """
    Description:
      - Adds "Excellence" flag to Faculty.csv based on CSRankings data.

    Time Complexity:
      - Matching and merging: O(N)
      - PID fetching (HTTP + XML): O(N * M)
    """
    # Create an empty DataFrame to store NTU-specific professor data across all fields
    columns = ["Subject Area", "University Name", "University Rank for Subject Area", "Professor Name", "DBLP Link"]
    combined_df = pd.DataFrame(columns=columns)

    university_column = "University Name"
    index_column = "University Rank for Subject Area"
    
    # Filter only faculty from NTU. Designate all these faculty as "Excellence" nodes
    df_subset = df[['University Name','Professor Name', 'DBLP Link']]
    df_subset['University Name'] = df_subset['University Name'].str.strip().str.lower()
    ntu_df = df_subset[df_subset['University Name'] == 'nanyang technological university']
    ntu_df["Excellence"] = True


    # Function to extract the unique DBLP person ID (pid) for each professor. Uses the XML version of the DBLP page to parse the PID. 
    # Also used for cleaning Faculty.csv
    def add_pid_to_df(df):

        df['pid'] = None

        for idx, row in df.iterrows():
            dblp_url = row["DBLP Link"]
            name = row["Professor Name"]

            dblp_url = requests.get(dblp_url).url # some url don't have the .html, so request the url to get the final url
            xml_url = dblp_url.replace(".html", ".xml") 

            try:

                response = requests.get(xml_url)
                response.raise_for_status()

                root = ET.fromstring(response.text)

                pid = None
                for person in root.findall(".//person"):
                    author = person.find("author")
                    if author is not None:
                        pid = author.get("pid")
                        break

                df.at[idx, 'pid'] = str(pid)
                print(f"{name} : {pid}")
                time.sleep(0.05)

            except Exception as e:
                print(f"{name} : {e}")
        return df
    
    ntu_df = add_pid_to_df(ntu_df)

    # Merge the aggregated NTU excellence data with the master faculty list using PID. Drop redundant columns and save the enriched faculty file
    df_faculty = pd.read_csv(input_csv)  
    merged_df = df_faculty.merge(
        ntu_df, 
        left_on=['pid'], 
        right_on=['pid'],
        how='left')
    merged_df = merged_df.drop(columns=['DBLP Link','Professor Name'])
    merged_df.to_csv(output_csv, index=False)

# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 21:36:57 2025

@author: Choo
"""


def process_faculty_folder(folder_path, output_path):
    """
    Description:
      - Loops over XML files, parses and merges their paper data.

    Time Complexity:
      - O(F * P * A), where F = files, P = papers/file
    """
    papers_by_key = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".xml"):
            xml_path = os.path.join(folder_path, filename)
            papers_by_key.update(extract_paper_data(xml_path))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers_by_key, f, indent=2, ensure_ascii=False)

    print(f" Extracted paper data saved to: {output_path}")

def deduplicate_paper_data(input_path, output_path):
    """
    Description:
      - Removes duplicate authors (based on pid) in each paper.

    Time Complexity:
      - O(P * A), where P = papers, A = authors per paper
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = {}

    for key, paper in data.items():
        seen_pids = set()
        unique_authors = []

        for author in paper.get("authors", []):
            pid = author.get("pid")
            if pid and pid not in seen_pids:
                seen_pids.add(pid)
                unique_authors.append(author)

        cleaned_data[key] = {
            "title": paper.get("title", ""),
            "year": paper.get("year", ""),
            "authors": unique_authors
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f" Cleaned JSON saved to: {output_path}")

if __name__ == "__main__":
    # Usage example
    file = "Faculty.csv"
    download_dblp_xml(file) 
    add_pid_to_faculty_csv(file)
    add_pid_to_faculty_csv(file)
    df = csrankings_scrape()
    add_excellence_to_faculty_csv(df, file,"Faculty_with_excellence.csv")
