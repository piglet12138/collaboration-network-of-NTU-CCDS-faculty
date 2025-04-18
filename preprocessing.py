import os
import pandas as pd
import requests
from urllib.parse import urlparse
import time
import xml.etree.ElementTree as ET
import json
import numpy as np
import re

def download_dblp_xml(xlsx_file, output_dir="faculty_data"):
    """
    Read DBLP links from xlsx file, download XML data and save to specified directory
    
    Parameters:
        xlsx_file: Excel file path, containing faculty DBLP links
        output_dir: Directory to save XML files
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
    Check the DBLP page of Faculty.csv and extract the unique DBLP person ID (pid) for each professor.
    Uses the XML version of the DBLP page to parse the PID.
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

def extract_paper_data(xml_file_path):
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
    
def add_excellence_to_faculty_csv(input_csv, output_csv):
    """
    Data Cleaning for Question 5 to add new attributes to the Faculty.csv file
    General Steps
    1. Read subject-specific university ranking CSVs
    2. Extract NTU data and assign ranks (intermediate output)
    3. Aggregate professor data and encode subject area expertise
    4. Retrieve DBLP PIDs via XML
    5. Merge with faculty master data and export the final CSV
    """
    # Import necessary libraries for data manipulation, web requests, and XML parsing


    # Mapping of full field names to their corresponding CSRankings field codes
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

    # Create an empty DataFrame to store NTU-specific professor data across all fields
    columns = ["Subject Area", "University Name", "University Rank for Subject Area", "Professor Name", "DBLP Link"]
    combined_df = pd.DataFrame(columns=columns)

    university_column = "University Name"
    index_column = "University Rank for Subject Area"

    # For each subject area: Read the corresponding CSV file, Assign university ranks, Filter for Nanyang Technological University (NTU), Append to the combined DataFrame
    for field_name, field_code in fields_dict.items():
        safe_field_name = re.sub(r"[^\w]+", "_", field_name).strip("_").lower()
        df = pd.read_csv(f'{safe_field_name}_2016-2025-v1.csv')
        unique_universities = {name: idx for idx, name in enumerate(df[university_column].unique())}
        df[index_column] = df[university_column].map(unique_universities) + 1
        df_subset = df[["Subject Area", 'University Name', 'University Rank for Subject Area', 'Professor Name', 'DBLP Link']]
        df_subset['University Name'] = df_subset['University Name'].str.strip().str.lower()
        ntu_df = df_subset[df_subset['University Name'] == 'nanyang technological university']
        combined_df = pd.concat([combined_df, ntu_df], ignore_index=True)
            
    # Create and print a summary table of NTU's ranking across subject areas
    combined_df_subset = combined_df[["Subject Area", 'University Rank for Subject Area']]
    ntu_ranking = combined_df_subset.drop_duplicates()
    ntu_ranking = ntu_ranking.sort_values(by="University Rank for Subject Area", ascending=True)
    print(ntu_ranking)   
        
    # One-hot encode subject areas and aggregate per facutly. Each row represents a facutly with their subject areas and an 'Excellence' flag.

    combined_df_subset2 = combined_df[["Subject Area", "Professor Name", "DBLP Link"]]
    df_encoded = pd.get_dummies(combined_df_subset2, columns=["Subject Area"])
    ntu_agg = df_encoded.groupby(["Professor Name","DBLP Link"]).sum(numeric_only=True).reset_index()
    ntu_agg["Excellence"] = True
        

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

    ntu_agg = add_pid_to_df(ntu_agg)
    ntu_agg.to_csv('Excellence Node.csv', index=False)

    # Merge the aggregated NTU excellence data with the master faculty list using PID. Drop redundant columns and save the enriched faculty file
    df_faculty = pd.read_csv(input_csv)  
    merged_df = df_faculty.merge(
        ntu_agg, 
        left_on=['pid'], 
        right_on=['pid'],
        how='left')
    merged_df = merged_df.drop(columns=['DBLP Link','Professor Name'])
    merged_df.to_csv(output_csv, index=False)


def process_faculty_folder(folder_path, output_path):
    papers_by_key = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".xml"):
            xml_path = os.path.join(folder_path, filename)
            papers_by_key.update(extract_paper_data(xml_path))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers_by_key, f, indent=2, ensure_ascii=False)

    print(f" Extracted paper data saved to: {output_path}")

def deduplicate_paper_data(input_path, output_path):
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
    add_excellence_to_faculty_csv(file, "Faculty_with_excellence.csv")