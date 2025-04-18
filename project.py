from preprocessing import *
from faculty import *

# all data preparation,only run this if you want to download the XML file from DBLP
# file = "Faculty.csv"
# download_dblp_xml(file)
# add_pid_to_faculty_csv("Faculty.csv")
# generate_raw_data()
# generate_network_links()

### This should always be run to build the collaboration networks
networks = build_collaboration_networks('main_authors_collaborations.csv')

### Run this to get statistics for Question 2.1
visualize_year_network(networks, 2025)
get_network_statistics(year=2025)
compare_with_random_network(year=2025)

### Run this to get visualization for Question 2.2
visualize_years_network_grid(networks, 2001, 2025)
visualize_statistics_change()

### Run this and change the attribute name to either "position", "management" or "area" to get the visualization for Question 2.3-2.5
analyze_and_visualize_collaboration(year = 2025, attribute_name="position", min_faculty=3)
analyze_and_visualize_collaboration(year = 2025, attribute_name="management", min_faculty=3)
analyze_and_visualize_collaboration(year = 2025, attribute_name="area", min_faculty=3)

### Run this to get visualisation and statistics for Section 3 (central & excellence nodes)
visualize_excellence_central()

### Run this to get new faculty data and analyze for section 4:
folder_path = r"faculty_data" #subsitute with relative path
output_json_path = r"papers_by_key.json" #relative path
input_json = r"papers_by_key.json"
output_json = r"papers_by_key_cleaned.json"

process_faculty_folder(folder_path, output_json_path)
deduplicate_paper_data(input_json, output_json)
page_rank_network()
new_1000_network()
overall_info()
network_degree_plot()
