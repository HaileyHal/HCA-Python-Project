import pandas as pd
hca = pd.read_csv("C:/Users/haile/ASC/DATA-3500-HW/finalProject/CoordHCA.csv")

# user input destination hospital ID and nearest airport code
    # calulate needed emps - get from file on local computer
# 10%-50% of employees are needed to fill an affected hospital, depending on size
destinationZip = int(input("What is your facility zipcode? ")) # determining what hospital we are going to
empCount = hca.groupby("facility_zip")["Emp34Id"].nunique() # grouping by hospital and counting emp ID
neededEmps = empCount.get(destinationZip) # filtering by inputted location- value is total emps at one hospital location

# 10%-50% of employees are needed to fill an affected hospital, depending on size
hurricaneLvl = int(input("What is the incoming hurricane level? "))
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

destinationCode = input("What is your destination airport? Please enter the airport code: ")






# # Multiply by flight prices
# cityPrice = 0 
# totalPrice = 0 # itializing total price
# while neededEmps > 0:
#     # find lowest flight price/city into affected city, somehow filter when I use a city (don't let it pick the lowest city twice)
#     cityPrice = min(fare) # group by destination city
#     # save fares as a list, then remove the minimum from the list at the end of the loop
#     neededEmps = neededEmps - availableEmps # how many emps are still needed
#     if neededEmps < 0:  # making sure we aren't getting "extra" available employees over needed ones
#         neededEmps += availableEmps
#         availableEmps = neededEmps
#     empPrice = cityPrice * availableEmps # make sure availableEmps is from the right city! Not destination city
#     print(f"You are bringing in {availableEmps} from {city}.")
#     totalPrice += empPrice #adding price for each state we pull from to total cost of bringing in employees
#     # remove the minimum fare from my list

# print(f"Your total cost will be {totalPrice}.")

# # make a range of prices?? Like a confidence interval, giving a high and a low price point. Not necessary
