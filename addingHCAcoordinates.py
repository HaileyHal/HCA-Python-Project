 
import pandas as pd # can delete once merged
import numpy
import pgeocode

airports = pd.read_csv("airports.csv")
hca = pd.read_csv(
    "deidentified_hca_employees (1).csv",
    dtype={9: str},  # Target ZIP code column
    usecols=lambda col: col not in {  # Pre-filter columns during read
        "EmpProcessLevelDesc", "EmpLegCoid", 
        "EmpAnnivDate", "EmpPositionIsSuper", "MgrName"
    }
)
hca = hca.dropna(subset=["facility_zip"]) # dropping all rows where the zip doesn't exist
hca["facility_zip"] = hca["facility_zip"].astype(str).str.strip().str.extract(r'(\d{5})')[0]  # Clean and standardize zipcode 
nomi = pgeocode.Nominatim('us') # Batch Geocoding
coords = nomi.query_postal_code(hca["facility_zip"].tolist())[['latitude', 'longitude']] # pulling lat and long
hca = pd.concat([hca.reset_index(drop=True), coords.reset_index(drop=True)], axis=1) # Efficient Merge

hca.to_csv(f'CoordHCA.csv', index=False) # saving csv -- might not actually need
