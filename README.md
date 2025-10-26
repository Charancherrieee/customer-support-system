# Customer Support Ticketing System

A full-stack web application for managing customer support tickets, built as part of Flipkart Internship Project.

**Developer:** Charan Penumarthi  
**Organization:** Flipkart Pvt Ltd  
**Project Duration:** 55 Days

## 📋 Project Overview

This Customer Support Ticketing System allows customers to raise support tickets and enables support teams to manage and resolve them efficiently. The system includes user authentication, ticket management, analytics, and reporting features.

## ✨ Features

### User Portal
- ✅ User registration and login
- ✅ Create support tickets with category, priority, and description
- ✅ View ticket history and track status
- ✅ Add replies to tickets
- ✅ Search tickets
- ✅ Profile management

### Admin Portal
- ✅ View all tickets with filtering options
- ✅ Assign tickets to support agents
- ✅ Update ticket status (Open, In Progress, Resolved, Closed)
- ✅ Update ticket priority
- ✅ Add internal notes
- ✅ Comprehensive analytics dashboard
- ✅ Agent performance metrics

### Analytics & Reports
- 📊 Ticket volume trends
- 📈 Resolution time reports
- 👥 Agent performance dashboard
- 📉 Category-wise ticket distribution
- 🎯 Priority distribution analysis

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Backend:** Python 3.8+, Flask
- **Database:** MySQL
- **Libraries:** 
  - Flask-MySQLdb (Database connection)
  - Flask-Login (Authentication)
  - Flask-Bcrypt (Password hashing)
  - Chart.js (Analytics visualization)

## 📁 Project Structure

```
customer-support-system/
│
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── models.py              # Database models
│   ├── routes/
│   │   ├── auth.py           # Authentication routes
│   │   ├── tickets.py        # Ticket routes
│   │   └── admin.py          # Admin routes
│   ├── utils/
│   │   └── helpers.py
│   └── requirements.txt
│
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── signup.html
│       ├── user/
│       └── admin/
│
├── database/
│   └── schema.sql
│
├── docs/
├── .gitignore
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites

1. **Python 3.8 or higher**
   ```bash
   python --version
   ```

2. **MySQL Server**
   - Download from https://dev.mysql.com/downloads/mysql/
   - Or install XAMPP (includes MySQL)

3. **Git**
   ```bash
   git --version
   ```

### Step-by-Step Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/customer-support-system.git
cd customer-support-system
```

#### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 4. Set Up MySQL Database

**Option A: Using MySQL Command Line**

```bash
mysql -u root -p
```

Then run:
```sql
CREATE DATABASE customer_support_db;
USE customer_support_db;
SOURCE ../database/schema.sql;
```

**Option B: Using MySQL Workbench**
1. Open MySQL Workbench
2. Connect to your MySQL server
3. Go to File → Run SQL Script
4. Select `database/schema.sql`
5. Execute the script

#### 5. Configure Database Connection

Edit `backend/config.py` with your MySQL credentials:

```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'  # Change this
MYSQL_DB = 'customer_support_db'
```

Or create a `.env` file in the backend directory:

```env
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=customer_support_db
```

#### 6. Create Default Admin User

The database schema includes default users. Update their passwords:

```sql
UPDATE users SET password_hash = 'YOUR_HASHED_PASSWORD' WHERE email = 'admin@flipkart.com';
```

Or you can register a new admin user through the application and manually update the role in the database.

#### 7. Run the Application

```bash
cd backend
python app.py
```

The application will be available at: `http://localhost:5000`

## 👤 Default Login Credentials

After setting up, you need to create proper password hashes. For testing, you can:

1. **Register a new account** through signup page
2. **Update role in database:**
```sql
UPDATE users SET role = 'admin' WHERE email = 'your_email@example.com';
```

## 📖 Usage Guide

### For Customers

1. **Sign Up**: Create an account using the signup page
2. **Login**: Access your dashboard
3. **Create Ticket**: Click "New Ticket" and fill in the form
4. **Track Tickets**: View all your tickets and their status
5. **Add Replies**: Communicate with support agents

### For Support Agents/Admins

1. **Login**: Use admin credentials
2. **View Tickets**: See all tickets with filters
3. **Assign Tickets**: Assign tickets to agents
4. **Update Status**: Change ticket status as work progresses
5. **Add Notes**: Add internal notes (not visible to customers)
6. **View Analytics**: Check performance metrics

## 🎯 Key Functionalities

### Ticket Management
- **Priority Levels**: Low, Medium, High, Urgent
- **Status Tracking**: Open → In Progress → Resolved → Closed
- **Categories**: Technical Issue, Billing, Delivery, Returns, etc.
- **Unique Ticket Numbers**: Auto-generated (e.g., TKT20240001)

### Security Features
- Password hashing using Werkzeug security
- Session management with Flask-Login
- CSRF protection with Flask-WTF
- Role-based access control (Customer, Agent, Admin)

## 📊 Database Schema

### Main Tables
- **users**: Store user information and roles
- **tickets**: Store all support tickets
- **categories**: Ticket categories
- **ticket_responses**: Responses and notes
- **ticket_attachments**: File attachments (optional)

### Relationships
- One user can have many tickets
- One ticket belongs to one user
- One ticket can have many responses
- One ticket can be assigned to one agent

## 🔧 Configuration

### Email Notifications (Future Enhancement)
To enable email notifications, add SMTP settings to `config.py`:

```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_app_password'
```

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```
Error: Can't connect to MySQL server
```
**Solution:** Ensure MySQL is running and credentials are correct.

**2. Module Not Found**
```
ModuleNotFoundError: No module named 'flask'
```
**Solution:** Activate virtual environment and install requirements:
```bash
pip install -r requirements.txt
```

**3. Port Already in Use**
```
Address already in use
```
**Solution:** Change port in `app.py` or kill the process using port 5000.

**4. Permission Denied on Uploads**
```
PermissionError: [Errno 13] Permission denied
```
**Solution:** Create uploads directory:
```bash
mkdir backend/uploads
chmod 755 backend/uploads
```

## 📝 Development Roadmap

### Phase 1 (Days 1-20): ✅ Completed
- [x] Database design
- [x] Basic Flask setup
- [x] User authentication
- [x] Ticket CRUD operations

### Phase 2 (Days 21-35): 🚧 In Progress
- [ ] User dashboard templates
- [ ] Ticket creation form
- [ ] Ticket history page

### Phase 3 (Days 36-45): 📅 Planned
- [ ] Admin dashboard
- [ ] Ticket assignment
- [ ] Status management

### Phase 4 (Days 46-55): 📅 Planned
- [ ] Analytics dashboard
- [ ] Reports generation
- [ ] Final testing & documentation

## 🤝 Contributing

This is an internship project. For suggestions or issues, please contact:
- Email: charan.penumarthi@example.com
- Supervisor: Jayanth Pathwari (HR - Flipkart)

## 📄 License

This project is created for educational purposes as part of Flipkart Internship Program.

## 🙏 Acknowledgments

- Flipkart Pvt Ltd for the internship opportunity
- Jayanth Pathwari for project guidance
- Bootstrap team for the UI framework
- Flask community for excellent documentation

---

**Project Status:** 🟢 Active Development  
**Last Updated:** October 2024  
**Next Review:** Day 30