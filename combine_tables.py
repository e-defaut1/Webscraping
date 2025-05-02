# combine_tables.py

import sqlite3
import pandas as pd
import sys

def combine_all_team_tables(
    db_path: str,
    output_table: str = "TeamStats_AllTeams",
    if_exists: str = "replace"
) -> None:
    """
    Combine all user-defined tables in the given SQLite database into one table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name "
        "  FROM sqlite_master "
        " WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [r[0] for r in cursor.fetchall()]

    if not tables:
        conn.close()
        raise RuntimeError("No user-defined tables found in the database.")

    frames = []
    for tbl in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM '{tbl}'", conn)
        except Exception as e:
            print(f"Warning: could not read table '{tbl}': {e}", file=sys.stderr)
            continue
        if df.empty:
            print(f"Notice: table '{tbl}' is empty; skipping.", file=sys.stderr)
            continue
        df["Team"] = tbl
        frames.append(df)

    if not frames:
        conn.close()
        raise RuntimeError("No tables contained any data to concatenate.")

    combined_df = pd.concat(frames, ignore_index=True)
    combined_df.to_sql(output_table, conn, if_exists=if_exists, index=False)
    conn.close()

    print(f"Combined {len(frames)} tables into '{output_table}'. "
          f"Total rows: {len(combined_df):,}.")

# If you still want to run as a standalone script, you can call this directly:
#if __name__ == "__main__":
#    combine_all_team_tables(db_path="NBA_25.db", output_table="TeamStats_AllTeams")