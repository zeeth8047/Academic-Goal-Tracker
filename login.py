import tkinter as tk
import mysql.connector
import random
from tkinter import messagebox
from database_connection import db
from tkinter import PhotoImage
from PIL import Image, ImageTk
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define colors for the application
background_color = '#F9F9F9'  # Light gray similar to iOS Notes
text_color = '#333333'  # Dark gray for text
button_color = '#2962FF'  # Blue for buttons

# Define a list of motivational quotes
motivational_quotes = [
    "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle.",
    "Start where you are. Use what you have. Do what you can.",
    "Don't be afraid to fail. Not failing is the biggest failure of all.",
    "The journey of a thousand miles begins with a single step.",
    "Believe you can and you're halfway there.",
]

# Function to handle user registration
def register_user():
    username = registration_username_entry.get()
    password = registration_password_entry.get()
    email = registration_email_entry.get()

    if username and password and email:

        # Check if username meets the minimum length requirement
        if len(username) < 3:
            show_custom_error("Username should contain at least 3 characters.")
            return

        # Check if the password is strong
        strength_level = calculate_password_strength(password)
        if strength_level == "Weak":
            show_custom_error("Weak Password! Please choose a stronger password!")
            return

        cursor = db.cursor()

        try:
            # Check if username already exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            # Register the user if username doesn't exist
            if not existing_user:
                cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
                db.commit()
                messagebox.showinfo("Registration", "Registration successful!")
                registration_username_entry.delete(0, 'end')
                registration_password_entry.delete(0, 'end')
                registration_email_entry.delete(0, 'end')
                registration_window.destroy()  # Close registration window
            else:
                show_custom_error("Username already exists!\nPlease Chose a different username!")

        except mysql.connector.errors.ProgrammingError as e:
            messagebox.showerror("Registration Error", f"Invalid SQL query. Check the placeholder parameters: {e}")

        cursor.close()
    else:
        messagebox.showerror("Registration", "Please fill in all the fields.")

# Function to handle user login
def login_user():
    username = username_entry.get()
    password = password_entry.get()
    cursor = db.cursor()

    try:
        # Check user credentials against the database
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            global logged_in_username
            global user_Id
            user_Id = user_id
            logged_in_username = username
            messagebox.showinfo("Login", "Login successful!")
            root.destroy()
        else:
            show_custom_error("Invalid username or password.")
            username_entry.delete(0, 'end')
            password_entry.delete(0, 'end')

    except mysql.connector.errors.ProgrammingError as e:
        messagebox.showerror("Login Error", f"Invalid SQL query. Check the placeholder parameters: {e}")

    cursor.close()

def show_custom_error(message):
    error_window = tk.Toplevel(root)
    error_window.title("Error")
    error_window.geometry("450x130")
    error_window.configure(bg="white")

    error_label = tk.Label(error_window, text=message, fg="red", bg="white", font=("Helvetica", 14, "bold"))
    error_label.pack(pady=20)

    ok_button = tk.Button(error_window, text="OK", command=error_window.destroy)
    ok_button.pack()

