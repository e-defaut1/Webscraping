-- avg_stats_query.sql

WITH 
  -- 1) Pull just the columns we need and rename Opp.1 to OpponentPoints
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
      Team = :team_name
      AND Date IS NOT NULL
      AND Date <> ''
  ),

  -- 2) Build a synthetic GameID per team+game (Date+Opponent)
  distinct_games AS (
    SELECT
      Team,
      Date || ' vs ' || Opponent AS GameID
    FROM games
    GROUP BY Team, Date, Opponent
  )

-- 3) Aggregate per team
SELECT
  g.Team,
  COUNT(*)                           AS GamesPlayed,
  ROUND(AVG(CASE WHEN g.TeamPoints > g.OpponentPoints THEN 1.0 ELSE 0.0 END),3)
                                     AS WinPct,
  ROUND(AVG(g.TeamPoints),1)        AS AvgPtsFor,
  ROUND(AVG(g.OpponentPoints),1)    AS AvgPtsAgainst,
  ROUND(AVG(g.TwoP_Perc),3)         AS Avg_2P_Perc,
  ROUND(AVG(g.ThreeP_Perc),3)       AS Avg_3P_Perc,
  ROUND(AVG(g.TotalRebounds),1)     AS Avg_TRB,
  ROUND(AVG(g.Steals),1)            AS Avg_STL,
  ROUND(AVG(g.Turnovers),1)         AS Avg_TOV,
  ROUND(AVG(g.Opp_TwoP_Perc),3)      AS Opp_Avg_2P_Perc,
  ROUND(AVG(g.Opp_ThreeP_Perc),3)    AS Opp_Avg_3P_Perc,
  ROUND(AVG(g.Opp_TotalRebounds),1)  AS Opp_Avg_TRB,
  ROUND(AVG(g.Opp_Steals),1)         AS Opp_Avg_STL,
  ROUND(AVG(g.Opp_Turnovers),1)      AS Opp_Avg_TOV
FROM games AS g
JOIN distinct_games AS d 
  ON g.Team = d.Team
 AND g.Date || ' vs ' || g.Opponent = d.GameID
GROUP BY g.Team;