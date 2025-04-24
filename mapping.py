import pandas as pd
from geopy import distance 
from datetime import date # can delete later (leave the one at the top)
# import geopandas as gpd # not sure I need this, but I will leave it anyway
today = date.today()

neededEmps = 252 # delete after merge, for testing purposes

# new mapping attempt
hca = pd.read_csv("CoordHCA.csv") # can delete once merged
newdf = pd.read_csv(f"flightpricesfor{today}latlong.csv") # can also probably delete once merged

prices_sorted = newdf.sort_values(["destination", "price"], ascending=[True,True]) # prints all origins and the destination sorted by price
# cheapest_prices = prices_sorted.groupby("destination").first().reset_index() # only prints out one origin and destination --- might need to delete

def withinRadius(OriginLat, OriginLong, radius_miles=50): # returns a df with hospitals that are within the radius of the given airport coordinates
    def isWithin(hospital_row): # hospital row - a row from the hospital's df
        hosLocation = (hospital_row["latitude"], hospital_row["longitude"]) # location is the lat and long of the hospital coords 
        airportLocation = (OriginLat, OriginLong) # lat and long of the airport origin
        return distance.distance(hosLocation, airportLocation).miles <= radius_miles # checking if it is within 50
    # print(hca[hca.apply(isWithin, axis=1)].to_string())
    return hca[hca.apply(isWithin, axis=1)] # when the function is called, return only hospitals within the radius (true/false)

totalPrice = 0 # total price for employees flying through selected airport
finalPrice = 0 # price for all employees through all airports


for index, row in prices_sorted.iterrows(): # this will look at one origin airport at a time, looking at the top one first, bc they were sorted by price before
    while neededEmps > 0: # while more employees are needed, this will run 
        radiusHos = withinRadius(row["OriginLat"], row["OriginLong"]) #new df containing every employee that works at a hospital within the radius
        radiusEmps = sum(radiusHos.groupby("facility_zip")["Emp34Id"].nunique()) # sum of all employees that are within the 50 mile radius of the airport
        totalAvEmps = radiusEmps * 0.1 # total number of employees available through the selected airport (10% of emps is industry standard)
        totalAvEmps = round(totalAvEmps, 0) # rounding
        print(f"There are {totalAvEmps} employees available from {row['origin']}.")
    
        if neededEmps > totalAvEmps: # if the destination hospital needs more emps than what was available
            totalPrice = totalAvEmps * row["price"]
            print(f"You need {totalAvEmps} employees from the {row['origin']} airport. This will cost ${totalPrice}.")
            neededEmps = neededEmps - totalAvEmps # updating neededEmps
        elif neededEmps < totalAvEmps: # if there are more available emps than are needed
            totalAvEmps = neededEmps # making available emps equal to needed so we don't pull in extra employees
            totalPrice = totalAvEmps * row["price"]
            print(f"You need {totalAvEmps} employees from the {row['origin']} airport. This will cost ${totalPrice}.")
            neededEmps = neededEmps - totalAvEmps # updating neededEmps
        
        response = input("Would you like to see which hospitals these employees are coming from? (Y/N): ") # for project purposes: allowing hospital managers to see what hospitals specifically they can pull from
        if response == "Y":
            print(f"These are the hospitals within 50 miles of the {row['origin']} airport, and how many employees work at each one:")
            print(radiusHos.groupby("facility_zip")["Emp34Id"].nunique()) # showing hospital zips and how many emps they have
            # show zipcodes and counts. tell them they can decide how to disperse. 
        if response == "N":
            pass

        finalPrice += totalPrice # adding each origin airport price to the total

print(f"Your total cost is ${finalPrice}.")


# test = withinRadius(40.78838778,-111.9777731) # showing what hospitals are within 50 miles of this radius, wich is SLC
# test.to_csv("mapTest.csv") # printing to csv to see what it loks like

# save results to a json again?? 

# FINAL DF GOAL:
# destination airport, needed emps, origin airport, hospital id, available emps, distance to origin airport, flight price
# I need to make one cohesive DF so I can more easily filter through my while loop
