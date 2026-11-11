from pathlib import Path
import pandas as pd
import sqlite3

DATA_DIR = Path('../01_DATA_RAW')
DB = 'project_11_dwh.db'
con = sqlite3.connect(DB)
files = {
    'locations': DATA_DIR / 'locations.csv',
    'workers_synthetic': DATA_DIR / 'workers_synthetic.csv',
    'incidents': DATA_DIR / 'incidents.csv',
    'safety_observations': DATA_DIR / 'safety_observations.csv',
    'equipment': DATA_DIR / 'equipment.csv',
}

# STEP 1 - RAW: load sources without business transformation
for name, path in files.items():
    df = pd.read_csv(path)
    df.to_sql('raw_' + name, con, index=False, if_exists='replace')
    print(name, len(df))

# TODO STEP 2 - STAGING: typing, standardization, duplicates, rejects
# TODO STEP 3 - CORE: dimensions + facts
# TODO STEP 4 - MART: KPI-ready tables
# TODO STEP 5 - reconciliation and monitoring metrics
con.close()
