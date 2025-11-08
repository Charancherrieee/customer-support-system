from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import Ticket, Category, User, TicketResponse
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def agent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_agent():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@agent_required
def dashboard():
    mysql = current_app.mysql
    
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM tickets")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as open_count FROM tickets WHERE status = 'open'")
        open_count = cursor.fetchone()['open_count']
        
        cursor.execute("SELECT COUNT(*) as in_progress_count FROM tickets WHERE status = 'in_progress'")
        in_progress_count = cursor.fetchone()['in_progress_count']
        
        cursor.execute("SELECT COUNT(*) as resolved_count FROM tickets WHERE status = 'resolved'")
        resolved_count = cursor.fetchone()['resolved_count']
        
        cursor.close()
        
        stats = {
            'total': total,
            'open_count': open_count,
            'in_progress_count': in_progress_count,
            'resolved_count': resolved_count
        }
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT priority, COUNT(*) as count FROM tickets 
            WHERE status IN ('open', 'in_progress')
            GROUP BY priority
        """)
        priority_stats = cursor.fetchall()
        cursor.close()
        
        recent_tickets = Ticket.get_all_tickets(mysql, limit=5)
        
        return render_template('dashboard.html', stats=stats, priority_stats=priority_stats, recent_tickets=recent_tickets)
    
    except Exception as e:
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('index'))

@admin_bp.route('/tickets')
@login_required
@agent_required
def tickets():
    mysql = current_app.mysql
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    category_id = request.args.get('category')
    assigned = request.args.get('assigned', '')
    
    filters = {}
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    if category_id:
        filters['category_id'] = category_id
    if assigned:
        filters['assigned_to'] = assigned
    
    per_page = 10
    offset = (page - 1) * per_page
    
    try:
        total_tickets = Ticket.get_ticket_count(mysql, filters)
        total_pages = (total_tickets + per_page - 1) // per_page
        tickets_list = Ticket.get_all_tickets(mysql, filters, limit=per_page, offset=offset)
        categories = Category.get_all(mysql)
        agents = User.get_all_agents(mysql)
        
        return render_template('tickets.html', 
                             tickets=tickets_list, 
                             categories=categories, 
                             agents=agents,
                             page=page, 
                             total_pages=total_pages,
                             filters=filters)
    except Exception as e:
        flash('Error loading tickets.', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/tickets/<int:ticket_id>/status', methods=['POST'])
@login_required
@agent_required
def update_status(ticket_id):
    mysql = current_app.mysql
    new_status = request.form.get('status')
    
    try:
        updates = {'status': new_status, 'updated_at': datetime.now()}
        if new_status == 'resolved':
            updates['resolved_at'] = datetime.now()
        if new_status == 'closed':
            updates['closed_at'] = datetime.now()
        
        Ticket.update_ticket(mysql, ticket_id, updates)
        flash('Ticket status updated successfully!', 'success')
    except Exception as e:
        flash('Error updating ticket status.', 'danger')
    
    return redirect(url_for('admin.tickets'))

@admin_bp.route('/tickets/<int:ticket_id>/priority', methods=['POST'])
@login_required
@agent_required
def update_priority(ticket_id):
    mysql = current_app.mysql
    new_priority = request.form.get('priority')
    
    try:
        Ticket.update_ticket(mysql, ticket_id, {'priority': new_priority, 'updated_at': datetime.now()})
        flash('Ticket priority updated successfully!', 'success')
    except Exception as e:
        flash('Error updating ticket priority.', 'danger')
    
    return redirect(url_for('admin.tickets'))

@admin_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
@login_required
@agent_required
def assign_ticket(ticket_id):
    mysql = current_app.mysql
    agent_id = request.form.get('agent_id')
    
    try:
        Ticket.update_ticket(mysql, ticket_id, {'assigned_to': agent_id, 'updated_at': datetime.now()})
        flash('Ticket assigned successfully!', 'success')
    except Exception as e:
        flash('Error assigning ticket.', 'danger')
    
    return redirect(url_for('admin.tickets'))

@admin_bp.route('/tickets/<int:ticket_id>/internal-note', methods=['POST'])
@login_required
@agent_required
def add_internal_note(ticket_id):
    mysql = current_app.mysql
    note_text = request.form.get('note_text')
    
    if not note_text or len(note_text) < 5:
        flash('Note must be at least 5 characters.', 'danger')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    
    try:
        TicketResponse.add_response(mysql, ticket_id, current_user.user_id, note_text, is_internal=True)
        flash('Internal note added successfully!', 'success')
    except Exception as e:
        flash('Error adding internal note.', 'danger')
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))

@admin_bp.route('/analytics')
@login_required
@agent_required
def analytics():
    mysql = current_app.mysql
    days = request.args.get('days', 30, type=int)
    
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM tickets 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY status
        """, (days,))
        status_distribution = cursor.fetchall()
        
        cursor.execute("""
            SELECT category_name, COUNT(*) as count FROM tickets t
            JOIN categories c ON t.category_id = c.category_id
            WHERE t.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY c.category_id, c.category_name
            ORDER BY count DESC
        """, (days,))
        category_stats = cursor.fetchall()
        
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count FROM tickets
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (days,))
        volume_trend = cursor.fetchall()
        
        cursor.execute("""
            SELECT priority, AVG(HOUR(TIMEDIFF(resolved_at, created_at))) as avg_hours, COUNT(*) as count 
            FROM tickets
            WHERE status = 'resolved' AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY priority
        """, (days,))
        resolution_times = cursor.fetchall()
        
        cursor.execute("""
            SELECT u.full_name, COUNT(t.ticket_id) as total_assigned,
                   SUM(CASE WHEN t.status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                   SUM(CASE WHEN t.status = 'closed' THEN 1 ELSE 0 END) as closed,
                   AVG(HOUR(TIMEDIFF(t.resolved_at, t.created_at))) as avg_resolution_hours
            FROM users u
            LEFT JOIN tickets t ON u.user_id = t.assigned_to
            WHERE u.role IN ('agent', 'admin')
            GROUP BY u.user_id, u.full_name
        """)
        agent_performance = cursor.fetchall()
        
        cursor.close()
        
        return render_template('analytics.html', 
                             status_distribution=status_distribution,
                             category_stats=category_stats,
                             volume_trend=volume_trend,
                             resolution_times=resolution_times,
                             agent_performance=agent_performance,
                             days=days)
    
    except Exception as e:
        flash('Error loading analytics.', 'danger')
        return redirect(url_for('admin.dashboard'))
