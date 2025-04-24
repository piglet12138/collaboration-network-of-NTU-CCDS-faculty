# A Network Science's View on Academic Collaboration at NTU CCDS

*SD6127 Network Science Project - Group 3*

Group members: 
- Le Anh Tuan G2403592D
- Grace Choo Yu Xuan G2403279C
- Yao Yuheng G2405427G
- Nguyen Giang Son G2404606D

Written Report: https://docs.google.com/document/d/11AptFtR-8v5_eyzy_mE80oHM_WLNTiO5I74IVBzTGH4/edit?tab=t.0

PPT: https://entuedu-my.sharepoint.com/:p:/g/personal/c240066_e_ntu_edu_sg/Ecbxu_4o6vNNqWAWAcZnDbgB-5lEgiSPEjZFyfB49rFhzA?e=gTFZOQ

## Code files
- `faculty.py`: code for analyzing the faculty network and gaining insights on aforementioned issues.
- `preprocessing.py`: code that takes DBLP information of faculty in XML format as input and constructs the faculty network for  analysis.
- `project.py` is the main file that invokes all the necessary procedures from these three files.

### How to Run the Code

To run the code in this project, follow these steps:

1. Make sure you have Python installed on your system.

2. Install the required dependencies:
    ```bash
    pip install networkx matplotlib numpy pandas
    ```
3. Run the main project file
    
    1. Option 1: From the command line
    ```bash
    python project.py
    ```
    Each question is addressed with specialized functions. Please follow the comments in `project.py` to run respective functions that generate metrics and visualizations for each question.

    2. Option 2: In the Jupyter Notebook with `project.ipynb` file. Please open the file and execute each cell. 
