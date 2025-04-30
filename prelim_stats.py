import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1) ─── Load & Prep ────────────────────────────────────────────────────────────
DB_PATH   = "NBA_25.db"
TABLE     = "Lakers"

# pull the table
conn = sqlite3.connect(DB_PATH)
df   = pd.read_sql_query(f"SELECT * FROM {TABLE}", conn)
conn.close()

# parse dates
df['Date'] = pd.to_datetime(df['Date'])

# binary win flag
df['Win'] = (df['Rslt'] == 'W').astype(int)
#test line
print("test integer:")
print(df['Win'])
# extract home/away: that stray column (often unnamed) contains '@' when away
loc_col = [c for c in df.columns if df[c].isin(['@']).any()]
if loc_col:
    df['HomeAway'] = df[loc_col[0]].fillna('Home').replace({'@':'Away'})
else:
    df['HomeAway'] = 'Home'  # fallback if no such column

# helper to show a bar chart
def bar_plot(series, title, xlabel, ylabel='Win %', rotate=45):
    plt.figure(figsize=(6,4))
    vals = series.values * (100 if series.max()<=1 else 1)
    plt.bar(series.index.astype(str), vals)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=rotate, ha='right')
    plt.tight_layout()
    plt.show()

# 2) ───  Home vs. Away ─────────────────────────────────────────────────────────
home_pct = df.groupby('HomeAway')['Win'].mean()
bar_plot(home_pct, "Win % by Venue", "Venue")

# 3) - Opponent “Strength” Tiers via Rank → 3 fixed bins ────────────────────────
# 3-1) compute each opponent’s overall win rate
opp_win = df.groupby('Opp')['Win'].mean().sort_values()

# 3-2) turn that into a 0–1 percentile rank
ranks = opp_win.rank(method='average', pct=True)

# 3-3) cut those ranks into 3 equal slices
#    bins = [0, 1/3, 2/3, 1]  →  3 intervals → 3 labels
labels = ['Bottom','Mid','Top']
opp_tiers = pd.cut(
    ranks,
    bins=[0, 1/3, 2/3, 1],
    labels=labels,
    include_lowest=True
)

# 3-4) map back onto your main df
opp_tier_map = opp_tiers.to_dict()
df['OppTier'] = df['Opp'].map(opp_tier_map)

# 3-5) plot it
tier_pct = df.groupby('OppTier')['Win'].mean().reindex(labels)
bar_plot(tier_pct, "Win % vs Opponent Tier", "Opponent Tier")

# 4) ───  Rest Days ──────────────────────────────────────────────────────────────
df = df.sort_values('Date')
df['RestDays'] = df['Date'].diff().dt.days.fillna(0).astype(int)
bins = [ -1, 1, 3, 99 ]
labels = ['0–1 Days','2–3 Days','4+ Days']
df['RestBin'] = pd.cut(df['RestDays'], bins=bins, labels=labels)
rest_pct = df.groupby('RestBin', observed=True)['Win'].mean()
bar_plot(rest_pct, "Win % by Rest Days", "Rest Bin")

# 5) ───  Monthly Trends ─────────────────────────────────────────────────────────
df['Month'] = df['Date'].dt.month_name().str[:3]
month_order = ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep']
month_pct = df.groupby('Month', observed=True)['Win'].mean().reindex(month_order).dropna()
bar_plot(month_pct, "Win % by Month", "Month")

# 6) ───  Rolling 5‑Game Momentum ────────────────────────────────────────────────
df.set_index('Date', inplace=True)
rolling_win = df['Win'].rolling(5).mean()
rolling_eFG = df['FG%'].rolling(5).mean()

plt.figure(figsize=(8,4))
plt.plot(rolling_win.index, rolling_win, label='5‑Game Win%')
plt.plot(rolling_eFG.index, rolling_eFG, label='5‑Game eFG%')
plt.title("5‑Game Rolling Win% vs eFG%")
plt.xlabel("Date")
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
plt.legend()
plt.tight_layout()
plt.show()
df.reset_index(inplace=True)

# 7) ───  Feature Bins & Win% ────────────────────────────────────────────────────
# Example: eFG% bins
bins = [0, 0.48, 0.52, 1]
labels = ['<0.48','.48–.52','>0.52']
df['eFG_bin'] = pd.cut(df['FG%'], bins=bins, labels=labels)
bin_pct = df.groupby('eFG_bin', observed=True)['Win'].mean()
bar_plot(bin_pct, "Win % by eFG% Bin", "eFG% Bin")

# 8) ───  Two‑Way Pivot (eFG vs TOV bins) ────────────────────────────────────────
# turnover rate per shot
df['TOV_rate'] = df['TOV'] / df['FGA']
tov_bins = [0, 0.10, 0.15, 1]
tov_labels = ['<10%','10–15%','>15%']
df['TOV_bin'] = pd.cut(df['TOV_rate'], bins=tov_bins, labels=tov_labels)

pivot = df.pivot_table(
    index='eFG_bin',
    columns='TOV_bin',
    values='Win',
    aggfunc='mean',
     observed=True
).loc[labels, tov_labels]

plt.figure(figsize=(5,4))
plt.imshow(pivot, aspect='auto', vmin=0, vmax=1)
plt.colorbar(label='Win %')
plt.xticks(range(len(tov_labels)), tov_labels)
plt.yticks(range(len(labels)), labels)
plt.title("Win% by eFG% Bin vs TOV Rate Bin")
plt.xlabel("Turnover Rate")
plt.ylabel("eFG% Bin")
plt.tight_layout()
plt.show()