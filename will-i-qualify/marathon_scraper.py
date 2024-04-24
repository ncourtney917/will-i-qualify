from bs4 import BeautifulSoup
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time

# Navigate to results homepage
url = "https://www.marathonguide.com/results/browse.cfm?RL=1&MIDD=15240415&Gen=B&Begin=1&End=100&Max=25530"
driver = webdriver.Chrome()
driver.get(url)

# Click the select menu and view the first 100 results
select_element = driver.find_element(by=By.NAME, value="RaceRange")
select = Select(select_element)
select.select_by_value("B,1,100,25530")
view_button = driver.find_element(by=By.NAME, value="SubmitButton")
view_button.click()

data = []
for i in range(1):
    time.sleep(1)

    # Grab the table row elements
    table = driver.find_element(By.CLASS_NAME, "colordataTable")
    rows = table.find_elements(By.TAG_NAME, "tr")

    # Iterate over each row and grab the data
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            name = cells[0].text
            racetime = cells[1].text
            overall_place = cells[2].text
            sex_place = cells[3].text
            division = cells[4].text
            hometown = cells[5].text
            age_adjusted_time = cells[6].text
            boston_qualifier = cells[7].text
            data_row = [name, racetime, division, hometown, boston_qualifier]
            data.append(data_row)

    # Click the right arrow to go to the next page
    button = driver.find_element(By.XPATH, "//img[@src='../images/smallarrow_right.gif']")
    button.click()


results = pd.DataFrame(data)
results.to_csv("data/boston_results_2024v2.csv", header=["Name", "Time", "Division", "Hometown", "Boston Qualify"], index=False)
print(results.head(5))