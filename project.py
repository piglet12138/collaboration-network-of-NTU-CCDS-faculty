from preprocessing import *
from parse_faculty import  *
from faculty import *

# Only run this if you want to download the XML file from DBLP
# file = "Faculty.csv"
# download_dblp_xml(file)
# add_pid_to_faculty_csv("Faculty.csv")
# generate_raw_data()
# generate_network_links()

#1000 preprocessing:
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
