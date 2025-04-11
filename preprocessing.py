import os
import pandas as pd
import requests
from urllib.parse import urlparse
import time
import xml.etree.ElementTree as ET
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
                
            # Save XML file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            print(f"Successfully saved to: {output_file}")

            # Add delay to avoid too many requests
            time.sleep(1)
            
        except Exception as e:
            print(f"Failed to download XML data for {name}: {e}")





def add_pid_to_faculty_csv(input_csv, output_csv=None):

    if output_csv is None:
        output_csv = input_csv
    df = pd.read_csv(input_csv)
    df['pid'] = None

    for idx, row in df.iterrows():
        dblp_url = row["DBLP"]
        name = row["Faculty"]

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



if __name__ == "__main__":
    # Usage example
    file = "Faculty.csv"
    #download_dblp_xml(file)
    add_pid_to_faculty_csv("Faculty.csv")