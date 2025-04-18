"""
Data Cleaning for Question 5 to add new attributes to the Faculty.csv file
General Steps
1. Filter CSRankings.info scraped dataset to only NTU faculty
2. Retrieve DBLP PIDs via XML
3. Merge with faculty master data and export the final CSV
"""
# Import necessary libraries for data manipulation, web requests, and XML parsing
import pandas as pd
import numpy as np
import os
import requests
import time
import xml.etree.ElementTree as ET
import re

# Create an empty DataFrame to store NTU-specific professor data across all fields
columns = ["Subject Area", "University Name", "University Rank for Subject Area", "Professor Name", "DBLP Link"]
combined_df = pd.DataFrame(columns=columns)

university_column = "University Name"
index_column = "University Rank for Subject Area"

# Filter only faculty from NTU. Designate all these faculty as "Excellence" nodes
df = pd.read_csv('CSRankings_Scrapped_2016-2025.csv')
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


# Merge the aggregated NTU excellence data with the master faculty list using PID. Drop redundant columns and save the enriched faculty file
ntu_df = add_pid_to_df(ntu_df)
df_faculty = pd.read_csv('Faculty.csv')  
merged_df = df_faculty.merge(
    ntu_df, 
    left_on=['pid'], 
    right_on=['pid'],
    how='left')
merged_df = merged_df.drop(columns=['DBLP Link','Professor Name'])
merged_df.to_csv('Faculty_with_excellence.csv', index=False)
