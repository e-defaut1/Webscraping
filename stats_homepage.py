# stats_homepage.py

import sqlite3
import pandas as pd

from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go

from combine_tables import combine_all_team_tables

DB_PATH      = "NBA_25.db"
MASTER_TABLE = "TeamStats_AllTeams"
SQL_FILE     = "avg_stats_query.sql"

# 0) Ensure combined table exists
combine_all_team_tables(DB_PATH, output_table=MASTER_TABLE)

# 1) Load team list
with sqlite3.connect(DB_PATH) as conn:
    df_teams = pd.read_sql(f"SELECT DISTINCT Team FROM {MASTER_TABLE}", conn)
teams = sorted(df_teams["Team"].tolist())

# 2) Load SQL template
with open(SQL_FILE, "r") as f:
    QUERY_TEMPLATE = f.read()

# 3) Build Dash app
app = Dash(__name__)
app.title = "NBA Team Comparison Dashboard"

app.layout = html.Div([
    html.H1("NBA Team Comparison Dashboard"),

    html.Div([
        html.Div([
            html.Label("Team A"),
            dcc.Dropdown(
                id="team-a-dropdown",
                options=[{"label": t, "value": t} for t in teams],
                value=teams[0],
                clearable=False,
            ),
        ], style={"width": "48%", "display": "inline-block"}),

        html.Div([
            html.Label("Team B"),
            dcc.Dropdown(
                id="team-b-dropdown",
                options=[{"label": t, "value": t} for t in teams],
                value=teams[1] if len(teams) > 1 else teams[0],
                clearable=False,
            ),
        ], style={"width": "48%", "display": "inline-block", "float": "right"}),
    ], style={"padding": "10px 0"}),

    html.Hr(),

    html.H3("Counting Metrics (values > 1)"),
    dcc.Graph(id="count-metrics-bar"),

    html.H3("Percentage Metrics (0–1 scale)"),
    dcc.Graph(id="pct-metrics-bar"),
])

# 4) Callback to update both charts
@app.callback(
    Output("count-metrics-bar", "figure"),
    Output("pct-metrics-bar",   "figure"),
    Input("team-a-dropdown",    "value"),
    Input("team-b-dropdown",    "value"),
)
def update_bars(team_a, team_b):
    def fetch_stats(team_name):
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql(
                QUERY_TEMPLATE,
                conn,
                params={"team_name": team_name}
            )

    # fetch aggregates
    df_a = fetch_stats(team_a)
    df_b = fetch_stats(team_b)

    # melt to long form
    long_a = df_a.melt(id_vars=["Team"], var_name="Stat", value_name="Value")
    long_b = df_b.melt(id_vars=["Team"], var_name="Stat", value_name="Value")

    # split by threshold (1.0)
    count_a = long_a[long_a["Value"] > 1]
    count_b = long_b[long_b["Value"] > 1]

    pct_a   = long_a[(long_a["Value"] <= 1) & (long_a["Value"] >= 0)]
    pct_b   = long_b[(long_b["Value"] <= 1) & (long_b["Value"] >= 0)]

    # ① Counting metrics chart
    trace_ca = go.Bar(
        name=team_a,
        x=count_a["Stat"],
        y=count_a["Value"],
        marker_color="darkblue",
    )
    trace_cb = go.Bar(
        name=team_b,
        x=count_b["Stat"],
        y=count_b["Value"],
        marker_color="firebrick",
    )
    fig_count = go.Figure(data=[trace_ca, trace_cb])
    fig_count.update_layout(
        barmode="group",
        xaxis_tickangle=-45,
        xaxis_title="Metric",
        yaxis_title="Value",
        margin=dict(t=40, b=150),
    )

    # ② Percentage metrics chart
    trace_pa = go.Bar(
        name=team_a,
        x=pct_a["Stat"],
        y=pct_a["Value"],
        marker_color="darkblue",
    )
    trace_pb = go.Bar(
        name=team_b,
        x=pct_b["Stat"],
        y=pct_b["Value"],
        marker_color="firebrick",
    )
    fig_pct = go.Figure(data=[trace_pa, trace_pb])
    fig_pct.update_layout(
        barmode="group",
        xaxis_tickangle=-45,
        xaxis_title="Metric",
        yaxis_title="Value (0–1)",
        margin=dict(t=40, b=150),
    )

    return fig_count, fig_pct


if __name__ == "__main__":
    app.run(debug=True)