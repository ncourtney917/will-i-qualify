import pandas as pd
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import os
import re
import time

# TODO: Eliminate if there are 0 BQS
# TODO: Add New to temp list

# Get findmymarathon list
# Check for new marathons
# Get dates for those marathons
# Search name and date
# if nothing, search name without marathon and date
# if nothing search state and date


def find_my_marathon_search(driver, year):
    marathon_list_fname = f"data/find_my_marathon_temp_list.csv"
    # Create file if it doesn't exist
    try:
        marathon_df = pd.read_csv(marathon_list_fname)
    except:
        marathon_df = pd.DataFrame()

    stop = False
    marathon_list = []
    for i in range(20):
        if stop:
            break
        url = f"https://findmymarathon.com/bostonmarathonqualifiers-{year}.php?page={i+1}#list"
        driver.get(url)
        tables = driver.find_elements(By.TAG_NAME, "tbody")
        bq_table = tables[2]
        rows = bq_table.find_elements(By.TAG_NAME, "tr")
        if len(rows) > 2:
            for row in rows:
                tds = row.find_elements(By.TAG_NAME, "td")
                if tds:
                    name_field = tds[1]
                    marathon_text = name_field.text
                    marathon_split_text1 = marathon_text.split("\n")

                    location = marathon_split_text1[-1]
                    location_split = location.split(",")
                    city = location_split[0].strip()
                    state = location_split[-1].strip()

                    marathon_split_text2 = marathon_split_text1[0].split("(")
                    marathon_name = marathon_split_text2[0].strip()
                    marathon_year = marathon_split_text2[-1].replace(")", "")

                    marathon_link = name_field.find_element(By.TAG_NAME, "a")
                    href = marathon_link.get_attribute("href")
                    bq_field = tds[2].text
                    bq_quals = bq_field.split(" ")[0]
                    bq_quals = bq_quals.replace(",","")
                    data = [marathon_name, marathon_year, city, state, "", href, ""]
                    # Skip if there are no bq quals
                    if bq_quals == "0":
                        print(data)
                        continue
                    marathon_list.append(data)
        else:
            stop = True
    print(f"Collected {len(marathon_list)} marathons!")
    df = pd.DataFrame(marathon_list, columns=["Marathon", "Year", "City", "State", "Link", "FMM_Link", "Date"])

    if marathon_df.empty is False:
        full_df = pd.concat([marathon_df, df], axis=0)
    else:
        full_df = df.copy()
    # Write new marathons to DF
    new_df = full_df.drop_duplicates(subset=["Year", "FMM_Link"], keep=False)
    new_df.to_csv("new_marathons_temp_list.csv", index=False)
    # Write
    full_df.drop_duplicates(subset=["Year", "FMM_Link"], keep="first", inplace=True)
    full_df.to_csv(marathon_list_fname, index=False)

def find_my_marathon_date_search(driver):
    unsearchable_fname = f"data/unsearchable_df.csv"
    unsearchable_df = pd.read_csv(unsearchable_fname)

    marathon_list = []
    for i, row in unsearchable_df.iterrows():
        url = row["FMM_Link"]
        driver.get(url)
        text_box = driver.find_element(By.ID, "RaceDetails")
        headers = text_box.find_elements(By.TAG_NAME, "h4")
        year = str(row["Year"])
        year_text = [h.text for h in headers if str(row["Year"]) in h.text]
        formatted_date = ""
        if year_text:
            race_dates_text = year_text[0]
            pattern = r'[A-Za-z]+, ([A-Za-z]+ \d{1,2}, \d{4})'
            matches = re.findall(pattern, race_dates_text)
            if matches:
                long_date = [m for m in matches if year in m][0]
                date_obj = datetime.strptime(long_date, '%B %d, %Y')
                # Format the datetime object into the desired format
                formatted_date = date_obj.strftime('%m/%d/%Y')
        print(row["Marathon"], formatted_date)
        row["Date"] = formatted_date
        marathon_list.append(row)

    unsearchable_df = pd.DataFrame(marathon_list)
    unsearchable_df.to_csv(unsearchable_fname, index=False)


