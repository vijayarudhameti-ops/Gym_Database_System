# Gym Management System

This project is a "Gym Membership Management System" developed for the Database Management System (UE23CS351A) miniproject.

It is a complete, deployable database application built with Python and Tkinter. It provides a full-featured graphical user interface (GUI) for gym staff to manage members, trainers, membership plans, payments, and equipment. The application connects to a MySQL database to perform all necessary CRUD (Create, Read, Update, Delete) operations.

## 🚀 Key Features

This application provides a tab-based interface to manage all aspects of the gym:

* **Member Management:** Full CRUD operations for members, including name, date of birth, gender, and contact info. It also links members to specific trainers.
* **Trainer Management:** Add, update, and view trainers and their contact details.
* **Plan Management:** Create and manage various membership plans, including their name, duration (in months), and fee.
* **Enrollment:** Enroll members into specific plans. This action automatically **triggers** a popup to confirm the member's new total due and creates a "Pending" payment record.
* **Payment Processing:** Log all member payments, including amount, date, mode, and status (Pending, Completed, Failed).
* **PDF Receipt Generation:** Select any payment record and generate a PDF (or .txt fallback) receipt, which dynamically fetches the member's name and plan details.
* **Pending Payments Dashboard:** A dedicated tab that **joins** the `payment` and `member` tables to show a live list of all payments marked as "Pending." Staff can select a pending payment and mark it as "Completed," which updates its status across the application.
* **Attendance Tracking:** Log member attendance (Present/Absent) for specific dates.
* **Equipment Inventory:** Manage the gym's equipment, including its condition, purchase date, and the trainer responsible for it.
* **Trainer Specialization:** Assign one or more specializations to each trainer.

## 🛠️ Technologies Used

As required by the project deliverables, the following technologies were used:
* **Language:** Python 3
* **Database:** MySQL
* **GUI:** Tkinter (via `tkinter.ttk`)
* **Python-MySQL Connector:** `mysql-connector-python`
* **PDF Generation:** `reportlab`

## 📦 Database & SQL Features

This project meets the requirements for advanced database design:
* **ER Diagram & Relational Schema:** The database design (ERD and Schema) is included in the final project report.
* **SQL Functions:** A custom SQL function, `fn_calculate_member_age`, is created and called from the application to display the member's age in the Members tab.
* **SQL Triggers:** Triggers are implemented in the database. For example, when a new enrollment is inserted, a trigger fires to update the member's total due and automatically create a corresponding 'Pending' payment in the `payment` table.
* **Join Queries:** The application uses `JOIN` queries, most notably in the "Pending Payments" dashboard, to display the member's name alongside their payment details.
* **Aggregate Queries:** The `SUM()` aggregate function is used to calculate a member's total outstanding fees when they enroll in a new plan.

## ⚙️ Setup and Installation

To run this application, you will need Python 3 and a running MySQL server.

### 1. Database Setup

1.  Open your MySQL server (e.g., via MySQL Workbench, command line, or XAMPP).
2.  Create a new database named `gym_db`.
3.  Import the provided `.sql` file (e.g., `gym_db_backup.sql`) into your new `gym_db` database. This file contains all the DDL commands (tables), functions, and triggers needed to run the project.

### 2. Install Python Dependencies

This project requires two external Python libraries. You can install them using `pip`:

```bash
# Required for connecting to MySQL
pip install mysql-connector-python

# Required for generating PDF receipts
pip install reportlab

3. Configure Credentials
In the gym_app.py file, locate the DB_CONFIG dictionary and enter your MySQL username and password:

DB_CONFIG = {
    "host": "localhost",
    "user": "TYPE_YOUR_USER_ID_HERE",  # <-- Your MySQL username
    "password": "TYPE_YOUR_PASSWORD_HERE",  # <-- Your MySQL password
    "database": "gym_db",
    "autocommit": True,
}

4. Run the Application
Once the database is set up and the credentials are in place, you can run the application:
python gym_app.py
