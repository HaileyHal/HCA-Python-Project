
import os
from dotenv import load_dotenv

import tkinter as tk
from customtkinter import CTk, CTkButton, CTkLabel, CTkEntry, CTkComboBox

from datetime import date

import pandas as pd
import requests

import json
from geopy import distance

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================
# Reading in file of HCA Employees
hca = pd.read_csv('CoordHCA.csv')

load_dotenv()
api_key = os.getenv('API_KEY')

departure_airports = ['SLC', 'LAX', 'DFW', 'HOU'] # USE THIS FOR TESTING
# departure_airports = ['ANC', 'SJC', 'OXR', 'SFO', 'OAK', 'LAX', 'ONT', 'PSP', 'LAS', 'BOI',
#                       'IDA', 'SLC', 'DEN', 'ELP', 'ITC', 'MCI', 'DAL', 'DFW', 'AUS', 'GRK',
#                       'CRP', 'IAH', 'HOU', 'AEX', 'MSY', 'PIB', 'PNS', 'VPS', 'PFN', 'TLH',
#                       'PIE', 'TPA', 'SRQ', 'GNV', 'JAX', 'DAB', 'MLB', 'MCO', 'RSW', 'PBI',
#                       'FLL', 'MIA', 'ATL', 'AGS', 'SAV', 'BQK', 'VLD', 'MCN', 'CHS', 'CHA',
#                       'BNA', 'GSO', 'RDU', 'TRI', 'TYS', 'CLT', 'ROA', 'LYH', 'LWB', 'RIC',
#                       'PHF', 'CHO', 'DCA', 'IAD', 'BWI', 'LEX', 'IND', 'CMI', 'MHT', 'BOS']

today = date.today()  # Updates for daily flight price information


def submit():
    '''
    This method will calculate the number of needed employess, and then display that on the GUI.
    '''
    emp_count = hca.groupby("facility_zip")["Emp34Id"].nunique()  # Grouping by hospital and counting emp ID
    
    destination_zip = destination_zip_var.get()
    destination_zip = int(destination_zip)
    needed_emps = emp_count.get(destination_zip)  # Total emps at one hospital location

    # 10%-50% of employees are needed to fill an affected hospital, depending on size
    hurricane_level = hurricane_level_var.get()
    hurricane_level = int(hurricane_level)
    if hurricane_level == 1:
        needed_emps *= 0.1
    elif hurricane_level == 2:
        needed_emps *= 0.2
    elif hurricane_level == 3:
        needed_emps *= 0.3
    elif hurricane_level == 4:
        needed_emps *= 0.4
    elif hurricane_level == 5:
        needed_emps *= 0.5
    needed_emps = int(round(needed_emps, 0))
    emp_count_label.configure(text=f'You will need {needed_emps} employees brought in.')
    airport_code_label.configure(text='What is the destination airport code?')
    submit_button.grid_forget()
    airport_code_dropdown.grid()
    find_employees_button.grid()
    root.update()

def find_employees():
    '''
    This method will run the rest of the backend code, searching for available
    employees and where they come from.
    '''
    airport_code = airport_code_var.get()
    all_prices = {}  # Setting this empty dictionary for later 

    for origin in departure_airports:  # Looping through each origin/departure airport 
        params = {
            'engine': 'google_flights',
            'departure_id': origin,
            'arrival_id': airport_code,
            'gl': 'us',  # Only domestic flights
            'type': 2,  # One way flights
            'outbound_date': today,  # UPDATING the API daily
            'api_key': api_key,
            'sort_by': 2  # Sorting output by price
        }

        try:
            response = requests.get('https://serpapi.com/search', params=params)
            data = response.json()  # Creating a dictionary from web request

            if data.get('error'):  # Skip if API returned an error
                print(f'API error for {origin}: {data["error"]}')
                continue

            flights = data.get('other_flights', [])  # Grabbing the right subset of data

            if flights == []:  # If no flight found, continue to the next airport code
                continue  # Error airports that have no route happens here

            all_prices[origin] = []  # Empty list for each origin code
            
            for flight in flights:
                price = flight.get('price')
                if price:
                    all_prices[origin].append(price)
                    with open('prices.json', 'a') as f:
                        json.dump({'origin': origin, 'destination': airport_code,
                                   'price': price}, f)
                        f.write('\n')

                if price == []:  # If there is no price to be found
                    print('No valid price found.')
                    continue

                # Rewriting all_prices to include the daily average rounded to 2 decimals
                if all_prices[origin]:
                    avg_price = round(sum(all_prices[origin]) / len(all_prices[origin]), 2)
                    # Resetting all_prices value to be just the average price instead of the list
                    all_prices[origin] = avg_price
                else:
                    del all_prices[origin]  # Clean up empty entries

        except Exception as e: # error handling
            pass #just skip to the next departure airport. 
    cleaning_prices()

