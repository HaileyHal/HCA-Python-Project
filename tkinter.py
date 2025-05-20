
import tkinter
from tkinter import *
window = tkinter.Tk(screenName = "HCA", baseName = None, className = "Tk", useTk=1) # creating the main window
window.title("Healthcare Hurricane Portal") #titling window
window.geometry("400x300") # setting width and height for window

# widgets

zip = Label(text="Please Enter your Hospital Zipcode.") # creating label
zip.pack() # adding to the window
zipEntry = Entry()
zipEntry.pack()
zipcode = Entry.get() # CONTINUE HERE
level = Label(text="Please enter the incoming hurricane level: ")
level.pack()
levelEntry = Entry()
levelEntry.pack()

window.mainloop() # running the tkinter as an event loop

# label
# entry

# label
# entry
# button (to then run code based on input). these are configured to functions!
button = tkinter.Button( # creating what the button looks like
    text="Find Employees",
    width=25,
    height=5,
    bg="blue",
    fg='white',
)