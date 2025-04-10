from preprocessing import *
from sparse_faculty import  *


file = "Faculty.csv"
download_dblp_xml(file)
sparse_faculty_main()

