from preprocessing import *
from sparse_faculty import  *


file = "Faculty.csv"
download_dblp_xml(file)
add_pid_to_faculty_csv("Faculty.csv")
generate_raw_data()
generate_network_links()

