import pandas as pd
import json
from datetime import date
today = date.today()

df = pd.read_json("prices.json", lines=True) # reading the json to df to alter
airports = pd.read_csv("airports.csv")

newdf = df.merge(airports[['IATA', 'LATITUDE', 'LONGITUDE']], # adding origin lat and long to df file
                 left_on='origin',
                 right_on='IATA',
                 how='left')
newdf = newdf.rename(columns={"LATITUDE": "OriginLat"}) #renaming for clarity
newdf = newdf.rename(columns={"LONGITUDE": "OriginLong"})

newdf = newdf.merge(airports[['IATA', 'LATITUDE', 'LONGITUDE']], # adding destination lat and long to df file
                 left_on='destination',
                 right_on='IATA',
                 how='left')
newdf = newdf.rename(columns={"LATITUDE": "DestinationLat"})# renaming for clarity
newdf = newdf.rename(columns={"LONGITUDE": "DestinationLong"})

newdf = newdf.drop(columns=["IATA_x", "IATA_y"]) # dropping extra added columns from merge


df.to_csv(f'flightdatafor{today}.csv', index=False) # saving csv 


