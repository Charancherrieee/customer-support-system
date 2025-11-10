# Customer Support Ticketing System

A web-based customer support system built with Python Flask and MySQL.

## Features

- User registration and login
- Create and manage support tickets
- View ticket status and history
- Admin dashboard with statistics
- Assign tickets to support agents
- Track ticket resolution time
- Role-based access control

## Technology Stack

- Backend: Python Flask
- Database: MySQL
- Frontend: HTML5, CSS3, JavaScript
- Framework: Bootstrap 5

## Installation

### Requirements

- Python 3.8+
- MySQL 5.7+
- Git

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/Charancherrieee/customer-support-system.git
cd customer-support-system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Setup database:
```bash
mysql -u root -p
CREATE DATABASE customer_support_db;
USE customer_support_db;
SOURCE database/schema.sql;
```

5. Configure database connection:

Edit `backend/config.py`:
```python
MYSQL_USER = 'your_username'
MYSQL_PASSWORD = 'your_password'
MYSQL_HOST = 'localhost'
MYSQL_DB = 'customer_support_db'
```

6. Run the application:
```bash
cd backend
python app.py
```

7. Access at: `http://localhost:5000`

## Demo Credentials

Admin Account:
- Email: admin@flipkart.com
- Password: admin123

Agent Account:
- Email: agent1@flipkart.com
- Password: agent123

## Project Structure

```
customer-support-system/
├── backend/
│   ├── app.py              (Main application)
│   ├── config.py           (Configuration)
│   ├── models.py           (Database models)
│   ├── requirements.txt    (Dependencies)
│   └── routes/
│       ├── auth.py         (Authentication)
│       ├── tickets.py      (Ticket management)
│       └── admin.py        (Admin features)
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/
│       └── (14+ HTML templates)
├── database/
│   └── schema.sql
└── docs/
    └── README.md
```

## Key Functions

### User Features
- Register new account
- Login to dashboard
- Create support tickets
- View ticket status
- Reply to tickets

### Admin Features
- View all tickets
- Assign tickets to agents
- Update ticket status
- View performance reports
- Track resolution times

## Database Tables

- users (user accounts)
- tickets (support tickets)
- categories (ticket categories)
- ticket_responses (ticket replies)

## Security

- Password hashing with Werkzeug
- SQL injection prevention
- Session management
- Role-based access control

## Testing

The application has been tested on:
- Windows 10, Windows 11
- Chrome, Firefox, Edge browsers
- Mobile responsive design

## Author

Charan Penumarthi
- Email: 23jr1a12g6@gmail.com
- Phone: 9100544646

## License

Proprietary - Flipkart Pvt Ltd

## Support

For issues or questions, refer to the setup instructions above.
