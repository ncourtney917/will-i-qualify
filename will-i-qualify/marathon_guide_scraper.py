import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime
import os
import time
import re

BOSTON_CUTOFF = "5:40:00"

# TODO: Scrape multiple years at once
# TODO: SCRAPE WHEN THERE ARE NO FINISHERS
# TODO: Get Dan to do the manual ones

def get_marathon_results(driver, url, bq_year, marathon_name, marathon_date, finishers):
    start = time.time()
    # Navigate to results homepage
    driver.get(url)

    print(f"Getting results for {marathon_name} from {marathon_date}...")
    # Click the select menu and view the first 100 results
    select_element = driver.find_element(by=By.NAME, value="RaceRange")
    page_options = select_element.find_elements(by=By.TAG_NAME, value="option")
    num_pages = len(page_options)
    select = Select(select_element)
    try:
        select.select_by_visible_text("1 - 100")
    except:
        try:
            time.sleep(1)
            select.select_by_index(1)
        except:
            print("#########")
            print(f"COULD NOT FIND RESULTS FOR {marathon_name}")
            print("##########")
    view_button = driver.find_element(by=By.NAME, value="SubmitButton")
    view_button.click()
    data = []
    for i in range(num_pages):
        try:
            # Wait until table loads
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "colordataTable")))
        except TimeoutException:
            print(f"Page did not load for {marathon_name}...skipping to the next marathon")

        # Grab the table row elements
        table = driver.find_element(By.CLASS_NAME, "colordataTable")
        rows = table.find_elements(By.TAG_NAME, "tr")
        headers = table.find_elements(By.TAG_NAME, "th")
        header_text = [h.text for h in headers]

        # Initialize column name indices
        name_index = None
        time_index = None
        bq_index = None
        div_index = None
        hometown_index = None

        # Check for index of column names
        name_list_index = [index for index, element in enumerate(header_text) if "name" in element.lower()]
        bq_list_index = [index for index, element in enumerate(header_text) if "bq" in element.lower()]
        time_list_index = [index for index, element in enumerate(header_text) if "net time" in element.lower()]
        if len(time_list_index) == 0:
            time_list_index = [index for index, element in enumerate(header_text) if "time" == element.lower()]
        div_list_index = [index for index, element in enumerate(header_text) if "div" == element.lower()]
        hometown_list_index = [index for index, element in enumerate(header_text) if "city" in element.lower() or "state" in element.lower() or "country" in element.lower()]

        # Get column index
        if name_list_index:
            name_index = name_list_index[0]
        if bq_list_index:
            bq_index = bq_list_index[0]
        if time_list_index:
            time_index = time_list_index[0]
        if div_list_index:
            div_index = div_list_index[0]
        if hometown_list_index:
            hometown_index = hometown_list_index[0]

        # Iterate over each row and grab the data
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                if isinstance(name_index, int):
                    name = cells[name_index].text
                else:
                    name = ""
                if isinstance(time_index, int):
                    racetime = cells[time_index].text
                else:
                    racetime = ""
                if isinstance(div_index, int):
                    division = cells[div_index].text
                else:
                    division = ""
                if isinstance(hometown_index, int):
                    hometown = cells[hometown_index].text
                else:
                    hometown = ""
                if isinstance(bq_index, int):
                    boston_qualifier = cells[bq_index].text
                else:
                    boston_qualifier = ""
                data_row = [name, racetime, division, hometown, boston_qualifier, marathon_name, marathon_date]
                data.append(data_row)
        # Cutoff if the most recent runner grabbed has exceeded the cutoff time
        if racetime > BOSTON_CUTOFF:
            break


        try:
            # Click the right arrow to go to the next page
            button = driver.find_element(By.XPATH, "//img[@src='../images/smallarrow_right.gif']")
            driver.execute_script("arguments[0].click();", button)
        except NoSuchElementException:
            break


    end = time.time()
    print(f"Took {end - start} seconds to scrape")
    results = pd.DataFrame(data)
    # Write to file
    full_results_fname = "data/raw_results_all.csv"
    if os.path.exists(full_results_fname):
        results.to_csv(full_results_fname, mode="a", header=False, index=False)
    else:
        results.to_csv(full_results_fname, header=["Name", "Time", "Division", "Hometown", "Boston Qualify", "Marathon", "Marathon Date"], index=False)
    return

def get_marathon_list(driver, year):
    """Get list of all marathons in a given year on the boston qualifying page"""
    url = f"https://www.marathonguide.com/races/BostonMarathonQualifyingRaces.cfm?Year={str(year)}"
    marathon_list_fname = f"data/marathon_list.csv"
    # Create file if it doesn't exist
    try:
        marathon_df = pd.read_csv(marathon_list_fname)
    except:
        marathon_df = pd.DataFrame()

    driver.get(url)
    bq_table = driver.find_elements(By.CLASS_NAME, "colordataTable")[1]
    rows = bq_table.find_elements(By.TAG_NAME, "tr")
    # Iterate over each row and grab the data
    marathon_data = []
    for i, row in enumerate(rows):
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            marathon = cells[1]
            marathon_link = marathon.find_element(By.TAG_NAME, "a")
            marathon_text = marathon.text
            href = marathon_link.get_attribute("href")
            # Replace with link to the race results
            href = href.replace("/races/racedetails", "/results/browse")
            finishers = cells[2].text
            mt_split = marathon_text.split("(")
            marathon_name = mt_split[0].strip()
            marathon_date = mt_split[-1].split(" ")[0]
            year_re = re.search("(\d{4})", marathon_date)
            if year_re:
                year = year_re.group()
            else:
                year = ""
            scraped = "FALSE"
            marathon_row = [marathon_name, marathon_date, finishers, href, scraped, year, ""]
            marathon_data.append(marathon_row)
    results = pd.DataFrame(marathon_data, columns=["Name", "Date", "Finishers", "Link", "Scraped", "Year","FMM_Link"])
    if marathon_df.empty is False:
        full_df = pd.concat([marathon_df, results], axis=0)
    else:
        full_df = results.copy()
    full_df.drop_duplicates(subset=["Link"], keep="first", inplace=True)
    full_df.to_csv(marathon_list_fname, header=True, index=False)
    return

def scrape_results(driver, bq_year):
    # Get marathon list
    marathons = []
    marathon_list_fname = f"data/marathon_list.csv"
    marathon_list = pd.read_csv(marathon_list_fname)
    for i, marathon in marathon_list.iterrows():
        if marathon["Scraped"] == False:
            url = marathon["Link"]
            marathon_name = marathon["Name"]
            marathon_date = marathon["Date"]
            if isinstance(marathon["Finishers"], str):
                num_finishers = marathon["Finishers"].replace(",", "")
            else:
                num_finishers = ""
            get_marathon_results(driver, url, bq_year, marathon_name, marathon_date, num_finishers)
            marathon["Scraped"] = True
        marathons.append(marathon)
        df = pd.DataFrame(marathons)
        df.to_csv(marathon_list_fname, index=False)


if __name__ == "__main__":
    driver = webdriver.Chrome()
    bq_year = "2025"
    year = 2024
    get_results = True
    if get_results:
        scrape_results()
    else:
        # Get marathon list from given year and write to CSV
        url = f"https://www.marathonguide.com/races/BostonMarathonQualifyingRaces.cfm?Year={str(year)}"
        get_marathon_list(driver, url, year)
