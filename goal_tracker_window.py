import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from tkinter import font
from tkcalendar import DateEntry
import mysql.connector
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import os
from login import logged_in_username, user_Id, bg_image
from database_connection import db
from datetime import datetime

# Defining colors for the application
#background_color = '#F9F9F9'  # Light gray background
background_color = 'white'
text_color = '#333333'  # Dark gray for text
button_color = 'white'  # Green for buttons
header_color = '#2196F3'  # Blue for header
left_pane_color = '#BBDEFB'  # Light blue for the left pane

# Creating the main window
root = tk.Tk()
root.title("Academic Goal Tracking Application")
root.geometry("1100x550")
root.configure(bg=background_color)

if not logged_in_username:
    root.destroy()

background_photo = ImageTk.PhotoImage(bg_image)

def show_custom_error(message):
    error_window = tk.Toplevel(root)
    error_window.title("Error")
    error_window.geometry("450x130")
    error_window.configure(bg="white")

    error_label = tk.Label(error_window, text=message, fg="red", bg="white", font=("Helvetica", 14, "bold"))
    error_label.pack(pady=20)

    ok_button = tk.Button(error_window, text="OK", command=error_window.destroy)
    ok_button.pack()

# Function to create a new goal in the database
def create_goal():
    goal_name = goal_name_entry.get()
    deadline = deadline_calendar.get_date()
    description = description_entry.get()
    progress = completion_slider.get()  # Get completion percentage from the slider

    # Check if the goal name already exists
    if goal_exists(goal_name):
        show_custom_error(f"A goal with the name '{goal_name}' already exists.\nPlease choose a different name.")
        return

    # Adding logic here for creating a goal in the database
    try:
        cursor = db.cursor()
        sql = "INSERT INTO goals (user_id, goal_name, deadline, description, completion_percentage) VALUES (%s, %s, %s, %s, %s)"
        values = (user_Id, goal_name, deadline, description, progress)
        cursor.execute(sql, values)
        db.commit()
        messagebox.showinfo("Success", "Goal created successfully!")

        goal_id = get_goal_id_from_name(goal_name)

        # Inserting a new record into the "progress" table
        insert_progress_sql = "INSERT INTO progress (goal_id, progress_date, completion_percentage) VALUES (%s, %s, %s)"
        insert_progress_values = (goal_id, deadline, progress)

        cursor.execute(insert_progress_sql, insert_progress_values)
        db.commit()
        refresh_modify_screen()
        goal_name_entry.delete(0, 'end')
        deadline_calendar.delete(0, 'end')
        description_entry.delete(0, 'end')
        completion_slider.set(0)  # Reset completion slider after creating goal
    except mysql.connector.Error as e:
        show_custom_error(f"Error! Failed to create goal: {e}")

def goal_exists(goal_name):
    cursor = db.cursor()
    cursor.execute("SELECT goal_name FROM goals WHERE user_id = %s AND goal_name = %s", (user_Id, goal_name))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

# Function to modify an existing goal in the database
def modify_goal():
    selected_item = goal_tree.selection()
    if selected_item:
        goal_id = goal_tree.item(selected_item, 'values')[0]
        new_description = new_description_entry.get()
        new_progress = new_progress_slider.get()
        new_deadline = new_deadline_calendar.get_date()

        try:
            cursor = db.cursor()
            sql = "UPDATE goals SET description = %s, completion_percentage = %s, deadline = %s WHERE goal_id = %s"
            values = (new_description, new_progress, new_deadline,goal_id)
            cursor.execute(sql, values)
            db.commit()
            messagebox.showinfo("Success", "Goal modified successfully!")

            # Inserting a new record into the "progress" table
            insert_progress_sql = "INSERT INTO progress (goal_id, progress_date, completion_percentage) VALUES (%s, %s, %s)"
            insert_progress_values = (goal_id, new_deadline, new_progress)

            cursor.execute(insert_progress_sql, insert_progress_values)
            db.commit()

            # Calling this function after saving data to the database
            refresh_modify_screen()
            new_description_entry.delete(0, 'end')
            new_deadline_calendar.delete(0, 'end')
            new_progress_slider.set(0) 
        except mysql.connector.Error as e:
            show_custom_error(f"Error! Failed to modify goal: {e}")
    else:
        messagebox.showinfo("Info", "Please select a goal to modify.")

def refresh_modify_screen():
    # Clearing existing items in the tree
    for item in goal_tree.get_children():
        goal_tree.delete(item)

    # Repopulating the tree with the latest data
    populate_goals_list()

# Function to handle the selection of a goal from the Treeview
def on_goal_select(event):
    selected_item = goal_tree.selection()
    if selected_item:
        # Extracting values from the selected item
        goal_id, goal_name, goal_deadline = goal_tree.item(selected_item, 'values')
        # Setting the values to the entry widgets or sliders for modification
        new_description_entry.delete(0, tk.END)
        new_description_entry.insert(0, goal_name)  # You can modify this line based on your data model
        new_progress_slider.set(get_completion_percentage_for_goal(goal_id)) 

