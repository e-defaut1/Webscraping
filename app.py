# app.py
import sqlite3
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.calibration import calibration_curve

import plotly.graph_objs as go

from dash import Dash, dcc, html, Input, Output

# your helper that combines 30 tables into TeamStats_AllTeams
from combine_tables import combine_all_team_tables
# your prelim stats function (should return a DataFrame summary by team)
from prelim_stats import get_prelim_stats_df

# ─── 0) combine tables on start (if not already done) ────────────────────────────
combine_all_team_tables("NBA_25.db", output_table="TeamStats_AllTeams")

# ─── 1) Load full-season data from SQLite ────────────────────────────────────────
DB_PATH    = "NBA_25.db"
TABLE_NAME = "TeamStats_AllTeams"

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)

# Drop any rows missing Opponent (if invalid)
df = df[df["Opp"].notna()]

# ─── 2) Derive binary Win & the point Margin ─────────────────────────────────────
# assume your columns for team points and opponent points are named Tm and Opp.1:
df["Win"]    = (df["Tm"] > df["Opp.1"]).astype(int)
df["Margin"] = df["Tm"] - df["Opp.1"]

# ─── 3) Prepare feature matrix & targets ────────────────────────────────────────
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
exclude  = ["Win", "Margin"]
features = [c for c in num_cols if c not in exclude]

X_full     = df[features].fillna(0)
y_win      = df["Win"]
y_margin   = df["Margin"]

# ─── 4) Train scikit‑learn models once at startup ────────────────────────────────
logit = LogisticRegression(max_iter=1000)
logit.fit(X_full, y_win)

linreg = LinearRegression()
linreg.fit(X_full, y_margin)

# residuals for histogram
resids    = y_margin - linreg.predict(X_full)

# calibration curve (global)
prob_true, prob_pred = calibration_curve(
    y_win,
    logit.predict_proba(X_full)[:, 1],
    n_bins=10,
)

# pull unique team list
teams = sorted(df["Team"].unique())

# ─── 5) get_team_features helper ────────────────────────────────────────────────
def get_team_features(team_name):
    """
    Return a 1×k DataFrame (with column names = features)
    containing the season‐average stats of one team.
    """
    sub = df[df["Team"] == team_name][features]
    avg = sub.mean().to_frame().T
    return avg.fillna(0)

# ─── 6) Build Dash app ─────────────────────────────────────────────────────────
app = Dash(__name__)
app.layout = html.Div([
    html.H1("NBA Win‑Prob & Spread Dashboard"),

    # Team selectors
    html.Div([
        html.Div([
            html.Label("Team A:"),
            dcc.Dropdown(
                id="team-a",
                options=[{"label": t, "value": t} for t in teams],
                value=teams[0],
            ),
        ], style={"width": "48%", "display": "inline-block"}),

        html.Div([
            html.Label("Team B:"),
            dcc.Dropdown(
                id="team-b",
                options=[{"label": t, "value": t} for t in teams],
                value=teams[1],
            ),
        ], style={"width": "48%", "display": "inline-block", "float": "right"}),
    ]),

    # Row of graphs
    html.Div([
        html.Div(dcc.Graph(id="win-prob-gauge"), style={"width": "48%", "display": "inline-block"}),
        html.Div(dcc.Graph(id="spread-hist"),    style={"width": "48%", "display": "inline-block", "float": "right"}),
    ]),

    # Calibration curve (static)
    html.H3("Calibration Curve (Logistic Model)"),
    dcc.Graph(
        id="calibration-curve",
        figure=go.Figure([
            go.Scatter(x=prob_pred, y=prob_true, mode="lines+markers", name="Calibration"),
            go.Scatter(x=[0,1], y=[0,1], mode="lines", line=dict(dash="dash"), name="Perfect"),
        ]).update_layout(
            xaxis_title="Predicted P(win)",
            yaxis_title="Empirical P(win)",
        )
    ),

    # Prelim stats for each team
    html.H3("Season‑to‑Date Summary"),
    html.Div([
        html.Div(id="prelim-a", style={"width": "48%", "display": "inline-block"}),
        html.Div(id="prelim-b", style={"width": "48%", "display": "inline-block", "float": "right"}),
    ]),
])

# ─── 7) Callbacks ───────────────────────────────────────────────────────────────
@app.callback(
    Output("win-prob-gauge", "figure"),
    Output("spread-hist",    "figure"),
    Output("prelim-a",       "children"),
    Output("prelim-b",       "children"),
    Input("team-a", "value"),
    Input("team-b", "value"),
)
def update_figs(team_a, team_b):
    # ── A) get season averages as DataFrame so names line up ─────────────────
    fa = get_team_features(team_a)
    fb = get_team_features(team_b)

    # ── B) predict probabilities and margins ────────────────────────────────
    p_a = logit.predict_proba(fa)[0, 1]     # P(Team A wins)
    p_b = 1.0 - p_a                         # P(Team B wins)
    m_a = linreg.predict(fa)[0]            # expected margin for A 

    # ── C) Win‑prob gauge ───────────────────────────────────────────────────
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=100 * p_a,
        title={"text": f"Win Prob: {team_a} vs {team_b}"},
        gauge={
            "axis": {"range": [0, 100], "tickformat": "%"},
            "bar":  {"color": "darkblue"},
            "steps":[
                {"range": [0, 50],  "color": "#ffcccc"},
                {"range": [50, 100], "color": "#ccffcc"},
            ],
        }
    ))

    # ── D) Spread‑residual histogram ────────────────────────────────────────
    counts, bins = np.histogram(resids, bins=30)
    max_count   = counts.max()

    hist = go.Figure()
    hist.add_trace(go.Bar(
        x=bins[:-1],
        y=counts,
        name="Residuals"
    ))
    hist.add_trace(go.Scatter(
        x=[m_a, m_a],
        y=[0, max_count],
        mode="lines",
        line=dict(color="red", dash="dash"),
        name=f"Predicted Margin={m_a:.1f}"
    ))
    hist.update_layout(
        title      = f"Spread Residuals & Predicted Margin for {team_a}",
        xaxis_title= "Actual − Predicted Margin",
        yaxis_title= "Count",
    )

    # ── E) Prelim stats tables ───────────────────────────────────────────────
    # get_prelim_stats_df should return a DataFrame with your summary stats
    prelim_a_df = get_prelim_stats_df(team_a)
    prelim_b_df = get_prelim_stats_df(team_b)

    # render as simple html table
    def df_to_table(df):
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(len(df))
            ])
        ], style={"border": "1px solid #ccc", "margin": "5px"})

    prelim_a = html.Div([
        html.H4(team_a),
        df_to_table(prelim_a_df)
    ])
    prelim_b = html.Div([
        html.H4(team_b),
        df_to_table(prelim_b_df)
    ])

    return gauge, hist, prelim_a, prelim_b

# ─── 8) Run server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)