def find_marathon_guide_equivalent(driver, detailed_search: bool = False):
    search_url = "https://www.marathonguide.com/races/search.cfm"
    if detailed_search:
        temp_list_fname = "data/unsearchable_df.csv"
    else:
        temp_list_fname = "data/new_marathons_temp_list.csv"
    marathon_list_fname = "data/marathon_list.csv"
    try:
        temp_df = pd.read_csv(temp_list_fname)
    except FileNotFoundError:
        return
    marathon_list_df = pd.read_csv(marathon_list_fname)
    unsearchable = []
    searchable = []
    for i, row in temp_df.iterrows():
        match = marathon_list_df.loc[(marathon_list_df["Name"]==row["Marathon"]) & (marathon_list_df["Year"]==row["Year"]), :]
        if match.empty:
            if detailed_search:
                attempts = ["dateSearch"]
            else:
                attempts = ["fullName", "abridgedName", "firstWord"]
            got_data = False
            for attempt in attempts:
                driver.get(search_url)
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "bodyInnerPageContents")))
                form = driver.find_element(By.ID, "bodyInnerPageContents")
                if attempt == "fullName":
                    m_name = row["Marathon"]
                elif attempt == "abridgedName":
                    m_name = row["Marathon"].replace("Marathon", "").strip()
                elif attempt == "firstWord":
                    m_name = row["Marathon"].split(" ")[0]
                else:
                    m_name = None

                # Enter state
                state_element = form.find_element(By.NAME, "state")
                select = Select(state_element)
                select.select_by_value(row["State"])

                begin_date_form = form.find_element(By.NAME, "BeginDate")
                end_date_form = form.find_element(By.NAME, "EndDate")
                if attempt == "dateSearch":
                    # Use exact date and state
                    exact_date = row["Date"]
                    begin_date_form.send_keys(exact_date)
                    end_date_form.send_keys(exact_date)
                else:
                    # Use name, state, and year
                    mar_name = form.find_element(By.NAME, "MarName")
                    mar_name.send_keys(m_name)
                    # Enter start of year date
                    marathon_year = row["Year"]
                    begin_date = f"01/01/{marathon_year}"
                    begin_date_form.send_keys(begin_date)
                    # Enter end of year date
                    end_date = f"12/31/{marathon_year}"
                    end_date_form.send_keys(end_date)
                # Submit search
                submit = form.find_element(By.NAME, "submit")
                submit.click()
                try:
                    WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, "racesListTable")))
                except selenium.common.exceptions.TimeoutException:
                    continue

                race_results_table = driver.find_element(By.CLASS_NAME, "racesListTable")
                race_results = race_results_table.find_elements(By.TAG_NAME, "tr")
                if len(race_results) == 2:
                    marathon_row = race_results[1]
                    cells = marathon_row.find_elements(By.TAG_NAME, "td")
                    date = cells[0].text
                    year = f"20{date.split('/')[2]}"
                    name_cell = cells[1]
                    marathon_links = name_cell.find_elements(By.TAG_NAME, "a")
                    marathon_link = [m for m in marathon_links if "racedetails" in m.get_attribute("href")][0]
                    marathon_url = marathon_link.get_attribute("href")
                    marathon_url = marathon_url.replace("/races/racedetails", "/results/browse")
                    marathon_name = marathon_link.text
                    data = [marathon_name, date, "", marathon_url, False, year, row["FMM_Link"]]
                    print(data)
                    searchable.append(data)
                    got_data = True
                    break
                else:
                    continue
            """
            elif len(race_results) > 2:
                for i in range(len(race_results)-1):
                    marathon_row = race_results[i+1]
                    cells = marathon_row.find_elements(By.TAG_NAME, "td")
                    date = cells[0].text
                    year = f"20{date.split('/')[2]}"
                    name_cell = cells[1]
                    marathon_links = name_cell.find_elements(By.TAG_NAME, "a")
                    marathon_link = [m for m in marathon_links if "racedetails" in m.get_attribute("href")][0]
                    marathon_url = marathon_link.get_attribute("href")
                    marathon_name = marathon_link.text
                    data = [marathon_name, date, "MULTIPLE", marathon_url, False, year]
                    print(data)
                    searchable.append(data)
            """
            if got_data is False:
                unsearchable.append(row)
    columns = ["Name", "Date", "Finishers", "Link", "Scraped", "Year", "FMM_Link"]
    print(len(searchable))
    print(len(unsearchable))
    searchable_df = pd.DataFrame(searchable, columns=columns)
    unsearchable_df = pd.DataFrame(unsearchable)
    unsearchable_df.to_csv("data/unsearchable_df.csv", index=False)

    full_marathon_df = pd.concat([marathon_list_df, searchable_df])
    full_marathon_df.drop_duplicates(subset=["Year", "Link"], keep="first", inplace=True)
    full_marathon_df.to_csv(marathon_list_fname, mode="w", index=False)







if __name__ == "__main__":
    driver = webdriver.Chrome()
    bq_year = "2025"
    get_find_my_marathon_list = False
    date_search = False
    if date_search:
        find_my_marathon_date_search(driver)
    else:
        if get_find_my_marathon_list:
            # Get marathon list from given year and write to CSV
            find_my_marathon_search(driver, bq_year, unsearchable_check=True)
        else:
            find_marathon_guide_equivalent(driver)
