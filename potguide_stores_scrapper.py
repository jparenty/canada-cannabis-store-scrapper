# -*- coding: utf-8 -*-
"""
Created on Tue May 17 14:18:40 2022

Scrapper to scrap the count of cannabis stores by provinces across all Canada.
For now the script only count each store.
You can edit the code to easily scrap details about each store (such as LAT/LONG, is MED/REC, and possible reviews).
You would have to create another dataFrame to store the store details data.

TO USE THE SCRIPT:
    Call the script from the commmand line, results output will be located in the ./results/ subdirectory.
    EX:
        $python scrap_stores_count_potguide.py 
        
    When starting the script, you must click on a popup from potguide website before letting it run by itself
    
@author: Jean Parenty
"""

import sys
import os
import urllib.parse
import unidecode
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
from time import gmtime, strftime
import re
import pandas as pd


def format_city_name(city):
    
    city = urllib.parse.unquote(city)
    city = unidecode.unidecode(city)
    city = city.lower()
    city = re.sub(r'[^\w\s]', '', city)
    city_clean = city.replace(" ", "")
    return city_clean



def main(output):

    provinces = ["ALberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Nortwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon"]
    df_columns = ["Date", "ALberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Nortwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon", "Total"]
    
    #consider canada's big city for scrapper to NOT zoom in the map for those cities 
    #scrapper will zoom in the map for smaller cities in order to view only the stores belonging to it and not consider the surrounding cities' stores
    canada_cities = pd.read_csv("canadacities.csv")
    canada_big_cities = canada_cities.loc[canada_cities["population"] > 200000]
    canada_big_cities["city"] = canada_big_cities["city"].apply(format_city_name)
    canada_big_cities_list = canada_big_cities["city"].to_list()
    
    #create df to store results
    stores_count_results = pd.DataFrame(columns = df_columns)
    
    provinces_potguide_link = [
        "https://potguide.com/dispensaries/canada/alberta/",
        "https://potguide.com/dispensaries/canada/british-columbia/",
        "https://potguide.com/dispensaries/canada/manitoba/",
        "https://potguide.com/dispensaries/canada/new-brunswick/",
        "https://potguide.com/dispensaries/canada/newfoundland-and-labrador/",
        "https://potguide.com/dispensaries/canada/northwest-territories/",
        "https://potguide.com/dispensaries/canada/nova-scotia/",
        "https://potguide.com/dispensaries/canada/nunavut/",
        "https://potguide.com/dispensaries/canada/ontario/",
        "https://potguide.com/dispensaries/canada/prince-edward-island/",
        "https://potguide.com/dispensaries/canada/quebec/",
        "https://potguide.com/dispensaries/canada/saskatchewan/",
        "https://potguide.com/dispensaries/canada/yukon/"]
    
    provinces_results= []
    
    driver = webdriver.Chrome(ChromeDriverManager().install())
    
    error_dict = dict.fromkeys(provinces, [])
    
    #iterate through the provinces 
    for province_index in range(0, len(provinces_potguide_link)):
        
        province_link = provinces_potguide_link[province_index]
        
        province_process = provinces[province_index]
        
        driver.get(province_link)
        
        #sleep driver for human being to confirm age on potguide website
        time.sleep(6)
        
        province_stores_count = 0
        
        #erro is considered for a city present in the provinces city list of potguide but for which no stores are present
        #which is probably due to error in comparing city name and store city adress
        province_error = []
        
        #get all the city links for the province/territory
        city_links = []
        the_city_element = driver.find_elements(By.CLASS_NAME, 'city-list-item')
        for tag in the_city_element:
            city_links.append(tag.get_attribute('href'))
        
        #iterate through the provinces city and count the stores in the city
        for link in city_links: 
        
            driver.execute_script("window.open('');")
            #switch to new window
            driver.switch_to.window(driver.window_handles[1])
            
            #go to province cities listing page
            driver.get(link)
        
            #wait for the page to load before trying to fetch data
            #time.sleep(5)
            page_load_flag = False
            while not page_load_flag:
                try:
                    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "fn-store-address")))
                    page_load_flag = True
                except:
                    print("refreshing web page...")
                    time.sleep(40)
                    driver.refresh()
            
            #handle page not found after clicking on a city 
            check_not_found = driver.find_element(By.ID, "pg-breadcrumbs")
            not_found = check_not_found.find_elements(By.TAG_NAME, "li")[-1].find_element(By.TAG_NAME, "small").get_attribute('innerHTML').strip().lower()
            if not_found == "page not found":
                print("Page not found for: " + link.split("/")[-2])
                continue
            
            city = link.split("/")[-2]
            city = format_city_name(city)
    
           
            stores_listing = len(driver.find_elements(By.CLASS_NAME, "fn-basic-listing"))
            
            #if city is NOT part of canada_big_city, zoom in the map to filter out shops of surrounding cities
            #AND
            #if stores listing len < 30 --> no zoom in
            if city not in canada_big_cities_list and stores_listing == 30:
                driver.find_element(By.CLASS_NAME, "mapboxgl-ctrl-zoom-in").click()
                time.sleep(1)
                driver.find_element(By.CLASS_NAME, "mapboxgl-ctrl-zoom-in").click()
                time.sleep(1)
                driver.find_element(By.CLASS_NAME, "mapboxgl-ctrl-zoom-in").click()
                time.sleep(1)
    
            
            city_count = 0
            
            next_page = True
            
            #iterate pagination of list of stores of a province's city
            while next_page:
                #wait until store listing load before trying to scrap data
                page_load_flag = False
                while not page_load_flag:
                    try:
                        element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "fn-store-address")))
                        page_load_flag = True
                    except:
                        print("refreshing web page...")
                        time.sleep(40)
                        driver.refresh()
    
                stores = driver.find_elements(By.CLASS_NAME, "fn-basic-listing")
                print("Stores listing length: " + str(len(stores)))
                
                #iterate over the stores of page # of a province's city
                for i in range(0, len(stores)):
                    
                    #grabbing the adress of the store in the list, not all the stores in the list actually are located in the selected city, so need to make                 
                    adress = stores[i].find_elements(By.CLASS_NAME, "fn-store-address")
                    #formating store adress
                    adress_city = adress[1].get_attribute('innerHTML').split(',')[0]
                    adress_city = format_city_name(adress_city)
                   
                    print("Collecting for " + city + " - store adress: " + adress_city)
                    #checking that store is indeed located in the city we want to count number of stores
                    if city in adress_city:
                        province_stores_count = province_stores_count+1 
                        city_count = city_count + 1
                        #!!ADD CODE HERE TO SCRAP STORE DETAILS!!#
                        # - using selenium library and refering to potguide website for html template
                        #####
                    else:
                        continue
                    
                driver.find_element(By.CLASS_NAME,'pagination').location_once_scrolled_into_view
                time.sleep(1)
                pagination = driver.find_element(By.CLASS_NAME,'pagination')
                pagination_button = pagination.find_elements(By.TAG_NAME, 'li')
                next_button_check = pagination_button[-1].find_element(By.TAG_NAME, 'a').get_attribute('href')
                next_button = pagination_button[-1].find_element(By.TAG_NAME, 'a')
    
                if next_button_check == "javascript:;":
                    next_page = False
                else: 
                    next_button.click()
            
            #check for error
            if city_count == 0:
                province_error.append(city)
                
            print("Collected store count for "+ city + ": " + str(city_count)  + " - Total count: " + str(province_stores_count))
            time.sleep(1)
            
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    
        #write province store count results in df before counting for next province
        provinces_results.append(province_stores_count)
        error_dict[province_process] = province_error
        
    #compute the total number of stores
    provinces_results.append(sum(provinces_results))
    #add today's date to results
    provinces_results.insert(0, strftime("%Y-%m-%d", gmtime()))
    
    #write results in df
    stores_count_results.loc[len(stores_count_results)] = provinces_results

    #write results to csv at output path
    pd.to_csv(stores_count_results, "./results/" + strftime("%Y-%m-%d", gmtime()) + "results.csv")
    
if __name__ == "__main__":
    output = str(sys.argv[1])
    main(output)

    