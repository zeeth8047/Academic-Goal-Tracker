import mysql.connector
import tkinter as tk
from tkinter import messagebox

# Connect to MySQL database
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Saipoojith@8047..",
        database="BIS_698_Group2"
    )
except mysql.connector.Error as e:
    messagebox.showerror("Database Connection Error", f"Failed to connect to the database: {e}")
    exit()