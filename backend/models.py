from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin):
    """User model"""
    
    def __init__(self, user_id, full_name, email, password_hash, phone=None, 
                 role='customer', created_at=None, updated_at=None, is_active=True):
        self.id = user_id
        self.user_id = user_id
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.phone = phone
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at
        self._is_active = is_active
    
    @property
    def is_active(self):
        return self._is_active
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_agent(self):
        return self.role in ['agent', 'admin']
    
    def is_customer(self):
        return self.role == 'customer'
    
    @staticmethod
    def create_user(mysql, full_name, email, password, phone=None, role='customer'):
        cursor = mysql.connection.cursor()
        password_hash = generate_password_hash(password)
        
        query = """
            INSERT INTO users (full_name, email, password_hash, phone, role)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (full_name, email, password_hash, phone, role))
            mysql.connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            return user_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def get_by_id(mysql, user_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data:
            return User(**user_data)
        return None
    
    @staticmethod
    def get_by_email(mysql, email):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if user_data:
            return User(**user_data)
        return None
    
    @staticmethod
    def get_all_agents(mysql):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT user_id, full_name, email, role 
            FROM users 
            WHERE role IN ('agent', 'admin') AND is_active = TRUE
            ORDER BY full_name
        """)
        agents = cursor.fetchall()
        cursor.close()
        return agents


class Ticket:
    """Ticket model"""
    
    def __init__(self, ticket_id=None, ticket_number=None, user_id=None, 
                 category_id=None, subject=None, description=None, 
                 priority='medium', status='open', assigned_to=None,
                 created_at=None, updated_at=None, resolved_at=None, closed_at=None):
        self.ticket_id = ticket_id
        self.ticket_number = ticket_number
        self.user_id = user_id
        self.category_id = category_id
        self.subject = subject
        self.description = description
        self.priority = priority
        self.status = status
        self.assigned_to = assigned_to
        self.created_at = created_at
        self.updated_at = updated_at
        self.resolved_at = resolved_at
        self.closed_at = closed_at
    
    @staticmethod
    def generate_ticket_number(mysql):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM tickets")
        result = cursor.fetchone()
        count = result['count'] + 1
        cursor.close()
        
        year = datetime.now().year
        ticket_number = f"TKT{year}{count:06d}"
        return ticket_number
    
    @staticmethod
    def create_ticket(mysql, user_id, category_id, subject, description, priority='medium'):
        cursor = mysql.connection.cursor()
        ticket_number = Ticket.generate_ticket_number(mysql)
        
        query = """
            INSERT INTO tickets (ticket_number, user_id, category_id, subject, description, priority)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (ticket_number, user_id, category_id, subject, description, priority))
            mysql.connection.commit()
            ticket_id = cursor.lastrowid
            cursor.close()
            return ticket_id, ticket_number
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def get_by_id(mysql, ticket_id):
        cursor = mysql.connection.cursor()
        query = """
            SELECT t.*, u.full_name as customer_name, u.email as customer_email,
                   c.category_name, a.full_name as assigned_agent_name
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN users a ON t.assigned_to = a.user_id
            WHERE t.ticket_id = %s
        """
        cursor.execute(query, (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        return ticket
    
    @staticmethod
    def get_user_tickets(mysql, user_id, limit=None):
        cursor = mysql.connection.cursor()
        query = """
            SELECT t.*, c.category_name
            FROM tickets t
            JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (user_id,))
        tickets = cursor.fetchall()
        cursor.close()
        return tickets
    
    @staticmethod
    def get_all_tickets(mysql, filters=None, limit=None, offset=0):
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT t.*, u.full_name as customer_name, c.category_name,
                   a.full_name as assigned_agent_name
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN users a ON t.assigned_to = a.user_id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND t.status = %s"
                params.append(filters['status'])
            if filters.get('priority'):
                query += " AND t.priority = %s"
                params.append(filters['priority'])
            if filters.get('assigned_to'):
                query += " AND t.assigned_to = %s"
                params.append(filters['assigned_to'])
            if filters.get('category_id'):
                query += " AND t.category_id = %s"
                params.append(filters['category_id'])
        
        query += " ORDER BY t.created_at DESC"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, params)
        tickets = cursor.fetchall()
        cursor.close()
        return tickets
    
    @staticmethod
    def update_ticket(mysql, ticket_id, updates):
        cursor = mysql.connection.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        values = list(updates.values())
        values.append(ticket_id)
        
        query = f"UPDATE tickets SET {set_clause} WHERE ticket_id = %s"
        
        try:
            cursor.execute(query, values)
            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def get_ticket_count(mysql, filters=None):
        cursor = mysql.connection.cursor()
        query = "SELECT COUNT(*) as count FROM tickets WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = %s"
                params.append(filters['status'])
            if filters.get('user_id'):
                query += " AND user_id = %s"
                params.append(filters['user_id'])
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result['count']


class Category:
    """Category model"""
    
    @staticmethod
    def get_all(mysql):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY category_name")
        categories = cursor.fetchall()
        cursor.close()
        return categories
    
    @staticmethod
    def get_by_id(mysql, category_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM categories WHERE category_id = %s", (category_id,))
        category = cursor.fetchone()
        cursor.close()
        return category


class TicketResponse:
    """Response model"""
    
    @staticmethod
    def add_response(mysql, ticket_id, user_id, response_text, is_internal=False):
        cursor = mysql.connection.cursor()
        query = """
            INSERT INTO ticket_responses (ticket_id, user_id, response_text, is_internal)
            VALUES (%s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (ticket_id, user_id, response_text, is_internal))
            mysql.connection.commit()
            response_id = cursor.lastrowid
            cursor.close()
            return response_id
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            raise e
    
    @staticmethod
    def get_ticket_responses(mysql, ticket_id, include_internal=False):
        cursor = mysql.connection.cursor()
        query = """
            SELECT tr.*, u.full_name as responder_name, u.role as responder_role
            FROM ticket_responses tr
            JOIN users u ON tr.user_id = u.user_id
            WHERE tr.ticket_id = %s
        """
        if not include_internal:
            query += " AND tr.is_internal = FALSE"
        
        query += " ORDER BY tr.created_at ASC"
        
        cursor.execute(query, (ticket_id,))
        responses = cursor.fetchall()
        cursor.close()
        return responses
