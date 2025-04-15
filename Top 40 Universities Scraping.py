# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 17:25:19 2025

@author: Choo
"""

path = r'https://csrankings.org/'
import pandas as pd
import numpy as np
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import argparse
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

fields_dict = {
    "Artificial intelligence": "ai",
    "Computer vision": "vision",
    "Machine learning & data mining": "mlmining",
    "Natural language processing": "nlp",
    "The Web & information retrieval": "ir",
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

# Remove all non-alphabetic characters from a string
def clean_text(text):
    return re.sub(r"[^a-zA-Z ]+", "", text).strip()

def Scrapper():
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(path)


    time.sleep(10)
    button1 = driver.find_element(By.XPATH,'//select[@id="regions"]')
    action = ActionChains(driver)
    action.click(button1).perform()

    button2 = driver.find_element(By.XPATH,'//*[@id="regions"]/optgroup[2]/option[7]').click()
    button3 = driver.find_element(By.XPATH,'//*[@id="fromyear"]/option[47]').click()


    off_button1 = driver.find_element(By.XPATH,'//a[@id="systems_areas_on"]')
    action = ActionChains(driver)
    action.click(off_button1).perform()
    off_button2 = driver.find_element(By.XPATH,'//a[@id="theory_areas_on"]')
    action = ActionChains(driver)
    action.click(off_button2).perform()


    off_button3 = driver.find_element(By.XPATH,'//a[@id="other_areas_on"]')
    action = ActionChains(driver)
    action.click(off_button3).perform()




    down=driver.find_element(By.XPATH,'//*[@id="ranking"]/tbody')
    # driver.execute_script("arguments[0].scrollIntoView();", down)


    actions = ActionChains(driver)
    actions.move_to_element(down).perform()

    rows = driver.find_elements(By.XPATH,'//*[@id="ranking"]/tbody/tr')

    rank = []
    name = []
    data = []
    count = []
    faculty = []
    n = ''
    faculty_details =[]
    seen_universities = set()
    actions = ActionChains(driver)
    for ind,i in enumerate(rows):
        if len(seen_universities) >= 40:
            break
        
        if len(i.text.split()) > 0 and i.text.split()[0] != 'Faculty':
            split = i.text.split()
            n = ''
            
            rank.append(split[0])
            count.append(split[-2])
            faculty.append(split[-1])
            
            for j in split[2:-2]:
                n += j+' '
            name.append(n)
            
            uni_name = ' '.join(split[2:-2])
            if uni_name in seen_universities:
                continue
            seen_universities.add(uni_name)
            print(f"Added: {n} (Total: {len(seen_universities)})")

        
            x = i.find_elements(By.TAG_NAME,'span')[0]
            actions.click(x).perform()
            actions = ActionChains(driver)

        
    whole_table = driver.find_elements(By.XPATH,'//*[@id="ranking"]/tbody/tr')
    n =''
    seen_universities = set()
    
    for ind,i in enumerate(whole_table):
        
        if len(seen_universities) >= 40:
            break
        
        # print(i.text.split(),ind)
        elif (ind%3) == 0:
            split = i.text.split()
            for j in split[2:-2]:
                n += j+' '
            uni_name = ' '.join(split[2:-2])
            if uni_name in seen_universities:
                continue
            seen_universities.add(uni_name)
            print(f"Added: {n} (Total: {len(seen_universities)})")

        elif (ind%3) == 2:
            split = i.text.split('\n')
            for k in split[1:]:
                list = ['ml','nlp','vision','ai','theory','db','security','robotics','network','eda','se']
                for li in list:
                    if li in k:
                        div = k.split()
                        # print(div)
                        faculty_details.append([n,' '.join(div[:-3]),div[-3],div[-2],div[-1]])
            n=''
                     
    cols = ['University Name','Name','Subject','Publications Count', 'Avg Co-Author']


    dataf = pd.DataFrame(faculty_details,columns=cols)
    dataf["Name"] = dataf["Name"].apply(clean_text)
    dataf = dataf.drop_duplicates()
    print("Number of rows:", len(dataf))
    print(dataf.head())
    dataf.to_csv(r'C:/Users/Choo/Desktop/NTU Sem 2 2025/SD6127 Network Science/Group Project/Top 40 Universities.csv',index=False)
    print("CSV Created!")
    
    '''            
    datas = []
    for i in range(len(name)):
        datas.append([rank[i],name[i],count[i],faculty[i]])    
            

    dataf = pd.DataFrame(datas,columns=['Rank','University Name','Mean','Faculty'])

    print(dataf.head())

    dataf.to_csv('University_ranks.csv',index=False)
'''

    time.sleep(2)

    driver.close()
    
    return


if __name__ == '__main__':
    Scrapper()
    



