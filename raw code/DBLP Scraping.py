# -*- coding: utf-8 -*-
"""
Scraping of CSRankings.info website in preparation for Question 5 on identifying Excellence nodes
"""

# Import required libraries and custom configuration and utility functions
import pandas as pd
import csv
import time
import argparse
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import re
import config 
import utils 


# XPath values for selecting different regions in the CSRankings dropdown menu
ranking_NA ='//*[@id="regions"]/optgroup[2]/option[1]'
ranking_SA = '//*[@id="regions"]/optgroup[2]/option[2]'
ranking_africa ='//*[@id="regions"]/optgroup[2]/option[3]'
ranking_asia ='//*[@id="regions"]/optgroup[2]/option[4]'
ranking_aus = '//*[@id="regions"]/optgroup[2]/option[5]'
ranking_eu ='//*[@id="regions"]/optgroup[2]/option[6]'
ranking_world = '//*[@id="regions"]/optgroup[2]/option[7]'


# Displays a table of available subject areas and their codes
def print_field_choices():
    table = PrettyTable()
    table.field_names = ["Field", "Code"]

    for name, code in fields_dict.items():
        table.add_row([name, code])
    print(table)
    

# Remove all non-alphabetic characters from a string
def clean_text(text):
    return re.sub(r"[^a-zA-Z ]+", "", text).strip()

# Remove all non-numeric characters from a string
def clean_number(num_text):
    return re.sub(r"[^0-9]+", "", num_text).strip()

# Save university and professor data into a CSV file
def save_universities_to_csv(filename, universities):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "University Name",
                "Professor Name",
                "Home Page",
                "Google Scholar",
                "DBLP Link",
            ]
        )
        for university in universities:
            for professor in university.get("professors", []):
                writer.writerow(
                    [
                        university.get("name", ""),
                        professor.get("name", ""),
                        professor.get("home_page", ""),
                        professor.get("google_scholar", ""),
                        professor.get("dblp", ""),
                        ]
                    )

# Extract list of professor data from a given university section
def parse_professors(tbody):
    professors = []
    prof_trs = tbody.find_all("tr", recursive=False)
    # Professors' info are stored in another tr list
    for prof_tr in prof_trs:
        professor_info = parse_professor_info(prof_tr)
        if professor_info:
            professors.append(professor_info)
    return professors

# Extract 3 relevant links (Home page, DBLP, Google Scholar) for a professor
def parse_professor_info(prof_tr):
    tds = prof_tr.find_all("td")
    if not tds:
        return None
    professor = {}
    for j, td in enumerate(tds):
        if j % 4 == 1:
            homepage = td.find("a", title="Click for author's home page.")
            if homepage:
                professor["name"] = clean_text(homepage.text)
                professor["home_page"] = homepage["href"]
            google_scholar = td.find(
                "a", title="Click for author's Google Scholar page."
                )
            if google_scholar:
                professor["google_scholar"] = google_scholar["href"]
            dblp_link = td.find("a", title="Click for author's DBLP entry.")
            if dblp_link:
       #        professor["pub_count"] = clean_text(dblp_link.text)
                professor["dblp"] = dblp_link["href"]
    return professor


# Navigate to CSRankings, select a region, and extract university and professor info. The most complicated part...
def fetch_universities(url,region):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)
    
    button1 = driver.find_element(By.XPATH,'//select[@id="regions"]')
    action = ActionChains(driver)
    action.click(button1).perform()
    button2 = driver.find_element(By.XPATH,region).click()


    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    universities = []
    table = soup.find("table", id="ranking")
    tbody = table.find("tbody")
    trs = tbody.find_all("tr", recursive=False)

    for i, tr in enumerate(trs):
        if i % 3 == 0:
            # Parse university info
            university_info = parse_university_info(tr)
        if i % 3 == 2 and university_info:
            # Parse professors
            university_info["professors"] = parse_professors(tr.find("tbody"))
            universities.append(university_info)

    return universities

# Extract rank and name of a university from the page
def parse_university_info(tr):
    tds = tr.find_all("td")
    if not tds:
        return None
    university_info = {}
    for j, td in enumerate(tds):
        if j % 4 == 0:
            university_info["rank"] = clean_number(td.text)
        if j % 4 == 1:
            university_info["name"] = clean_text(td.text)
    return university_info

# Command-line argument parser to configure the scraping parameters
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Fetch universities and professors data from CSRankings."
    )
    
    all_fields = ",".join(fields_dict.values())
    
    parser.add_argument(
        "--fields",
        type=str,
        default=all_fields,
        help='Code of relevant fields, using "," to split multiple fields (e.g., "sec,ai" for Security and Artificial Intelligence)',
    )
    parser.add_argument(
        "--start_year", type=int, default=2016, help="Start year (default 2016)"
    )
    parser.add_argument(
        "--end_year", type=int, default=time.localtime().tm_year, help="End year (default 2025)"
    )

    args = parser.parse_args()

    if args.start_year > args.end_year or args.end_year > time.localtime().tm_year:
        parser.error("Invalid year range.")

    if not all(field in set(fields_dict.values()) for field in args.fields.split(",")):
        parser.error("Invalid field code.")

    return (
        args.fields.replace(" ", "").replace(",", "&"),
        args.start_year,
        args.end_year,
    )


if __name__ == "__main__":
    print_field_choices()

    from_year = 2016
    to_year = 2025
    url = f"https://csrankings.org/#/fromyear/{from_year}/toyear/{to_year}/&world"
    print(f"Your URL: {url}")
     
    universities = fetch_universities(url,ranking_asia)
    filename = f'{from_year}-{to_year}-v3.csv'
    save_universities_to_csv(filename, universities)
    print(f"Data has been saved to {filename}")
        
