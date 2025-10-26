from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import Ticket, User, Category, TicketResponse
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def agent_required(f):
    """Decorator to require agent or admin role"""
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
    """Admin dashboard with ticket overview and statistics"""
    mysql = current_app.mysql
    
    # Get ticket statistics
    cursor = mysql.connection.cursor()
    
    # Overall ticket counts
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_count,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
        FROM tickets
    """)
    stats = cursor.fetchone()
    
    # Priority distribution
    cursor.execute("""
        SELECT priority, COUNT(*) as count
        FROM tickets
        WHERE status NOT IN ('resolved', 'closed')
        GROUP BY priority
    """)
    priority_stats = cursor.fetchall()
    
    # Recent tickets
    cursor.execute("""
        SELECT t.*, u.full_name as customer_name, c.category_name
        FROM tickets t
        JOIN users u ON t.user_id = u.user_id
        JOIN categories c ON t.category_id = c.category_id
        ORDER BY t.created_at DESC
        LIMIT 10
    """)
    recent_tickets = cursor.fetchall()
    
    # Tickets assigned to current user (if agent)
    if not current_user.is_admin():
        cursor.execute("""
            SELECT COUNT(*) as my_tickets
            FROM tickets
            WHERE assigned_to = %s AND status NOT IN ('resolved', 'closed')
        """, (current_user.user_id,))
        my_tickets = cursor.fetchone()
    else:
        my_tickets = {'my_tickets': 0}
    
    cursor.close()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         priority_stats=priority_stats,
                         recent_tickets=recent_tickets,
                         my_tickets=my_tickets)


@admin_bp.route('/tickets')
@login_required
@agent_required
def tickets():
    """View all tickets with filters"""
    mysql = current_app.mysql
    
    # Get filter parameters
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    category_filter = request.args.get('category')
    assigned_filter = request.args.get('assigned')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build filters
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    if priority_filter:
        filters['priority'] = priority_filter
    if category_filter:
        filters['category_id'] = category_filter
    if assigned_filter:
        filters['assigned_to'] = assigned_filter
    
    # Get tickets
    offset = (page - 1) * per_page
    tickets = Ticket.get_all_tickets(mysql, filters, per_page, offset)
    
    # Get total count for pagination
    total_tickets = Ticket.get_ticket_count(mysql, filters)
    total_pages = (total_tickets + per_page - 1) // per_page
    
    # Get categories and agents for filters
    categories = Category.get_all(mysql)
    agents = User.get_all_agents(mysql)
    
    return render_template('admin/tickets.html', 
                         tickets=tickets,
                         categories=categories,
                         agents=agents,
                         page=page,
                         total_pages=total_pages,
                         filters=filters)


@admin_bp.route('/ticket/<int:ticket_id>/assign', methods=['POST'])
@login_required
@agent_required
def assign_ticket(ticket_id):
    """Assign ticket to an agent"""
    mysql = current_app.mysql
    
    agent_id = request.form.get('agent_id')
    
    if not agent_id:
        flash('Please select an agent.', 'danger')
        return redirect(url_for('admin.tickets'))
    
    try:
        Ticket.update_ticket(mysql, ticket_id, {'assigned_to': agent_id})
        flash('Ticket assigned successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))


@admin_bp.route('/ticket/<int:ticket_id>/status', methods=['POST'])
@login_required
@agent_required
def update_status(ticket_id):
    """Update ticket status"""
    mysql = current_app.mysql
    
    new_status = request.form.get('status')
    
    if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    
    try:
        updates = {'status': new_status}
        
        # Set resolved_at timestamp if status is resolved
        if new_status == 'resolved':
            updates['resolved_at'] = datetime.now()
        elif new_status == 'closed':
            updates['closed_at'] = datetime.now()
        
        Ticket.update_ticket(mysql, ticket_id, updates)
        flash(f'Ticket status updated to {new_status}!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))


@admin_bp.route('/ticket/<int:ticket_id>/priority', methods=['POST'])
@login_required
@agent_required
def update_priority(ticket_id):
    """Update ticket priority"""
    mysql = current_app.mysql
    
    new_priority = request.form.get('priority')
    
    if new_priority not in ['low', 'medium', 'high', 'urgent']:
        flash('Invalid priority.', 'danger')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    
    try:
        Ticket.update_ticket(mysql, ticket_id, {'priority': new_priority})
        flash(f'Ticket priority updated to {new_priority}!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))


@admin_bp.route('/ticket/<int:ticket_id>/note', methods=['POST'])
@login_required
@agent_required
def add_internal_note(ticket_id):
    """Add internal note to ticket"""
    mysql = current_app.mysql
    
    note_text = request.form.get('note_text', '').strip()
    
    if not note_text or len(note_text) < 5:
        flash('Note must be at least 5 characters long.', 'danger')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    
    try:
        TicketResponse.add_response(mysql, ticket_id, current_user.user_id, note_text, True)
        flash('Internal note added successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))


@admin_bp.route('/analytics')
@login_required
@agent_required
def analytics():
    """Analytics and reports dashboard"""
    mysql = current_app.mysql
    cursor = mysql.connection.cursor()
    
    # Date range filter
    days = int(request.args.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    # Ticket volume trend (last 30 days)
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM tickets
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY date
    """, (start_date,))
    volume_trend = cursor.fetchall()
    
    # Category distribution
    cursor.execute("""
        SELECT c.category_name, COUNT(t.ticket_id) as count
        FROM categories c
        LEFT JOIN tickets t ON c.category_id = t.category_id
        GROUP BY c.category_id, c.category_name
        ORDER BY count DESC
    """)
    category_stats = cursor.fetchall()
    
    # Average resolution time by priority
    cursor.execute("""
        SELECT priority, 
               AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) as avg_hours,
               COUNT(*) as count
        FROM tickets
        WHERE resolved_at IS NOT NULL
        GROUP BY priority
    """)
    resolution_times = cursor.fetchall()
    
    # Agent performance
    cursor.execute("""
        SELECT u.full_name, u.user_id,
               COUNT(t.ticket_id) as total_assigned,
               SUM(CASE WHEN t.status = 'resolved' THEN 1 ELSE 0 END) as resolved,
               SUM(CASE WHEN t.status = 'closed' THEN 1 ELSE 0 END) as closed,
               AVG(CASE 
                   WHEN t.resolved_at IS NOT NULL 
                   THEN TIMESTAMPDIFF(HOUR, t.created_at, t.resolved_at) 
                   ELSE NULL 
               END) as avg_resolution_hours
        FROM users u
        LEFT JOIN tickets t ON u.user_id = t.assigned_to
        WHERE u.role IN ('agent', 'admin')
        GROUP BY u.user_id, u.full_name
        ORDER BY total_assigned DESC
    """)
    agent_performance = cursor.fetchall()
    
    # Status distribution
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM tickets
        GROUP BY status
    """)
    status_distribution = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/analytics.html',
                         volume_trend=volume_trend,
                         category_stats=category_stats,
                         resolution_times=resolution_times,
                         agent_performance=agent_performance,
                         status_distribution=status_distribution,
                         days=days)