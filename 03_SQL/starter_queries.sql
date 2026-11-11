-- Project 11: Port Safety & Incident Analytics
-- TODO 1: count each source table
-- TODO 2: at least 3 JOIN queries
-- TODO 3: at least 2 GROUP BY KPI queries
-- TODO 4: one CTE
-- TODO 5: identify a Data Warehouse grain and validate source uniqueness

SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
