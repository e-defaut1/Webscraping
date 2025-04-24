# Webscraping
This is a storage location for all files related to my web scraping project.

Explanation of files
- full_stack.py is a script that will go to basketball-reference.com which is defined in the script itself. The url defined in the script is the Milwaukee Bucks 2025 game log. This script functions by opening a safari web driver and navigating to the specified url. The webpage holds an interactive table (java) of stats from each game of the 2025 season. Using Selenium, the script clicks several buttons to convert the java table to a csv text table which we can scrape from the html. The scraped text is then cleaned up (specifically the column names) and then imported into an SQLite database.

- full_stack_looped_final.py functions the same way as full_stack.py however it will loop thru a list of teams with the corresponding basketball-reference.com urls. The data is stored in the NBA_25.db with each team having its own table. 

- Team_webs_master.csv holds 2 columns: team name and url to the team game log for 2025.

- NBA_25.db is the SQLite database in which the scraped team stats are stored.

