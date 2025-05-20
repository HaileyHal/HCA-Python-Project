import pandas as pd
hca = pd.read_csv("CoordHCA.csv")
hca = hca.dropna(subset=["latitude"])
hca = hca.dropna(subset=["longitude"])
hca = hca.dropna(subset=["facility_zip"])


nan_count = hca['longitude'].isna().sum()
print(nan_count)

hca.to_csv(f'CoordHCA.csv', index=False) # saving csv -- might not actually need
