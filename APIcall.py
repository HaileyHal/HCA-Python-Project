# for TAs/Chelsea: Please be careful when running this. I have a very limited number of API calls I can use for this, 
# so it is likely I will run out if you run it multiple times. Enjoy!

import requests
from datetime import date
import json

today = date.today() # updates for daily flight price information
destination = "HOU" 

api_key = "a202ac4bd0b994e0eaaeed61cf95d6e60627ffcc91a233904027d467ee56c8b4"
# departure_airports = ["SLC", "LAX", "LAS"] # USE THIS FOR TESTING
departure_airports = ["ANC", "SJC", "OXR", "SFO", "OAK", "LAX", "ONT", "PSP", "LAS", "BOI", "IDA", "SLC", "DEN", "ELP", "ITC", "MCI", "DAL", "DFW", "AUS", "GRK", "CRP", "IAH", "HOU", "AEX", "MSY", "PIB", "PNS", "VPS", "PFN", "TLH", "PIE", "TPA", "SRQ", "GNV", "JAX", "DAB", "MLB", "MCO", "RSW", "PBI", "FLL", "MIA", "ATL", "AGS", "SAV", "BQK", "VLD", "MCN", "CHS", "CHA", "BNA", "GSO", "RDU", "TRI", "TYS", "CLT", "ROA", "LYH", "LWB", "RIC", "PHF", "CHO", "DCA", "IAD", "BWI", "LEX", "IND", "CMI", "MHT", "BOS"]
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
                all_prices[origin].append(price)
                with open("prices.json", "a") as f:
                    json.dump({"origin": origin, "destination": destination, "price": price}, f)
                    f.write("\n")
            
            if price == []: # assuming there is no price to be found
                print("no valid price found")
                continue
                    
            if all_prices[origin]: # Only calculate average if we collected prices
                avg_price = round(sum(all_prices[origin]) / len(all_prices[origin]), 2) # rewriting all_prices to include the average rounded to 2 decimals
                all_prices[origin] = avg_price # resetting all_prices value to be just the average price instead of the list
                print(f"Great job! The average price for {origin} to {destination} on {today} is {avg_price}")
            else:
                del all_prices[origin]  # Clean up empty entries

    except Exception as e: # error handling
        #npass #just skip to the next departure airport. most of the errors are caused bc there is no flight from that airport
        print(f"Error message: {e}") # printing the error message. I think it runs each time, for whatever reason. I leave it up so I can see when I run out of API calls 

    
with open("prices2.json", "a") as f: # Write each price to a JSON file
    json.dump({"origin": origin, "destination": destination, "price": price}, f)
    f.write("\n")  # Newline-delimited JSON entries
