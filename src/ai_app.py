'''
Welcome to the completed file for my HCA Competition non-submission. This program is built to
determine how many employees are needed in the event of a hurricane. 
'''
import threading
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

import tkinter as tk
from customtkinter import CTk, CTkButton, CTkLabel, CTkEntry, CTkComboBox
from customtkinter import CTkTextbox, CTkProgressBar

from dotenv import load_dotenv

import pandas as pd
import requests

from geopy import distance

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================
# Reading in file of HCA Employees - do this once at startup
hca = pd.read_csv('CoordHCA.csv')
airports_df = pd.read_csv('airports.csv')

load_dotenv()
api_key = 'bb9b3869f0b6710931ab34d0668b1b41710f304038eadc4083472e9483ee6e08'

departure_airports = ['AEX', 'AGS', 'ANC', 'ATL', 'AUS', 'BOI', 'BOS', 'BQK', 'BNA', 'BWI',
                      'CHA', 'CHS', 'CHO', 'CLT', 'CMI', 'CRP', 'DAB', 'DAL', 'DCA', 'DEN',
                      'DFW', 'ELP', 'FLL', 'GNV', 'GRK', 'HOU', 'IAD', 'IAH', 'IDA', 'IND', 
                      'ITC', 'JAX', 'LAS', 'LAX', 'LEX', 'LWB', 'LYH', 'MCI', 'MCN', 'MCO',
                      'MHT', 'MIA', 'MLB', 'MSY', 'OAK', 'ONT', 'OXR', 'PBI', 'PFN', 'PHF',
                      'PIB', 'PIE', 'PNS', 'PSP', 'RDU', 'RIC', 'ROA', 'RSW', 'SAV', 'SFO',
                      'SJC', 'SLC', 'SRQ', 'TLH', 'TPA', 'TRI', 'TYS', 'VLD', 'VPS']

today = date.today()

# Pre-calculate employee counts by facility_zip for performance
emp_count_by_facility = hca.groupby('facility_zip')['Emp34Id'].nunique()

def submit():
    '''
    This method will calculate the number of needed employees, and then display that on the GUI.
    '''
    destination_zip = int(destination_zip_var.get())
    needed_emps = emp_count_by_facility.get(destination_zip, 0)

    # 10%-50% of employees are needed to fill an affected hospital, depending on size
    hurricane_level = int(hurricane_level_var.get())
    multiplier = hurricane_level * 0.1
    needed_emps = int(round(needed_emps * multiplier, 0))  # Calculating needed emps

    needed_emps_var.set(needed_emps)
    emp_count_label.configure(text=f'You will need {needed_emps} employees brought in.')
    airport_code_label.configure(text='What is the destination airport code?')
    submit_button.grid_forget()
    airport_code_dropdown.grid()
    find_employees_button.grid()
    progress_bar.grid()
    root.update()

def fetch_flight_price(origin, destination):
    '''
    Using SerpAPI to fetch flight price for a single origin-destination pair
    '''
    params = {
        'engine': 'google_flights',
        'departure_id': origin,
        'arrival_id': destination,
        'gl': 'us',
        'type': 2,
        'outbound_date': today,
        'api_key': api_key,
        'sort_by': 2
    }

    try:
        response = requests.get('https://serpapi.com/search', params=params, timeout=10)
        data = response.json()

        if data.get('error'):  # If there is no found flight for the pair
            print(f'Error for {origin}: {data["error"]}')
            return None

        flights = data.get('other_flights', [])
        if not flights:
            return None

        prices = [flight.get('price') for flight in flights if flight.get('price') is not None]

        if prices:
            avg_price = round(sum(prices) / len(prices), 2)  # Finding average price for the day
            return {'origin': origin, 'destination': destination, 'price': avg_price}

        return None

    except requests.exceptions.RequestException as e:  # If there is any other sort of error
        print(f'Request error for {origin}: {e}')
        return None

def find_employees():
    '''
    This method will run the rest of the backend code using parallel processing
    '''
    airport_code = airport_code_var.get()
    available_airports = [ap for ap in departure_airports if ap != airport_code]

    # Clear previous results
    airport_emps_label.delete("1.0", "end")

    # Show progress bar
    progress_bar.set(0)
    progress_label.configure(text="Fetching flight prices...")
    root.update()

    # Run API calls in background thread to avoid freezing GUI
    threading.Thread(target=fetch_prices_async, args=(available_airports, airport_code),
                     daemon=True).start()

