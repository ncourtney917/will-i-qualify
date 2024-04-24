from bs4 import BeautifulSoup
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time

url = "https://www.marathonguide.com/results/browse.cfm?RL=1&MIDD=15240415&Gen=B&Begin=1&End=100&Max=25530"

#response = requests.get(url)
# print(response.text)
driver = webdriver.Chrome()

# Open the webpage
driver.get(url)

# Find the select element by its name
select_element = driver.find_element(by=By.NAME, value="RaceRange")

# Initialize a Select object with the select element
select = Select(select_element)

# Select the option with the specified value
select.select_by_value("B,1,100,25530")


# Parse the HTML
#soup = BeautifulSoup(response.text, 'html.parser')
#print(soup)
# Extract table rows
#rows = soup.find('table', )
#mydivs = soup.find_all("table", {"class": "colordataTable"})


#print(mydivs)#.find_all('tr')
view_button = driver.find_element(by=By.NAME, value="SubmitButton")
view_button.click()

# Find the table element
table = driver.find_element(By.CLASS_NAME, "colordataTable")

# Find all rows within the table
rows = table.find_elements(By.TAG_NAME, "tr")

# Iterate over each row and print the data
for row in rows:
    # Find all cells within the row
    cells = row.find_elements(By.TAG_NAME, "td")
    # Extract text from each cell and print
    for cell in cells:
        print(cell.text)
    print()  # Add an empty line between rows for clarity
"""
# Extract table data and create a list of dictionaries
data = []
for row in rows[1:]:  # Skip the header row
    cells = row.find_all('td')
    data.append({
        "Name": cells[0].text.strip(),
        "Time": cells[1].text.strip(),
        "Overall Place": cells[2].text.strip(),
        "Sex/Div Place": cells[3].text.strip(),
        "Div": cells[4].text.strip(),
        "Location": cells[5].text.strip(),
        "AG Time": cells[6].text.strip(),
        "BQ": cells[7].text.strip()
    })

# Create a DataFrame
df = pd.DataFrame(data)
print(df)
"""