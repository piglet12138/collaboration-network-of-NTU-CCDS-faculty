# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 17:52:10 2025

@author: Choo
"""

import pandas as pd
import numpy as np
import os
import requests
import time
import xml.etree.ElementTree as ET
import re

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
    "Visualization": "visualization",
}

columns = ["Subject Area", "University Name", "University Rank for Subject Area", "Professor Name", "DBLP Link"]
combined_df = pd.DataFrame(columns=columns)

university_column = "University Name"
index_column = "University Rank for Subject Area"

for field_name, field_code in fields_dict.items():
    safe_field_name = re.sub(r"[^\w]+", "_", field_name).strip("_").lower()
    df = pd.read_csv(f'{safe_field_name}_2016-2025-v1.csv')
    unique_universities = {name: idx for idx, name in enumerate(df[university_column].unique())}
    df[index_column] = df[university_column].map(unique_universities) + 1
    df_subset = df[["Subject Area", 'University Name', 'University Rank for Subject Area', 'Professor Name', 'DBLP Link']]
    df_subset['University Name'] = df_subset['University Name'].str.strip().str.lower()
    ntu_df = df_subset[df_subset['University Name'] == 'nanyang technological university']
    combined_df = pd.concat([combined_df, ntu_df], ignore_index=True)
        
# Create table listing NTU ranks for different subject area
combined_df_subset = combined_df[["Subject Area", 'University Rank for Subject Area']]
ntu_ranking = combined_df_subset.drop_duplicates()
ntu_ranking = ntu_ranking.sort_values(by="University Rank for Subject Area", ascending=True)
print(ntu_ranking)   
    
combined_df_subset2 = combined_df[["Subject Area", "Professor Name", "DBLP Link"]]
df_encoded = pd.get_dummies(combined_df_subset2, columns=["Subject Area"])
ntu_agg = df_encoded.groupby(["Professor Name","DBLP Link"]).sum(numeric_only=True).reset_index()
ntu_agg["Excellence"] = True
    
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

ntu_agg = add_pid_to_df(ntu_agg)
ntu_agg.to_csv('Excellence Node.csv', index=False)


df_faculty = pd.read_csv('Faculty.csv')  
merged_df = df_faculty.merge(
    ntu_agg, 
    left_on=['pid'], 
    right_on=['pid'],
    how='left')
merged_df = merged_df.drop(columns=['DBLP Link','Professor Name'])
merged_df.to_csv('Faculty_with_excellence.csv', index=False)


