import xml.etree.ElementTree as ET
import json
from collections import defaultdict
import os
import csv

# sparse xml
def parse_collaborations(xml_file):

    tree = ET.parse(xml_file)
    root = tree.getroot()

    
    main_author = None
    for person in root.findall(".//person"):
        author = person.find("author")
        if author is not None:
            main_author = {
                "pid": author.get("pid"),
                "name": author.text
            }
            break

    # collect collaborator by year
    collaborations_by_year = defaultdict(list)

    # for all article and inproceedings
    for r in root.findall("./r"):
        publication = None
        for child in r:
            if child.tag in ["article", "inproceedings"]:
                publication = child
                break

        if publication is None:
            continue

        # get year
        year_elem = publication.find("year")
        if year_elem is None:
            continue

        year = year_elem.text

        # check if the main author in the list
        has_main_author = False
        for author in publication.findall("author"):
            if author.get("pid") == main_author["pid"]:
                has_main_author = True
                break

        if has_main_author:
            # collect all collaborators（including the mainauthor）
            for author in publication.findall("author"):
                pid = author.get("pid")
                name = author.text

                collaborations_by_year[year].append({
                    "pid": pid,
                    "name": name
                })

    result = {
        "author": main_author,
        "collaborations_by_year": dict(collaborations_by_year)
    }

    return result



def generate_raw_data():
    directory = r"faculty_data"
    all_collaborations = {}
    main_authors = []
    
    # iterate all xml files
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            xml_file = os.path.join(directory, filename)
            print(f"processing file: {filename}")

            result = parse_collaborations(xml_file)
            
            # collect NTU faculty pid for filtering
            if result["author"]:

                all_collaborations[result["author"]["pid"]] = result
                

                main_authors.append({
                    "pid": result["author"]["pid"],
                    "name": result["author"]["name"]
                })
    

    with open("all_collaborations.json", "w", encoding="utf-8") as f:
        json.dump(all_collaborations, f, indent=2, ensure_ascii=False)
    

    with open("main_authors.json", "w", encoding="utf-8") as f:
        json.dump(main_authors, f, indent=2, ensure_ascii=False)
    
    print("data saved in all_collaborations.json and main_authors.json")


def generate_network_links():
    # read the CCDS faculties list
    with open('main_authors.json', 'r', encoding='utf-8') as f:
        main_authors = json.load(f)

    # CCDS faculty pid set
    main_author_pids = {author['pid'] for author in main_authors}

    # read all collaborators
    with open('all_collaborations.json', 'r', encoding='utf-8') as f:
        all_collaborations = json.load(f)

    # write in network links
    with open('main_authors_collaborations.csv', 'w', encoding='utf-8', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        csv_writer.writerow(['colab_id','author_pid', 'author_name', 'year', 'collaborator_pid', 'collaborator_name'])

        count = 0
        for author_pid, author_data in all_collaborations.items():
            # for every CCDS faculty
            if author_pid in main_author_pids:
                author_name = author_data['author']['name']

                # for each year
                for year, collaborators in author_data['collaborations_by_year'].items():
                    # filter the CCDS faculty
                    main_collaborators = [collab for collab in collaborators if collab['pid'] in main_author_pids and collab['pid'] != author_pid]

                    # write in the info
                    for collaborator in main_collaborators:
                        count += 1
                        csv_writer.writerow([
                            count,
                            author_pid,
                            author_name,
                            year,
                            collaborator['pid'],
                            collaborator['name']
                        ])

    print("finished in main_authors_collaborations.csv ")


if __name__ == "__main__":

    # generate_raw_data()
    generate_network_links()
