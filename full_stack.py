#import libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from io import StringIO
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Initialize Safari WebDriver
driver = webdriver.Safari()

# Navigate to the target webpage
url = "https://www.basketball-reference.com/teams/MIL/2025/gamelog/#team_game_log_reg::31"
driver.get(url)

# Wait helper with a timeout (e.g., 10 seconds)
wait = WebDriverWait(driver, 10)

# Locate the dropdown menu element that contains "Share & Export"
share_export_menu = wait.until(
    EC.visibility_of_element_located(
        (By.XPATH, '//li[contains(@class,"hasmore") and .//span[contains(text(),"Share & Export")]]')
    )
)

# Scroll the dropdown element into view
driver.execute_script("arguments[0].scrollIntoView(true);", share_export_menu)
time.sleep(1)

# Hover over the dropdown so that its contents appear
actions = ActionChains(driver)
actions.move_to_element(share_export_menu).perform()
time.sleep(1)
#IF WANT TO USE CSV, ADD CSV CODE HERE

# Use a more robust locator: locate the button using its tip attribute text.
# This button's tip contains "Convert the table below to comma-separated values"
csv_button = wait.until(
    EC.presence_of_element_located(
        (By.XPATH, '//button[contains(@tip, "Convert the table below to comma-separated values")]')
    )
)

# Scroll the CSV button into view in case it's hidden
driver.execute_script("arguments[0].scrollIntoView(true);", csv_button)
time.sleep(0.5)

# Click the CSV button using JavaScript to bypass any clickable issues
driver.execute_script("arguments[0].click();", csv_button)

# After clicking the CSV button, wait until the CSV data appears
pre_element = wait.until(
    EC.visibility_of_element_located((By.ID, "csv_team_game_log_reg"))
)

# Extract the CSV text from the <pre> tag.
csv_data = pre_element.text
print("CSV Data extracted:")
#print(csv_data)

# Optional: wait a few seconds before closing the browser
time.sleep(3)

# Close the browser
driver.quit()

#IF WANT TO USE EXPORT AS, ADD EXPORT AS CODE HERE
# END ADDED CODE HERE
######################################End of web driving commands#################

x = csv_data.find(',,')
cropped_data = csv_data[x:]

# Split into individual lines
lines = cropped_data.splitlines()

# 1. Find the grouping‑header line (the one containing “Score,Score”)
for idx, ln in enumerate(lines):
    if "Score,Score" in ln and "Team,Team" in ln:
        grouping_idx = idx
        break
else:
    raise ValueError("Could not find the grouping header row")

# 2. Build a new CSV text starting at that grouping header
#    which gives us exactly two header rows followed by data
clean_csv = "\n".join(lines[grouping_idx:])
df = pd.read_csv(StringIO(clean_csv), header=[0, 1])
print(df.head())

####################################################################################################

# 1. Split into lines and locate the "real" header row
lines = csv_data.strip().splitlines()

# Find the index of the line that starts with "Rk,Gtm,Date"
for idx, line in enumerate(lines):
    if line.startswith("Rk,Gtm,Date"):
        header_idx = idx
        break

# Keep only from the real header on
clean_lines = lines[header_idx:]
clean_csv = "\n".join(clean_lines)

# 2. Read using the single header row
df = pd.read_csv(StringIO(clean_csv), header=0)

# 3. Drop any accidental Unnamed columns
df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

# 4. (Optional) If you still have duplicate column names (e.g. two "Opp"), you can make them unique:

def make_unique(cols):
    counts = Counter()
    unique = []
    for c in cols:
        counts[c] += 1
        if counts[c] == 1:
            unique.append(c)
        else:
            unique.append(f"{c}_{counts[c]-1}")
    return unique

df.columns = make_unique(df.columns)

# 5. Inspect the result
print(df.head())

####################################################################################################

# Connect to (or create) an SQLite database and insert the DataFrame into a table
db_name = "NBA_25.db"      # name of your database file
table_name = "TeamStats"            # name of the table in the database
conn = sqlite3.connect(db_name)
df.to_sql(table_name, conn, if_exists='replace', index=False)
conn.close()

print(f"Data inserted into SQLite database '{db_name}' in table '{table_name}'.")