def fetch_prices_async(available_airports, airport_code):
    '''
    Fetch prices using parallel processing in background thread
    '''
    all_prices = []

    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all API calls
        future_to_airport = {
            executor.submit(fetch_flight_price, origin, airport_code): origin 
            for origin in available_airports
        }

        completed = 0
        total = len(available_airports)

        # Process results as they complete
        for future in as_completed(future_to_airport):
            completed += 1
            origin = future_to_airport[future]

            # Update progress bar on main thread
            progress = completed / total
            root.after(0, lambda p=progress: progress_bar.set(p))
            root.after(0, lambda: progress_label.configure(
                text=f"Processing {completed}/{total} airports..."))

            try:
                result = future.result()
                if result:
                    all_prices.append(result)
                    print(f'Got price for {origin}: ${result["price"]}')
            except Exception as e:
                print(f'Error processing {origin}: {e}')

    # Process results on main thread
    root.after(0, lambda: process_flight_results(all_prices, airport_code))
def process_flight_results(all_prices, airport_code):
    '''
    Process flight results and find optimal employee allocation
    '''
    # Update progress to show we're in final processing phase
    progress_label.configure(text="Processing flight data...")
    root.update()

    if not all_prices:
        progress_label.configure(text="No flight prices found")
        progress_bar.grid_remove()
        return

    print(f'Processing {len(all_prices)} flight prices')

    # Create DataFrame with flight prices and airport coordinates
    prices_df = pd.DataFrame(all_prices)

    progress_label.configure(text="Adding airport coordinates...")
    root.update()

    # Add coordinates using vectorized merge operations
    prices_df = prices_df.merge(
        airports_df[['IATA', 'LATITUDE', 'LONGITUDE']], 
        left_on='origin', right_on='IATA', how='left'
    ).rename(columns={'LATITUDE': 'origin_lat', 'LONGITUDE': 'origin_long'}).drop('IATA', axis=1)

    prices_df = prices_df.merge(
        airports_df[['IATA', 'LATITUDE', 'LONGITUDE']], 
        left_on='destination', right_on='IATA', how='left'
    ).rename(columns={'LATITUDE': 'destination_lat', 'LONGITUDE': 'destination_long'}).drop(
        'IATA', axis=1)

    # Remove rows with missing coordinates-- not sure this is needed
    prices_df = prices_df.dropna(subset=['origin_lat', 'origin_long'])

    if len(prices_df) == 0:
        progress_label.configure(text="No valid airport coordinates found")
        progress_bar.grid_remove()
        return

    # Sort by price for optimal allocation
    prices_df = prices_df.sort_values('price')

    # Save results
    filename = f'flight prices for {today}.csv'
    prices_df.to_csv(filename, index=False)

    progress_label.configure(text="Finding optimal employee allocation...")
    root.update()

    # Run the heavy computation in a separate thread
    threading.Thread(target=find_optimal_allocation_async, args=(prices_df,), daemon=True).start()

def find_optimal_allocation_async(prices_df):
    '''
    Find optimal employee allocation in background thread
    '''
    needed_emps = needed_emps_var.get()
    final_price = 0
    remaining_emps = needed_emps

    # Pre-calculate hospital locations for distance calculations
    hospital_coords = hca[['latitude', 'longitude']].values

    allocation_results = []

    for idx, (_, row) in enumerate(prices_df.iterrows()):
        if remaining_emps <= 0:
            break

        # Update progress on main thread
        progress_text = (f"Checking available employees: "
                         f"Airport {idx + 1} of {len(prices_df)}: {row['origin']}")
        root.after(0, lambda text=progress_text: progress_label.configure(text=text))

        # Vectorized distance calculation
        airport_coord = (row['origin_lat'], row['origin_long'])
        distances = [distance.distance(hospital_coord, airport_coord).miles 
                    for hospital_coord in hospital_coords]

        # Find hospitals within radius
        within_radius_mask = pd.Series(distances) <= 50
        radius_hospitals = hca[within_radius_mask]

        # Calculate available employees (10% of each facility)
        if len(radius_hospitals) > 0:
            facility_emp_counts = radius_hospitals.groupby('facility_zip')['Emp34Id'].nunique()
            total_available_emps = int(facility_emp_counts.sum() * 0.1)
        else:
            total_available_emps = 0

        # Calculate employees to use from this airport
        emps_to_use = min(remaining_emps, total_available_emps)
        airport_cost = emps_to_use * row['price']
        final_price += airport_cost
        remaining_emps -= emps_to_use

        # Store results for GUI update
        result_data = {
            'origin': row['origin'],
            'available_emps': total_available_emps,
            'price': round(row['price'], 2),
            'emps_used': emps_to_use,
            'remaining_emps': remaining_emps,
            'radius_hospitals': radius_hospitals if remaining_emps <= 0 else None
        }
        allocation_results.append(result_data)

    # Update GUI on main thread with all results
    root.after(0, lambda: update_gui_with_results(allocation_results, final_price))