# Function to populate widgets with goal information when a goal is selected
def populate_widgets_on_select(event):
    selected_item = goal_tree.selection()
    if selected_item:
        goal_id = goal_tree.item(selected_item, 'values')[0]

        try:
            cursor = db.cursor()
            sql = "SELECT description, completion_percentage, deadline FROM goals WHERE goal_id = %s"
            cursor.execute(sql, (goal_id,))
            result = cursor.fetchone()

            if result:
                # Populating widgets with information from the database
                new_description_entry.delete(0, 'end')
                new_description_entry.insert(0, result[0])  # Description

                new_progress_slider.set(result[1])  # Completion Percentage

                # Deadline (assuming new_deadline_calendar is a DateEntry widget)
                new_deadline_calendar.delete(0, 'end')
                new_deadline_calendar.insert(0, result[2])

        except mysql.connector.Error as e:
            show_custom_error(f"Error! Failed to fetch goal information: {e}")


# Function to get completion percentage for a goal 
def get_completion_percentage_for_goal(goal_id):
    try:
        cursor = db.cursor()
        sql = "SELECT completion_percentage FROM goals WHERE goal_id = %s"
        values = (goal_id,)
        cursor.execute(sql, values)
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return 0  # Default value if goal not found
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to fetch completion percentage: {e}")

# Populating the goals list in the "Select Goal to Modify" box
def populate_goals_list():
    try:
        cursor = db.cursor()
        sql = "SELECT goal_id, goal_name, deadline, completion_percentage FROM goals where user_id = %s"
        values = (user_Id,)
        cursor.execute(sql, values)
        results = cursor.fetchall()

        for result in results:
            goal_tree.insert("", tk.END, values=(result[0], result[1], result[2], result[3]))

    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to fetch goals: {e}")

def get_goal_names():
    try:
        cursor = db.cursor()
        sql = "SELECT goal_name FROM goals"
        cursor.execute(sql)
        results = cursor.fetchall()
        return [result[0] for result in results]
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to fetch goal names: {e}")
        return []

# Function to update the dropdown list based on the search string
def update_goal_dropdown(search_string):
    goal_names = get_goal_names()
    matching_goals = [goal for goal in goal_names if search_string.lower() in goal.lower()]
    goal_name_view_combobox['values'] = matching_goals

def show_progress_graph():
    selected_goal = goal_name_view_combobox.get()
    goal_id = get_goal_id_from_name(selected_goal)

    if goal_id is not None:
        # Retrieving progress data for the selected goal
        progress_data = get_progress_data_for_goal(goal_id)

        if progress_data:
            # Creating a new window for displaying the graph
            graph_window = tk.Toplevel(root)
            graph_window.title("Goal Progress Graph")

            # Plot the bar graph
            fig, ax = plt.subplots()
            bar_colors = ['skyblue' for _ in progress_data['dates']]
            bars = ax.bar(progress_data['dates'], progress_data['completion_percentages'], color=bar_colors, label='Completion Percentage')

            # Plot the line connecting the tops of the bars
            # ax.plot(progress_data['dates'], progress_data['completion_percentages'], color='red', marker='o', linestyle='-',
            #         label='Line Chart', markersize=8)

            ax.set_xlabel('Date')
            ax.set_ylabel('Completion Percentage')
            ax.set_title(f'Progress Bar Report for Goal: {selected_goal}')

            ax.legend()

            # Embed the Matplotlib graph in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=graph_window)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            # Adding a toolbar for the Matplotlib graph
            toolbar = NavigationToolbar2Tk(canvas, graph_window)
            toolbar.update()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            # Function to destroy the graph window
            def close_graph_window():
                graph_window.destroy()

            # Adding a button to close the window
            close_button = tk.Button(graph_window, text="Close", command=close_graph_window)
            close_button.pack(side=tk.BOTTOM)

            # Adding a button to export the graph and table to Excel
            export_button = tk.Button(graph_window, text="Export to Excel", command=lambda: export_to_excel(progress_data, selected_goal))
            export_button.pack(side=tk.BOTTOM)

        else:
            messagebox.showinfo("Info", "No progress data available for the selected goal.")
    else:
        messagebox.showinfo("Info", "Please select a goal.")


