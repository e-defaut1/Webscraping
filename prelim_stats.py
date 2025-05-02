# prelim_stats.py

import sqlite3
import pandas as pd

def get_prelim_stats_df(team_name: str, db_path: str = "NBA_25.db") -> pd.DataFrame:
    """
    Connects to the SQLite database, pulls basic aggregated stats
    for `team_name`, and returns a 1-row DataFrame.
    """
    conn = sqlite3.connect(db_path)
    # replace TeamStats_AllTeams with whatever combined table you use
    query = f"""
        SELECT
            Team AS Team,
            COUNT(*) AS Games_Played,
            AVG(CASE WHEN Team_Points > Opponent_Points THEN 1 ELSE 0 END) AS Win_Pct,
            AVG(Team_Points) AS Avg_Pts_For,
            AVG(Opponent_Points) AS Avg_Pts_Against,
            AVG(Team_Points - Opponent_Points) AS Avg_Margin
        FROM TeamStats_AllTeams
        WHERE Team = ?
    """
    df = pd.read_sql(query, conn, params=(team_name,))
    conn.close()
    return df