# Function to open the registration screen
def open_registration_screen():
    global registration_window, registration_username_entry, registration_password_entry, registration_email_entry, bg_photo_registration, strength_label,canvas

    registration_window = tk.Toplevel(root)
    registration_window.title('Registration')
    registration_window.geometry('600x500')
    registration_window.configure(bg='#F6F6F6')

    bg_photo_registration = ImageTk.PhotoImage(bg_image)

    # Create a label for the background image
    bg_label = tk.Label(registration_window, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

    welcome_label_registration = tk.Label(registration_window, text='Welcome to Academic Goal Tracking Application Registration', bg='maroon', font=('cursive', 16, 'bold'), fg='yellow',  width=30)  # Set text color to white
    welcome_label_registration.pack(side='top', fill='x', padx=30, pady=30)

    # Labels and Entry widgets for registration
    registration_username_label = tk.Label(registration_window, text='Username:', bg='white', fg='black')
    registration_username_entry = tk.Entry(registration_window)

    registration_password_label = tk.Label(registration_window, text='Password:', bg='white', fg='black')
    registration_password_entry = tk.Entry(registration_window, show='*')

    registration_password_entry.bind("<KeyPress>", update_password_strength)

    strength_label = tk.Label(registration_window, text="Password Strength: ", bg=background_color)
    canvas = tk.Canvas(registration_window, width=150, height=10, bg=background_color)

    registration_email_label = tk.Label(registration_window, text='Email:', bg='white', fg='black')
    registration_email_entry = tk.Entry(registration_window)

    # Button for registration
    register_button = tk.Button(registration_window, text='Register', command=register_user)

    registration_password_entry.bind("<Enter>", display_tooltip)
    registration_password_entry.bind("<Leave>", hide_tooltip)

    # Layout for registration screen
    registration_username_label.pack(pady=5)
    registration_username_entry.pack(pady=5)
    registration_password_label.pack(pady=5)
    registration_password_entry.pack(pady=5)
    strength_label.pack()
    canvas.pack()
    registration_email_label.pack(pady=5)
    registration_email_entry.pack(pady=5)
    register_button.pack(pady=15)

global SPECIAL_CHARACTERS

SPECIAL_CHARACTERS = "!@#$%^&*()-_=+"

def update_password_strength(event):
    password = registration_password_entry.get()
    strength_level = calculate_password_strength(password)
    strength_label.config(text=f"Password Strength: {strength_level}")

    if password:
        if strength_level == "Weak":
            color = "red"
            width = 50  # Fixed width for "Weak"
        elif strength_level == "Medium":
            color = "yellow"
            width = 70  # Fixed width for "Medium"
        elif strength_level == "Strong":
            color = "green"
            width = 150  # Fixed width for "Strong" (maximum width)
        else:
            color = "black"
            width = 0  # No width for an invalid password
    else:
        canvas.delete("all")  # Clear canvas when password is empty
        strength_label.config(text=f"Password Strength: ")
        return

    canvas.delete("all")
    canvas.create_rectangle(0, 0, width, 10, fill=color)

def calculate_password_strength(password):
    if len(password) < 8:
        return "Weak"
    elif not any(char.isdigit() for char in password):
        return "Medium"
    elif not any(char.isupper() for char in password):
        return "Medium"
    elif not any(char.islower() for char in password):
        return "Medium"
    elif not any(char in SPECIAL_CHARACTERS for char in password):
        return "Medium"
    else:
        return "Strong"


def display_tooltip(event):
    global tooltip
    x, y, _, _ = password_entry.bbox("insert")
    x += password_entry.winfo_rootx() + 25
    y += password_entry.winfo_rooty() + 25
 
    tooltip = tk.Toplevel(password_entry)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry(f"+{x}+{y}")
 
    tooltip_label = tk.Label(tooltip, text="""
    A strong password should meet the following criteria:
    1. At least 8 characters long
    2. Includes at least one special character (e.g., !@#$%^&*()-+={}[]|;:"<>,./?)
    3. Includes at least one uppercase letter
    4. Includes at least one lowercase letter
    """, background="#ffffe0", relief="solid", borderwidth=1)
    tooltip_label.pack(ipadx=5)
 
def hide_tooltip(event):
    tooltip.destroy()

# Function to handle password recovery
def recover_password():

    global bg_photo_recovery

    # Create a new window for password recovery
    recovery_window = tk.Toplevel(root)
    recovery_window.title("Forgot Password")
    recovery_window.geometry("600x400")
    recovery_window.configure(bg='#F6F6F6')

    bg_photo_recovery = ImageTk.PhotoImage(bg_image)

    # Create a label for the background image
    bg_label = tk.Label(recovery_window, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

    welcome_label_recovery = tk.Label(recovery_window, text='Forgot Password? Please enter details to recover your password!', bg='maroon', font=('cursive', 16, 'bold'), fg='yellow', width=30)  # Set text color to white
    welcome_label_recovery.pack(side='top', fill='x', padx=30, pady=30)

    # Labels and Entry widgets for username and email
    username_label = tk.Label(recovery_window, text='Username:', bg='white', fg='black')
    username_entry = tk.Entry(recovery_window)

    email_label = tk.Label(recovery_window, text='Email:', bg='white', fg='black')
    email_entry = tk.Entry(recovery_window)


    # Function to send the password to the user's email
    def send_password():
        username = username_entry.get()
        email = email_entry.get()

        if username and email:
            # Query the database to retrieve the user's password
            cursor = db.cursor()
            cursor.execute("SELECT password FROM users WHERE username = %s AND email = %s", (username, email))
            result = cursor.fetchone()
            cursor.close()

            if result:
                password = result[0]

                # Implement code to send the password to the user's email (you may use a library like smtplib)

                fromaddr = "goaltracker514@gmail.com"
                smtplibpassword = "ownozsbawlcjtkim"
                toaddr = email
                msg = MIMEMultipart()
                msg['From'] = fromaddr
                msg['To'] = toaddr
                msg['Subject'] = "Password Recovery"
                body = f"Dear user,\n\nYour password is: {password}. Please ensure to keep this password confidential for the security of your account.\n\nBest regards,\n[Academic Goal Tracking System]\n\nNote: Please do not reply to this email."
                msg.attach(MIMEText(body, 'plain'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(fromaddr, smtplibpassword)
                text = msg.as_string()
                server.sendmail(fromaddr, toaddr, text)
                server.quit()

                messagebox.showinfo("Password Recovery", "Your password has been sent to your email.")
                recovery_window.destroy()
            else:
                show_custom_error("Password Recovery", "Invalid username or email.")
        else:
            show_custom_error("Password Recovery", "Please fill in both username and email.")

    # Button to initiate password recovery
    recover_button = tk.Button(recovery_window, text='Recover Password', command=send_password)

    # Layout for the recovery window
    username_label.pack(pady=10)
    username_entry.pack(pady=10)
    email_label.pack(pady=10)
    email_entry.pack(pady=10)
    recover_button.pack(pady=20)


# Function to display a random motivational quote
def show_motivational_quote():
    quote = random.choice(motivational_quotes)
    quote_label.config(text=quote)
    root.after(5000, show_motivational_quote)  # Automatically show a new quote every 5 seconds

# Function to start showing motivational quotes
def start_motivational_quotes():
    show_motivational_quote()

# Create the main window
root = tk.Tk()
root.title('Welcome to Academic Goal Tracking')
root.geometry('700x380')
root.configure(bg='white')  # Set the background color to a light gray similar to iOS Notes

# Load the background image
bg_image = Image.open("login_image.jpeg")
bg_photo = ImageTk.PhotoImage(bg_image)

# Create a label for the background image
bg_label = tk.Label(root, image=bg_photo)
bg_label.place(relwidth=1, relheight=1)

# Create a rectangle for the motivational quote
quote_rectangle = tk.Frame(root, width=300, height=200, bg='white', bd=0, highlightthickness=0)
quote_rectangle.place(x=10, y=150)  # Align the rectangle to the middle bottom of the screen

# Labels and Entry widgets for registration and login
welcome_label = tk.Label(root, text='Welcome to Academic Goal Tracking Application', bg='maroon', font=('cursive', 16, 'bold'), fg='yellow',  width=30)  # Set text color to white
welcome_label.pack(side='top', fill='x', padx=20, pady=30)
username_label = tk.Label(root, text='Username:', bg='white', fg='black')  # Set text color to black
username_entry = tk.Entry(root)
password_label = tk.Label(root, text='Password:', bg='white', fg='black')  # Set text color to black
password_entry = tk.Entry(root, show='*')
quote_label = tk.Label(quote_rectangle, text='', wraplength=400, justify='center', bg='maroon', font=('cursive', 12, 'bold'), fg='yellow')  # Set text color to black

# Create a frame to hold the "Login" and "Register" buttons
buttons_frame = tk.Frame(root, bg='white', bd=0, highlightthickness=0)
buttons_frame.place(relx=0.5, rely=0.7, anchor='center')   # Align the frame to the bottom of the window

forgot_password_label = tk.Label(buttons_frame, text='Forgot Password?', bg='white', fg='blue', cursor='hand2', font=('cursive', 12, 'underline'))

# Function to handle forgot password click
def forgot_password_click(event):
    recover_password()

# Bind the label to the forgot_password_click function when clicked
forgot_password_label.bind("<Button-1>", forgot_password_click)

# Pack layout for the hyperlink label in the middle
forgot_password_label.pack(side='top', pady=5)

# Create buttons for registration and login within the buttons frame
register_button = tk.Button(buttons_frame, text='Register', command=open_registration_screen)
login_button = tk.Button(buttons_frame, text='Login', command=login_user)

# Pack layout for buttons in the middle
register_button.pack(side='left', padx=10, pady=30)
login_button.pack(side='left', padx=15, pady=30)

# Pack layout for other elements
welcome_label.pack(pady=5)
username_label.pack()
username_entry.pack()
password_label.pack()
password_entry.pack()
quote_label.pack(pady=20)
quote_rectangle.pack()

# Display an initial motivational quote and start the automatic quote rotation
start_motivational_quotes()

root.mainloop()
