import os
import pandas as pd
import requests
from urllib.parse import urlparse
import time
import xml.etree.ElementTree as ET
import json

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
    # add_pid_to_faculty_csv(file)