# Grand Hotel Management System 🏨

A robust, fully relational database-driven web application designed to automate and streamline hospitality management. Built with Python, Flask, and MySQL, this system acts as a centralized dashboard for hotel staff to manage guests, rooms, extra services, and automated billing.

## ✨ Features

- **Guest & Reservation Lifecycle:** Seamlessly book guests, assign them to specific room categories, and track their real-time status (Booked, Checked-In, Checked-Out).
- **Service & Inventory Tracking:** Add custom services (e.g., Spa, Room Service) and apply dynamic charges directly to a guest's tab.
- **Automated Financial Engine:** A foolproof checkout system that automatically calculates stay duration, room costs, aggregates service charges, applies a 10% tax, and generates an itemized final invoice.
- **Staff Portals:** Secure staff tracking with personalized dashboards displaying assigned active guests.
- **Modern UI:** Clean, responsive, and professional interface styled with Tailwind CSS.

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask
- **Database:** MySQL (Relational schema with strict foreign key constraints)
- **Frontend:** HTML5, Jinja2 Templating, Tailwind CSS
- **Database Connector:** mysql-connector-python

## 📂 Project Structure

GRANDHOTEL_FLASK/
│
├── static/               # CSS, JavaScript, and Image assets
├── templates/            # Jinja2 HTML templates (base.html, app pages)
├── .env                  # Environment variables (Database credentials)
├── .gitignore            # Git exclusion rules
├── app.py                # Main Flask application and routing logic
├── db.py                 # Database connection handling
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation


## 🚀 Installation & Setup

Follow these steps to run the application on your local machine.

### 1. Prerequisites
- Python 3.x installed
- MySQL Server & MySQL Workbench installed

### 2. Database Setup
1. Open MySQL Workbench.
2. Create a new schema named HotelSystem.
3. Run the provided project SQL scripts to generate the tables (Rooms, Guests, Reservations, Services, ServiceCharges, Invoices, Staff).

### 3. Application Setup
Clone the repository and navigate into the project directory:


git clone <your-repository-url>
cd GRANDHOTEL_FLASK


Create and activate a virtual environment:

# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate


Install the required Python dependencies:

pip install -r requirements.txt


### 4. Environment Variables
Create a `.env` file in the root directory and add your MySQL database credentials:


DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=HotelSystem
SECRET_KEY=your_secret_flask_key


### 5. Run the Application
Start the Flask development server:

python app.py

Open your web browser and navigate to http://127.0.0.1:5000 to access the dashboard.

## 🛡️ License
This project was created for academic purposes as part of a Database Management Systems (DBMS) curriculum.
```
