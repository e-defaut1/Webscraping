# === All imports up top ===
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
import csv

# === Load all teams ===
with open("Team_webs.csv", newline='') as f:
    reader = csv.reader(f)
    teams = [row[:2] for row in reader if row and row[0] and row[1]]

# === Loop through each team and scrape ===
for team_name, url in teams:
    print(f"Processing {team_name} from {url}")
    try:
        # Initialize Safari WebDriver
        driver = webdriver.Safari()

        # Navigate to the target webpage
        target_url = url
        driver.get(target_url)

        # Wait helper with a timeout (e.g., 10 seconds)
        wait = WebDriverWait(driver, 30)

        # Locate the dropdown menu element that contains "Share & Export"
        share_export_menu = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, '//li[contains(@class,"hasmore") and .//span[contains(text(),"Share & Export")]]')
            )
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", share_export_menu)
        time.sleep(10)

        actions = ActionChains(driver)
        actions.move_to_element(share_export_menu).perform()
        time.sleep(10)

        # Click CSV button
        csv_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//button[contains(@tip, "Convert the table below to comma-separated values")]')
            )
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", csv_button)
        time.sleep(5)
        driver.execute_script("arguments[0].click();", csv_button)

        # Wait for CSV data
        pre_element = wait.until(
            EC.visibility_of_element_located((By.ID, "csv_team_game_log_reg"))
        )

        csv_data = pre_element.text
        time.sleep(10)
        driver.quit()

        # === CSV cleaning ===
        x = csv_data.find(',,')
        cropped_data = csv_data[x:]
        lines = cropped_data.splitlines()

        for idx, ln in enumerate(lines):
            if "Score,Score" in ln and "Team,Team" in ln:
                grouping_idx = idx
                break
        else:
            raise ValueError("Could not find the grouping header row")

        clean_csv = "\n".join(lines[grouping_idx:])
        df = pd.read_csv(StringIO(clean_csv), header=[0, 1])

        # Backup header cleaning
        lines = csv_data.strip().splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("Rk,Gtm,Date"):
                header_idx = idx
                break

        clean_lines = lines[header_idx:]
        clean_csv = "\n".join(clean_lines)
        df = pd.read_csv(StringIO(clean_csv), header=0)
        df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

        # Make columns unique
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
        print(df.head())

        # === Save to SQLite ===
        db_name = "NBA_25.db"
        table_name = team_name.replace(" ", "_").replace("-", "_")
        conn = sqlite3.connect(db_name)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()

        print(f"Data inserted into SQLite database '{db_name}' in table '{table_name}'.")

    except Exception as e:
        print(f"Error processing {team_name}: {e}")