# Function to export the graph and table data to Excel
def export_to_excel(progress_data, goal_name):
    # Create a directory to store the exports
    exports_dir = 'exports'
    os.makedirs(exports_dir, exist_ok=True)

    # Saving the plots in a subdirectory with the goal name
    goal_dir = os.path.join(exports_dir, goal_name)
    os.makedirs(goal_dir, exist_ok=True)

    # Save the plot as an image file (e.g., PNG)
    fig, ax = plt.subplots()
    bar_colors = ['skyblue' for _ in progress_data['dates']]
    bars = ax.bar(progress_data['dates'], progress_data['completion_percentages'], color=bar_colors)
    plot_filename = f'{goal_name}_progress_plot.png'
    fig.savefig(os.path.join(goal_dir, plot_filename))
    plt.close(fig)  # Close the plot to release resources

    # Creating a DataFrame for the progress data
    df = pd.DataFrame({'Date': progress_data['dates'], 'Completion Percentage': progress_data['completion_percentages']})

    # Writing the DataFrame to an Excel file
    excel_filename = f'{goal_name}_progress_export.xlsx'
    excel_file_path = os.path.join(goal_dir, excel_filename)
    writer = pd.ExcelWriter(excel_file_path, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Progress Data')

    # Getting the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Progress Data']

    # Creating a chart object
    chart = workbook.add_chart({'type': 'column'})

    legend_name = 'Completion Percentage'

    # Configuring the chart from the DataFrame data
    chart.add_series({
        'name': legend_name,
        'categories': ['Progress Data', 1, 0, len(progress_data['dates']), 0],
        'values': ['Progress Data', 1, 1, len(progress_data['dates']), 1],  # Use the entire column for values
    })

    # Configuring the legend
    chart.set_legend({'name': legend_name, 'position': 'top'})

    # Inserting the chart into the worksheet
    worksheet.insert_chart('E2', chart)

    # Close the Pandas Excel writer and output the Excel file
    writer.save()
    messagebox.showinfo("Info", f"Data exported to Excel and plot saved successfully for {goal_name}.")


# # Function to view progress of a specific goal
def view_progress():
    # logic here for viewing progress of a goal
    goal_name = goal_name_view_combobox.get()

    try:
        cursor = db.cursor()
        sql = "SELECT goal_name, completion_percentage,description FROM goals where goal_name = %s"
        values = (goal_name,)
        cursor.execute(sql, values)
        results = cursor.fetchall()

        if results:
            # Extracting goal names and completion percentages from the results
            goal_names = [result[0] for result in results]
            completion_percentages = [result[1] for result in results]
            description = [result[2] for result in results]
            first_description = description[0]

            # If a specific goal is selected, retrieve its progress
            if goal_name:
                selected_goal_index = goal_names.index(goal_name)
                progress_percentage = completion_percentages[selected_goal_index]
            # Creating a vertical bar chart aligned to the right
            fig, ax = plt.subplots(figsize=(3, 2))
            if progress_percentage > 50:
                ax.bar(goal_name, progress_percentage, color='green')
            else:
                ax.bar(goal_name, progress_percentage, color='red')
            ax.set_ylim(0, 100)
            ax.set_ylabel('Completion Percentage')
            ax.set_title('Goal Completion Progress')
            plt.tight_layout()

            # Embed the plot in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=view_progress_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=5, column=1, padx=10, pady=10, sticky="nsew")

            # Displaying progress information in the text widget
            progress_text.delete(1.0, tk.END)
            progress_text.insert(tk.END, f"Goal Name: {goal_name}\nCompletion Percentage: {progress_percentage}\nDescription: {first_description}")
        else:
            show_custom_error("", f"Goal not found! \nNo goal with the name '{goal_name}' found.")

    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to view progress: {e}")


# Function to get goal ID from its name
def get_goal_id_from_name(goal_name):
    try:
        cursor = db.cursor()
        sql = "SELECT goal_id FROM goals WHERE goal_name = %s"
        values = (goal_name,)
        cursor.execute(sql, values)
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to fetch goal ID: {e}")
        return None

# Function to get progress data for a goal
def get_progress_data_for_goal(goal_id):
    try:
        cursor = db.cursor()
        sql = "SELECT DATE_FORMAT(progress_date, '%m/%d') AS progress_date, completion_percentage FROM progress WHERE goal_id = %s"
        values = (goal_id,)
        cursor.execute(sql, values)
        results = cursor.fetchall()

        dates = [result[0] for result in results]
        completion_percentages = [result[1] for result in results]

        return {'dates': dates, 'completion_percentages': completion_percentages}
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to fetch progress data: {e}")
        return None

# Function to view overall progress
def overall_progress():
    try:
        cursor = db.cursor()
        sql = "SELECT goal_id, goal_name, deadline, description FROM goals"
        cursor.execute(sql)
        results = cursor.fetchall()
        if results:
            # Clear existing items in the tree
            for item in overall_progress_tree.get_children():
                overall_progress_tree.delete(item)

            for result in results:
                goal_id, goal_name, deadline, description = result
                overall_progress_tree.insert("", tk.END, values=(goal_name, description, deadline, goal_id))

        else:
            show_custom_error("No goals found.")
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to view overall progress: {e}")

# Function to view detailed progress of a specific goal in overall progress
def view_overall_progress_report():
    try:
        cursor = db.cursor()
        cursor.execute("SELECT goal_name, completion_percentage FROM goals")
        results = cursor.fetchall()
        if results:
            goal_names, completion_percentages = zip(*results)
            # Replace None values with 0
            completion_percentages = [0 if percentage is None else percentage for percentage in completion_percentages]
            # Plotting the progress report
            fig, ax = plt.subplots(figsize=(7, 5))
            # Set the color based on completion_percentage
            colors = ['tomato' if percentage <= 25 else ('lightblue' if 25 < percentage < 100 else 'lightgreen') for percentage in
                      completion_percentages]
            bars = ax.barh(goal_names, completion_percentages, color=colors)

            # Display percentage numbers as labels on each bar
            for bar, value in zip(bars, completion_percentages):
                ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f'{value}%',
                        va='center', color='black', fontweight='bold')
            # ax.barh(goal_names, completion_percentages, color= colors)
            ax.set_xlabel('Percentage Completion')
            ax.set_ylabel('Goal Titles')
            ax.set_title('Progress Report for Goals')

            # Adjust layout and save the plot
            plt.tight_layout()
            plt.savefig("progress_report.png")

            # Embed the plot in a popup window
            popup_window = tk.Toplevel(root)
            popup_window.title("Overall Progress Report")
            popup_window.geometry("950x650")

            # Create a canvas for the plot
            canvas = FigureCanvasTkAgg(fig, master=popup_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack()

            # Embed Matplotlib's navigation toolbar
            toolbar = NavigationToolbar2Tk(canvas, popup_window)
            toolbar.update()
            canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            # Creating a button to save the plot
            save_button = tk.Button(popup_window, text='Save Plot', command=lambda: save_plot(fig))
            save_button.pack()

            # Saving the plot as an image file (optional)
            def save_plot(figure):
                filename = filedialog.asksaveasfilename(defaultextension=".png",
                                                        filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
                if filename:
                    figure.savefig(filename)

        else:
            show_custom_error('No Goals! No goals found in the database.')

    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to view progress report: {e}")
 

def get_and_categorize_reminders():
    # Getting the current date
    today = datetime.now().date()

    # Creating a cursor
    cursor = db.cursor()

    try:
        # Query upcoming reminders
        cursor.execute("""
            SELECT goal_name, deadline
            FROM goals
            WHERE deadline >= %s and completion_percentage != 100
            ORDER BY deadline ASC
        """, (today,))
        upcoming_reminders = cursor.fetchall()

        # Query pending reminders
        cursor.execute("""
            SELECT goal_name, deadline
            FROM goals
            WHERE deadline < %s and completion_percentage != 100
            ORDER BY deadline ASC
        """, (today,))
        pending_reminders = cursor.fetchall()

        # Query completed reminders
        cursor.execute("""
            SELECT DISTINCT goals.goal_name, goals.deadline
            FROM goals
            LEFT JOIN progress ON goals.goal_id = progress.goal_id
            WHERE progress.completion_percentage = 100
            ORDER BY goals.deadline ASC
        """)
        completed_reminders = cursor.fetchall()

        # Clearing the existing data in the Treeview
        upcoming_tree.delete(*upcoming_tree.get_children())
        pending_tree.delete(*pending_tree.get_children())
        completed_tree.delete(*completed_tree.get_children())

        # Inserting data into the Treeview
        for i, reminder in enumerate(upcoming_reminders):
            color = 'white' if i % 2 == 0 else 'lightgrey'
            upcoming_tree.insert('', 'end', values=reminder, tags=color)

        for i, reminder in enumerate(pending_reminders):
            color = 'white' if i % 2 == 0 else 'lightgrey'
            pending_tree.insert('', 'end', values=reminder, tags=color)

        for i, reminder in enumerate(completed_reminders):
            color = 'white' if i % 2 == 0 else 'lightgrey'
            completed_tree.insert('', 'end', values=reminder, tags=color)

        # # Display reminders in labels
        # upcoming_text.config(text="\n".join([f"{reminder[0]} - {reminder[1]}" for reminder in upcoming_reminders]))
        # pending_text.config(text="\n".join([f"{reminder[0]} - {reminder[1]}" for reminder in pending_reminders]))
        # completed_text.config(text="\n".join([f"{reminder[0]} - {reminder[1]}" for reminder in completed_reminders]))

    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Failed to retrieve reminders: {e}")

    finally:
        # Closing the cursor
        cursor.close()

# Function to switch to "Create Goal" functionality
def switch_to_create_goal():
    notebook.select(0)  # Index 0 corresponds to the "Create Goal" tab

# Function to switch to "Modify Goal" functionality
def switch_to_modify_goal():
    notebook.select(1)  # Index 1 corresponds to the "Modify Goal" tab

# Function to switch to "View Progress" functionality
def switch_to_view_progress():
    notebook.select(2)  # Index 2 corresponds to the "View Progress" tab

# Function to switch to "Overall Progress" functionality
def switch_to_overall_progress():
    notebook.select(3)  # Index 3 corresponds to the "Overall Progress" tab


def switch_to_reminders():
    notebook.select(4)  # Index 34corresponds to the "reminders" tab

# Create a left control pane
control_frame = tk.Frame(root, bg=left_pane_color)
control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ns")
    
# Create left control pane using grid
control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ns")

# Create buttons for different functionalities in the left control pane
create_goal_button = tk.Button(control_frame, text='Create Goal', fg=text_color, bg=button_color, command=switch_to_create_goal)
create_goal_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

modify_goal_button = tk.Button(control_frame, text='Modify Goal', fg=text_color, bg=button_color, command=switch_to_modify_goal)
modify_goal_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

view_progress_button = tk.Button(control_frame, text='View Progress', fg=text_color, bg=button_color, command=switch_to_view_progress)
view_progress_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

overall_progress_button = tk.Button(control_frame, text='Overall Progress', fg=text_color, bg=button_color, command=switch_to_overall_progress)
overall_progress_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

reminders_button = tk.Button(control_frame, text='Reminders', fg=text_color, bg=button_color, command=switch_to_reminders)
reminders_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")


# Open the image with Pillow
image_path = 'goal_image.jpeg'
original_image = Image.open(image_path)

# Calculate the new height to maintain the aspect ratio
new_width = 200  # Set your desired width
aspect_ratio = original_image.width / float(original_image.height)
new_height = int(new_width / aspect_ratio)

# Resize the image
resized_image = original_image.resize((new_width, new_height))

# Convert the Pillow image to a PhotoImage
image = ImageTk.PhotoImage(resized_image)

# Create a button with the image
image_button = tk.Button(control_frame, image=image, command=lambda: None, bd=0, highlightthickness=0)
image_button.grid(row=16, column=0, padx=10, pady=10, sticky="s")

# Label to display user details at the bottom:
# Create a custom font similar to Segoe UI
custom_font = font.Font(family="Lobster", size=12, weight="bold")

# Create a label with custom styling
user_label = tk.Label(
    control_frame,
    text=f"Hello, {logged_in_username.capitalize()}!\nWelcome to the Goal Tracker\nDashboard!",
    #fg="#4285F4", 
    fg="darkblue",
    bg="white",
    font=custom_font,
    justify="center",  # Center-align text
    padx=15,  # Add horizontal padding
    pady=15,  # Add vertical padding
    relief="raised",  # Add a border with raised relief
    borderwidth=4,  
)

user_label.grid(row=18, column=0, padx=10, pady=10, sticky="s")


# Create a notebook (tabbed interface) in the right pane
notebook = ttk.Notebook(root)
notebook.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

# Create frames for each tab
goal_creation_frame = tk.Frame(notebook, bg=background_color)
modify_goal_frame = tk.Frame(notebook, bg=background_color)
view_progress_frame = tk.Frame(notebook, bg=background_color)
overall_progress_frame = tk.Frame(notebook, bg=background_color)
reminders_frame = tk.Frame(notebook, bg=background_color)

# Add tabs to the notebook
notebook.add(goal_creation_frame, text='Create Goal')
notebook.add(modify_goal_frame, text='Modify Goal')
notebook.add(view_progress_frame, text='View Progress')
notebook.add(overall_progress_frame, text='Overall Progress')
notebook.add(reminders_frame, text='Reminders')

# Create a frame for the background image within the "Create Goal" tab
background_frame_create_goal = tk.Frame(goal_creation_frame, bg=background_color, bd=0, highlightthickness=0)
background_frame_create_goal.place(relwidth=1, relheight=1)

# Create a frame for the background image within the "Modify Goal" tab
background_frame_modify_goal = tk.Frame(modify_goal_frame, bg=background_color, bd=0, highlightthickness=0)
background_frame_modify_goal.place(relwidth=1, relheight=1)

# Create a frame for the background image within the "View Progress" tab
background_frame_view_progress = tk.Frame(view_progress_frame, bg=background_color, bd=0, highlightthickness=0)
background_frame_view_progress.place(relwidth=1, relheight=1)

# Create a frame for the background image within the "Overall Progress" tab
background_frame_overall_progress = tk.Frame(overall_progress_frame, bg=background_color, bd=0, highlightthickness=0)
background_frame_overall_progress.place(relwidth=1, relheight=1)

# Functionality for the "Create Goal" tab
goal_name_label = tk.Label(goal_creation_frame, text='Goal Name:', fg=text_color, bg=background_color)
goal_name_label.grid(row=2, column=1, padx=(0, 10), pady=(10, 5), sticky="e")

goal_name_entry = tk.Entry(goal_creation_frame, width=30)
goal_name_entry.grid(row=2, column=2, padx=(0, 10), pady=(10, 5), sticky="w")

description_label = tk.Label(goal_creation_frame, text='Description:', fg=text_color, bg=background_color)
description_label.grid(row=4, column=1, padx=(0, 10), pady=5, sticky="e")

description_entry = tk.Entry(goal_creation_frame, width=50)
description_entry.grid(row=4, column=2, padx=(0, 10), pady=5, sticky="w")

deadline_label = tk.Label(goal_creation_frame, text='Deadline:', fg=text_color, bg=background_color)
deadline_label.grid(row=6, column=1, padx=(0, 10), pady=5, sticky="e")

# Set the foreground color for the DateEntry widget
deadline_calendar = DateEntry(goal_creation_frame, date_pattern='yyyy-mm-dd', selectbackground=button_color, foreground=text_color)
deadline_calendar.grid(row=6, column=2, padx=(0, 10), pady=5, sticky="w")

completion_percentage_label = tk.Label(goal_creation_frame, text='Progress(%):', fg=text_color, bg=background_color)
completion_percentage_label.grid(row=8, column=1, padx=(0, 10), pady=5, sticky="e")

completion_slider = tk.Scale(goal_creation_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, resolution=1, bg=background_color)
completion_slider.grid(row=8, column=2, padx=(0, 10), pady=5, sticky="w")

submit_button = tk.Button(goal_creation_frame, text='Submit', fg=text_color, bg=button_color, command=create_goal)
submit_button.grid(row=10, column=1, columnspan=2, pady=(10, 20), sticky="s")

background_label_create_goal = tk.Label(background_frame_create_goal, image=background_photo)
background_label_create_goal.place(relx=0.5, rely=0.5, anchor='center')

# Functionality for the "Modify Goal" tab
new_description_label = tk.Label(modify_goal_frame, text='New Description:', fg=text_color, bg=background_color)
new_description_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="e")

new_description_entry = tk.Entry(modify_goal_frame, width=50)
new_description_entry.grid(row=2, column=1, padx=10, pady=(10, 5), sticky="w")

new_deadline_label = tk.Label(modify_goal_frame, text='New Deadline:', fg=text_color, bg=background_color)
new_deadline_label.grid(row=4, column=0, padx=10, pady=5, sticky="e")

# Set the foreground color for the DateEntry widget
new_deadline_calendar = DateEntry(modify_goal_frame, date_pattern='yyyy-mm-dd', selectbackground=button_color, foreground=text_color)
new_deadline_calendar.grid(row=4, column=1, padx=10, pady=5, sticky="w")

new_progress_label = tk.Label(modify_goal_frame, text='New Progress(%):', fg=text_color, bg=background_color)
new_progress_label.grid(row=6, column=0, padx=10, pady=5, sticky="e")

new_progress_slider = tk.Scale(modify_goal_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=200, resolution=1,  bg=background_color)
new_progress_slider.grid(row=6, column=1, padx=10, pady=(0, 10), sticky="w")


# Create a style for the Treeview
style = ttk.Style()
style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

# Functionality for the "Modify Goal" tab
goal_tree = ttk.Treeview(modify_goal_frame, columns=('Goal ID', 'Goal Name', 'Deadline', 'Progress'), show='headings', height=5)
goal_tree.heading('Goal ID', text='Goal ID')
goal_tree.heading('Goal Name', text='Goal Name')
goal_tree.heading('Deadline', text='Deadline')
goal_tree.heading('Progress', text='Progress')

# Set style for the Treeview
goal_tree.tag_configure('oddrow', background='#E8E8E8')
goal_tree.tag_configure('evenrow', background='#FFFFFF')

# Set column alignment to center
for col in ('Goal ID', 'Goal Name', 'Deadline', 'Progress'):
    goal_tree.column(col, anchor='center', width=100)  # Adjust width as needed

goal_tree.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")  # Adjusted columnspan to 2

# Scrollbar for the treeview
tree_scroll = ttk.Scrollbar(modify_goal_frame, orient='vertical', command=goal_tree.yview)
tree_scroll.grid(row=0, column=2, pady=10, sticky='ns')
goal_tree.configure(yscrollcommand=tree_scroll.set)

# Bind the function to the selection event of the goal_tree
goal_tree.bind("<<TreeviewSelect>>", populate_widgets_on_select)

# Populate the goals list in the "Select Goal to Modify" box
populate_goals_list()

# Apply styles to the Treeview
goal_tree.tag_configure('oddrow', background='#E8E8E8')
goal_tree.tag_configure('evenrow', background='#FFFFFF')

modify_button = tk.Button(modify_goal_frame, text='Modify Goal', fg=text_color, bg=button_color, command=modify_goal)
modify_button.grid(row=12, column=0, columnspan=2, padx=10, pady=(0,10), sticky="s")

background_label_modify_goal = tk.Label(background_frame_modify_goal, image=background_photo)
background_label_modify_goal.place(relx=0.5, rely=0.5, anchor='center')

# Open the image with Pillow
image3_path = 'goals1.png'
original_image3 = Image.open(image3_path)

# Calculate the new height to maintain the aspect ratio
new_width3 = 240  # Set your desired width
aspect_ratio3 = original_image3.width / float(original_image3.height)
new_height3 = int(new_width3 / aspect_ratio3)

# Resize the image
resized_image3 = original_image3.resize((new_width3, new_height3))

# Convert the Pillow image to a PhotoImage
image3 = ImageTk.PhotoImage(resized_image3)

# Functionality for the "Each Goal Progress" tab
goal_name_view_label = tk.Label(view_progress_frame, text='Goal Name:', fg=text_color, bg=background_color)
goal_name_view_label.grid(row=1, column=0, padx=(0, 10), pady=(10, 5), sticky="e")

# Create a combobox for goal selection
goal_name_view_combobox = ttk.Combobox(view_progress_frame, width=30, postcommand=lambda: update_goal_dropdown(goal_name_view_combobox.get()))
# Fetch goal names from the database and populate the Combobox
try:
    cursor = db.cursor()
    sql = "SELECT goal_name FROM goals"
    cursor.execute(sql)
    results = cursor.fetchall()

    if results:
        goal_names = [result[0] for result in results]
        goal_name_view_combobox['values'] = goal_names
    else:
        goal_name_view_combobox['values'] = ["No goals found."]

except mysql.connector.Error as e:
    goal_name_view_combobox['values'] = ["Error fetching goals."]
goal_name_view_combobox.grid(row=1, column=1, padx=(0, 10), pady=(10, 5), sticky="w")
goal_name_view_combobox.set("Type to search goal")

goal_detail_view_label = tk.Label(view_progress_frame, text='Goal Details:', fg=text_color, bg=background_color)
goal_detail_view_label.grid(row=2, column=0, padx=(0, 10), pady=(10, 5), sticky="e")

progress_text = tk.Text(view_progress_frame, height=3, width=40, wrap='word', fg=text_color, bg="white",
                        font=('Helvetica', 14))
progress_text.grid(row=2, column=1, padx=(0, 10), pady=(10, 5), sticky="e")

view_progress_button = tk.Button(view_progress_frame, text='View Progress', fg=text_color, bg=button_color, command=view_progress)
view_progress_button.grid(row=3, column=1, padx=(0, 10), pady=(10, 5), sticky="w")

# Button to show the progress graph
show_graph_button = tk.Button(view_progress_frame, text='Show Progress Graph', fg=text_color, bg=button_color, command=show_progress_graph)
show_graph_button.grid(row=3, column=1, padx=(0, 10), pady=(10, 5), sticky="e")

image_button2 = tk.Button(view_progress_frame, image=image3, command=lambda: None, bd=0, borderwidth=0)
image_button2.grid(row=1, rowspan=3, column=3, padx=(0, 10), pady=(10, 5), sticky="w")

# Open the image with Pillow
image2_path = 'goals.png'
original_image2 = Image.open(image2_path)

# Calculate the new height to maintain the aspect ratio
new_width2 = 300  # Set your desired width
aspect_ratio2 = original_image2.width / float(original_image2.height)
new_height2 = int(new_width2 / aspect_ratio2)

# Resize the image
resized_image2 = original_image2.resize((new_width2, new_height2))

# Convert the Pillow image to a PhotoImage
image2 = ImageTk.PhotoImage(resized_image2)

# Functionality for the "Overall Progress" tab
overall_progress_button = tk.Button(overall_progress_frame, text='View All Goals', fg=text_color, bg=button_color, command=overall_progress)
overall_progress_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

generate_report_button = tk.Button(overall_progress_frame, text='Generate Overall Report', fg=text_color, bg=button_color, command=view_overall_progress_report)
generate_report_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

background_label_view_progress = tk.Label(background_frame_view_progress, image=background_photo)
background_label_view_progress.place(relx=0.5, rely=0.5, anchor='center')

# Create a frame for the "Overall Progress" tab
overall_progress_tree_frame = tk.Frame(overall_progress_frame, bg=background_color)
overall_progress_tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
# Functionality for the "Overall Progress" tab
overall_progress_tree = ttk.Treeview(overall_progress_tree_frame, columns=('Goal Name', 'Description', 'Deadline'),
                                     show='headings', height=10)
overall_progress_tree.heading('Goal Name', text='Goal Name')
overall_progress_tree.heading('Description', text='Description')
overall_progress_tree.heading('Deadline', text='Deadline')
# overall_progress_tree.heading('Goal ID', text='Goal ID')

# Set column alignment to center
for col in ('Goal Name', 'Description', 'Deadline'):
    overall_progress_tree.column(col, anchor='center', width=100)  # Adjust width as needed

overall_progress_tree.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

# Scrollbar for the overall progress treeview
overall_progress_tree_scroll = ttk.Scrollbar(overall_progress_tree_frame, orient='vertical', command=overall_progress_tree.yview)
overall_progress_tree_scroll.grid(row=0, column=2, pady=10, sticky='ns')
overall_progress_tree.configure(yscrollcommand=overall_progress_tree_scroll.set)

image_button2 = tk.Button(overall_progress_frame, image=image2, command=lambda: None, bd=0, borderwidth=0)
image_button2.grid(row=1, column=2, columnspan=6, sticky="w")

background_label_overall_progress = tk.Label(background_frame_overall_progress, image=background_photo)
background_label_overall_progress.place(relx=0.5, rely=0.5, anchor='center')

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Configure column weights for centering
reminders_frame.columnconfigure(0, weight=1)

# Create Treeviews for upcoming, pending, and completed reminders
columns = ("Goal Name", "Deadline")

upcoming_tree = ttk.Treeview(reminders_frame, columns=columns, show="headings")
pending_tree = ttk.Treeview(reminders_frame, columns=columns, show="headings")
completed_tree = ttk.Treeview(reminders_frame, columns=columns, show="headings")

# Set column headings
for col in columns:
    upcoming_tree.heading(col, text=col, anchor="center")
    pending_tree.heading(col, text=col, anchor="center")
    completed_tree.heading(col, text=col, anchor="center")

# Configure column alignment for Treeviews
for col in columns:
    upcoming_tree.column(col, anchor="center")
    pending_tree.column(col, anchor="center")
    completed_tree.column(col, anchor="center")

# Define tag for alternate row colors
upcoming_tree.tag_configure('evenrow', background='white')
upcoming_tree.tag_configure('oddrow', background='lightgrey')

pending_tree.tag_configure('evenrow', background='white')
pending_tree.tag_configure('oddrow', background='lightgrey')

completed_tree.tag_configure('evenrow', background='white')
completed_tree.tag_configure('oddrow', background='lightgrey')

# Add vertical scrollbar for each treeview
upcoming_scrollbar = ttk.Scrollbar(reminders_frame, orient="vertical", command=upcoming_tree.yview)
pending_scrollbar = ttk.Scrollbar(reminders_frame, orient="vertical", command=pending_tree.yview)
completed_scrollbar = ttk.Scrollbar(reminders_frame, orient="vertical", command=completed_tree.yview)


# Grid layout
upcoming_label = tk.Label(reminders_frame, text="Upcoming Goals:", fg='black', bg='lightblue', font=("Arial", 12, "bold"))
upcoming_label.grid(row=1, column=0, pady=(0, 5), sticky="nsew")

upcoming_tree.grid(row=2, column=0, sticky="nsew")
upcoming_scrollbar.grid(row=2, column=1, sticky="ns")
upcoming_tree.configure(yscrollcommand=upcoming_scrollbar.set)

line1 = tk.Canvas(reminders_frame, width=200, height=1, bg="lightblue")
line1.grid(row=3, column=0, pady=(5, 10), sticky="nsew")

pending_label = tk.Label(reminders_frame, text="Pending Goals:", fg='black', bg='lightcoral', font=("Arial", 12, "bold"))
pending_label.grid(row=4, column=0, pady=(0, 5), sticky="nsew")

pending_tree.grid(row=5, column=0, sticky="nsew")
pending_scrollbar.grid(row=5, column=1, sticky="ns")
pending_tree.configure(yscrollcommand=pending_scrollbar.set)

line2 = tk.Canvas(reminders_frame, width=200, height=1, bg="lightcoral")
line2.grid(row=6, column=0, pady=(5, 10), sticky="nsew")

completed_label = tk.Label(reminders_frame, text="Completed Goals:", fg='black', bg='lightgreen', font=("Arial", 12, "bold"))
completed_label.grid(row=7, column=0, pady=(0, 5), sticky="nsew")

completed_tree.grid(row=8, column=0, sticky="nsew")
completed_scrollbar.grid(row=8, column=1, sticky="ns")
completed_tree.configure(yscrollcommand=completed_scrollbar.set)

# Line separator
line3 = tk.Canvas(reminders_frame, width=200, height=1, bg="lightgreen")
line3.grid(row=9, column=0, pady=(5, 10), sticky="nsew")

# Limit the number of displayed rows
rows_to_display = 3
upcoming_tree["height"] = rows_to_display
pending_tree["height"] = rows_to_display
completed_tree["height"] = rows_to_display

# Button to refresh and categorize reminders
refresh_button = tk.Button(reminders_frame, text="Refresh", command=get_and_categorize_reminders)
refresh_button.grid(row=11, column=0, columnspan=2, pady=10, sticky="s")

# Call the function to initially retrieve and categorize reminders
get_and_categorize_reminders()

# Initially select the "Create Goal" tab
notebook.select(0)

root.mainloop()
