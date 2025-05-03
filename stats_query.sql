-- stats_query.sql
WITH 
  -- 1) Pull just the columns we need, rename Opp.1 -> OpponentPoints
  games AS (
    SELECT
      Team,
      Date,
      Opp                   AS Opponent,
      Tm                    AS TeamPoints,
      "Opp.1"               AS OpponentPoints,
      "2P%"                 AS TwoP_Perc,
      "3P%"                 AS ThreeP_Perc,
      TRB                   AS TotalRebounds,
      STL                   AS Steals,
      TOV                   AS Turnovers,
      "2P%.1"               AS Opp_TwoP_Perc,
      "3P%.1"               AS Opp_ThreeP_Perc,
      "TRB.1"               AS Opp_TotalRebounds,
      "STL.1"               AS Opp_Steals,
      "TOV.1"               AS Opp_Turnovers
    FROM TeamStats_AllTeams
    WHERE 
      Team IN ('Bucks','Bulls')     -- ← SUB in your team list here
      AND Date IS NOT NULL
      AND Date <> ''
  )

SELECT
  Team,
  Date,
  Opponent,
  TeamPoints,
  OpponentPoints,
  TwoP_Perc,
  ThreeP_Perc,
  TotalRebounds,
  Steals,
  Turnovers,
  Opp_TwoP_Perc,
  Opp_ThreeP_Perc,
  Opp_TotalRebounds,
  Opp_Steals,
  Opp_Turnovers
FROM games
ORDER BY Team, Date;