def update_gui_with_results(allocation_results, final_price):
    '''
    Update GUI with allocation results on main thread
    '''
    # Clear previous results
    airport_emps_label.delete("1.0", "end")

    for result in allocation_results:
        if result['available_emps'] > 0:
            airport_message = (f"Airport {result['origin']}: "
                               f"{result['available_emps']} employees available "
                               f"at ${result['price']} each (using {result['emps_used']})\n")
            airport_emps_label.insert("end", airport_message)

    airport_emps_label.see("end")

    # Show hospital breakdown for the final airport if we found all employees
    final_result = allocation_results[-1] if allocation_results else None
    if (final_result and final_result['remaining_emps'] <= 0 
        and final_result['radius_hospitals'] is not None):
        emp_count_by_hospital = (final_result['radius_hospitals']
                                 .groupby('EmpLocationDesc')['Emp34Id'].nunique())
        response_message = (f'Hospitals within 50 miles of {final_result["origin"]} airport:'
                           f'\n{emp_count_by_hospital.to_string()}')
        response_label.configure(text=response_message)

    total_price_label.configure(text=f'Your total cost is ${final_price:,.2f}.')
    progress_bar.grid_remove()
    progress_label.configure(text="Complete!")

def find_optimal_allocation(prices_df):
    '''
    Legacy function - now redirects to async version
    '''
    find_optimal_allocation_async(prices_df)

def within_radius_vectorized(airport_lat, airport_lon, radius_miles=50):
    '''
    Vectorized version of within_radius function for better performance
    '''
    airport_coord = (airport_lat, airport_lon)
    distances = hca.apply(lambda row: distance.distance(
        (row['latitude'], row['longitude']), airport_coord).miles, axis=1)
    return hca[distances <= radius_miles]

# =============================================================================
# TKINTER PROGRAM
# =============================================================================
root = CTk()
root.geometry('900x800')
root.title("Healthcare Hurricane Portal")
destination_zip_var = tk.StringVar()
needed_emps_var = tk.IntVar()
hurricane_level_var = tk.IntVar()
airport_code_var = tk.StringVar()
response_var = tk.StringVar()

# =============================================================================
# TKINTER WIDGETS
# =============================================================================
zip_label = CTkLabel(root, text='Hospital Zipcode:', font=('Arial', 20), text_color='#04033A')
zip_entry = CTkEntry(root, textvariable=destination_zip_var, font=('Arial', 20),
                     text_color='#04033A')

hurricane_label = CTkLabel(root, text='Select Incoming Hurricane Level:', font=('Arial', 20),
                           text_color='#04033A')
hurricane_dropdown = CTkComboBox(root, variable=hurricane_level_var,
                                 values=['1', '2', '3', '4', '5'], font=('Arial', 20),
                                 text_color='#04033A')

submit_button = CTkButton(root, text='Submit', command=submit, corner_radius=32)
emp_count_label = CTkLabel(root, text='', font=('Arial', 20))

airport_code_label = CTkLabel(root, text='', font=('Arial', 20))
airport_code_dropdown = CTkComboBox(root, variable=airport_code_var, values=departure_airports,
                                    font=('Arial', 20))
airport_code_dropdown.grid_forget()

find_employees_button = CTkButton(root, text='Find Employees', command=find_employees,
                                  corner_radius=32)

# Progress indicators
progress_bar = CTkProgressBar(root, width=400)
progress_bar.grid_forget()
progress_label = CTkLabel(root, text='', font=('Arial', 16))

airport_emps_label = CTkTextbox(root, height=200, width=600, font=('Arial', 16))
response_label = CTkLabel(root, text='', font=('Arial', 16), wraplength=600)
total_price_label = CTkLabel(root, text='', font=('Arial', 20), text_color='green')

# =============================================================================
# TKINTER GRID AND APP START
# =============================================================================
zip_label.grid(pady=5)
zip_entry.grid(pady=5)
hurricane_label.grid(pady=5)
hurricane_dropdown.grid(pady=5)
submit_button.grid(pady=10)
emp_count_label.grid(pady=5)
airport_code_label.grid(pady=5)
progress_label.grid(pady=5)
airport_emps_label.grid(pady=10)
total_price_label.grid(pady=10)

root.mainloop()