def cleaning_prices():
    '''
    This method will take our json file of prices and clean it,
    adding lat and long for later mapping.
    '''
    airports_df = pd.read_csv('airports.csv')

    prices_df = pd.read_json('prices.json', lines=True)  # Reading the json to df

    # Adding origin/destination lat and long to df file and renaming for clarity
    newdf = prices_df.merge(airports_df[['IATA', 'LATITUDE', 'LONGITUDE']],
                    left_on='origin',
                    right_on='IATA',
                    how='left')
    newdf = newdf.rename(columns={'LATITUDE': 'origin_lat'})
    newdf = newdf.rename(columns={'LONGITUDE': 'origin_long'})

    newdf = newdf.merge(airports_df[['IATA', 'LATITUDE', 'LONGITUDE']],
                    left_on='destination',
                    right_on='IATA',
                    how='left')
    newdf = newdf.rename(columns={'LATITUDE': 'destination_lat'})
    newdf = newdf.rename(columns={'LONGITUDE': 'destination_long'})

    newdf = newdf.drop(columns=['IATA_x', 'IATA_y']) 
    filename = f'flight prices for {today}.csv'
    newdf.to_csv(filename, index=False)
    # DELETE prices.json HERE to avoid duplication

def find_airports(filename):
    '''
    This is the mapping method that calculates how many employees are available
    at the hospitals with the cheapest correlating flight.
    '''
    newdf = pd.read_csv(filename)
    prices_sorted_df = newdf.sort_values(['destination', 'price'], ascending=[True,True])

    def within_radius(origin_lat, origin_long, radius_miles=50):
        '''
        This method returns a df with hospitals that are within the radius of the given
        airport coordinates
        '''
        distances = hca.apply(lambda row: distance.distance(
            (row['latitude'], row['longitude']),
            (origin_lat, origin_long)).miles, axis=1)
        
        return hca[distances <= radius_miles]
    
    total_airport_price = 0  # Total price for employees flying through each needed airport
    final_price = 0  # Price for all employees through all airports

    for index, row in prices_sorted_df.iterrows():  # Sorting through cheaper origin airports
        while needed_emps > 0:
            # Sum of all employees that are within the 50 mile radius of the airport
            radius_hos = within_radius(row['origin_lat'], row['origin_long'])
            radius_emps = sum(radius_hos.groupby('facility_zip')['Emp34Id'].nunique())
            total_available_emps = radius_emps * 0.1
            total_available_emps = round(total_available_emps, 0)
            # print(f'There are {total_available_emps} employees available from {row['origin']}.')
    
            if needed_emps > total_available_emps:
                total_airport_price = total_available_emps * row['price']
                print(f'You need {total_available_emps} employees from the {row['origin']} \
                      airport. This will cost ${total_airport_price}.')
                needed_emps = needed_emps - total_available_emps
            elif needed_emps < total_available_emps:
                total_available_emps = needed_emps  # Avoiding pulling extra employees
                total_airport_price = total_available_emps * row['price']
                print(f'You need {total_available_emps} employees from the {row['origin']} \
                      airport. This will cost ${total_airport_price}.')
                needed_emps = needed_emps - total_available_emps # updating neededEmps
            
            response = input('Would you like to see which hospitals these employees are \
                             coming from? (Y/N): ')
            if response == 'Y':
                print(f'These are the hospitals within 50 miles of the {row['origin']} airport, \
                      and how many employees work at each one:')
                print(radius_hos.groupby('facility_zip')['Emp34Id'].nunique())

            if response == 'N':
                pass

            final_price += total_airport_price # adding each origin airport price to the total
    total_price_label.configure(text=f'Your total cost is ${final_price}.')


# =============================================================================
# TKINTER PROGRAM
# =============================================================================
root = CTk()
root.geometry('800x700')
root.title("Healthcare Hurricane Portal") #titling window
destination_zip_var=tk.StringVar()
hurricane_level_var=tk.IntVar()
airport_code_var=tk.StringVar()

# =============================================================================
# TKINTER WIDGETS
# =============================================================================
zip_label = CTkLabel(root, text='Hospital Zipcode:', font=('Arial',20), text_color='#04033A')
zip_entry = CTkEntry(root, textvariable=destination_zip_var, font=('Arial',20), text_color='#04033A')
hurricane_label = CTkLabel(root, text='Select Incoming Hurricane Level:', font=('Arial',20),
                           text_color='#04033A')
hurricane_dropdown = CTkComboBox(root, variable=hurricane_level_var, values=['1','2','3','4','5'],
                                 font=('Arial',20), text_color='#04033A')
submit_button = CTkButton(root, text='Submit', command=submit, corner_radius=32)

emp_count_label = CTkLabel(root, text='', font=('Arial',20))

airport_code_label = CTkLabel(root, text='', font=('Arial',20))
airport_code_dropdown = CTkComboBox(root, variable=airport_code_var, values=departure_airports,
                                    font=('Arial',20))
airport_code_dropdown.grid_forget()

find_employees_button = CTkButton(root, text='Find Employees', command=find_employees,
                                  corner_radius=32)
total_price_label = CTkLabel(root, text='', font=('Arial',20))

# =============================================================================
# TKINTER GRID AND APP START
# =============================================================================
zip_label.grid()
zip_entry.grid()
hurricane_label.grid()
hurricane_dropdown.grid()
submit_button.grid()
emp_count_label.grid()
airport_code_label.grid()
total_price_label.grid()

root.mainloop()
