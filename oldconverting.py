import pandas as pd
from datetime import date
import json
today = date.today()

df = pd.read_json("prices.json", lines=True)
df.to_csv(f'flightdatafor{today}.csv', index=False)
