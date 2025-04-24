import pandas as pd
hca = pd.read_csv("CoordHCA.csv")

destinationZip = int(input("What is your facility zipcode? (Chelsea/TAs please use 77004. This is a Houston Hospital Facility): ")) # determining what hospital we are going to
empCount = hca.groupby("facility_zip")["Emp34Id"].nunique() # grouping by hospital and counting emp ID
neededEmps = empCount.get(destinationZip) # filtering by inputted location- value is total emps at one hospital location

# 10%-50% of employees are needed to fill an affected hospital, depending on size
hurricaneLvl = int(input("What is the incoming hurricane level? (1-5): "))
if hurricaneLvl == 1: # Make depending on hurricane level
    neededEmps *= 0.1
elif hurricaneLvl == 2:
    neededEmps *= 0.2
elif hurricaneLvl == 3:
    neededEmps *= 0.3
elif hurricaneLvl == 4:
    neededEmps *= 0.4
elif hurricaneLvl == 5:
    neededEmps *= 0.5
neededEmps = round(neededEmps, 0) # change to round
print(f"You will need {neededEmps} employees brought in.")

destination = input("What is your destination airport? Please enter the airport code: (Chelsea/Tas please use HOU. This is the Houston Airport Code): ")

# use API to search all flight prices for that day
import requests
from datetime import date
import json
today = date.today() # updates for daily flight price information

api_key = "a202ac4bd0b994e0eaaeed61cf95d6e60627ffcc91a233904027d467ee56c8b4"
departure_airports = ["SLC", "LAX", "DFW"] # USE THIS FOR TESTING
# departure_airports = ["ANC", "SJC", "OXR", "SFO", "OAK", "LAX", "ONT", "PSP", "LAS", "BOI", "IDA", "SLC", "DEN", "ELP", "ITC", "MCI", "DAL", "DFW", "AUS", "GRK", "CRP", "IAH", "HOU", "AEX", "MSY", "PIB", "PNS", "VPS", "PFN", "TLH", "PIE", "TPA", "SRQ", "GNV", "JAX", "DAB", "MLB", "MCO", "RSW", "PBI", "FLL", "MIA", "ATL", "AGS", "SAV", "BQK", "VLD", "MCN", "CHS", "CHA", "BNA", "GSO", "RDU", "TRI", "TYS", "CLT", "ROA", "LYH", "LWB", "RIC", "PHF", "CHO", "DCA", "IAD", "BWI", "LEX", "IND", "CMI", "MHT", "BOS"]
all_prices = {} # setting this empty dictionary for later 

for origin in departure_airports: # looping through each origin/departure airport 
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "gl": "us", # only domestic flights
        "type": 2, # one way flights
        "outbound_date": today, #UPDATING the API
        "api_key": api_key,
        "sort_by": 2 # sorting output by price
    }

    try: # what I want to happen
        response = requests.get("https://serpapi.com/search", params=params) # connecting to the API (web request)
        data = response.json() # creating a dictionary from web request

        if data.get("error"): # Skip if API returned an error
            print(f"API error for {origin}: {data['error']}")
            continue

        flights = data.get("other_flights", []) # finding other flights in data - grabbing the right subset

        if flights == []: # if no flight found, continue to the next airport code
            continue # error airports that have no route happens here
            # check for data.get("error", []) exists, or doesn't equal [] and then go to next origin

        all_prices[origin] = [] # empty list for each origin code
        
        for flight in flights: # for each origin/departure airport:
            price = flight.get("price") # grabbing the price for that flight
            if price: # assuming there is a price
                all_prices[origin].append(price) # because I am appending I can only run this once a day to get daily updates, or I need to delete the old json.prices so I don't have double
                with open("prices.json", "a") as f: # saving to my json file
                    json.dump({"origin": origin, "destination": destination, "price": price}, f)
                    f.write("\n")
            
            if price == []: # assuming there is no price to be found
                print("no valid price found")
                continue
                    
            if all_prices[origin]: # Only calculate average if we collected prices
                avg_price = round(sum(all_prices[origin]) / len(all_prices[origin]), 2) # rewriting all_prices to include the average rounded to 2 decimals
                all_prices[origin] = avg_price # resetting all_prices value to be just the average price instead of the list
                print(f"The average price for {origin} to {destination} on {today} is ${avg_price}")
            else:
                del all_prices[origin]  # Clean up empty entries

    except Exception as e: # error handling
        pass #just skip to the next departure airport. 
        # print(f"Error message: {e}") # printing the error message. I think it runs each time, for whatever reason. I leave it up so I can see when I run out of API calls 
    # makes a json file that includes origin, destination, and price


# clean json file and add latitude and longitude coordinates
airports = pd.read_csv("airports.csv")

df = pd.read_json("prices.json", lines=True) # reading the json to df to alter

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

newdf.to_csv(f"flightpricesfor{today}latlong.csv", index=False) # saving csv 


# mapping and while loop to print final results
from geopy import distance 

# newdf = pd.read_csv(f"flightpricesfor{today}latlong.csv") # can also probably delete once merged

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
