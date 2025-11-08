from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Ticket, Category, TicketResponse

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/dashboard')
@login_required
def user_dashboard():
    mysql = current_app.mysql
    
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total FROM tickets WHERE user_id = %s
        """, (current_user.user_id,))
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as open_count FROM tickets 
            WHERE user_id = %s AND status = 'open'
        """, (current_user.user_id,))
        open_count = cursor.fetchone()['open_count']
        
        cursor.execute("""
            SELECT COUNT(*) as in_progress_count FROM tickets 
            WHERE user_id = %s AND status = 'in_progress'
        """, (current_user.user_id,))
        in_progress_count = cursor.fetchone()['in_progress_count']
        
        cursor.execute("""
            SELECT COUNT(*) as resolved_count FROM tickets 
            WHERE user_id = %s AND status = 'resolved'
        """, (current_user.user_id,))
        resolved_count = cursor.fetchone()['resolved_count']
        
        cursor.close()
        
        stats = {
            'total': total,
            'open_count': open_count,
            'in_progress_count': in_progress_count,
            'resolved_count': resolved_count
        }
        
        tickets = Ticket.get_user_tickets(mysql, current_user.user_id, limit=5)
        
        return render_template('dashboard.html', stats=stats, tickets=tickets)
    
    except Exception as e:
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('index'))

@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    mysql = current_app.mysql
    categories = Category.get_all(mysql)
    
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        subject = request.form.get('subject')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        
        if not category_id or not subject or not description:
            flash('All fields are required.', 'danger')
            return redirect(url_for('tickets.create_ticket'))
        
        if len(subject) < 5 or len(subject) > 200:
            flash('Subject must be between 5 and 200 characters.', 'danger')
            return redirect(url_for('tickets.create_ticket'))
        
        if len(description) < 20 or len(description) > 2000:
            flash('Description must be between 20 and 2000 characters.', 'danger')
            return redirect(url_for('tickets.create_ticket'))
        
        try:
            ticket_id, ticket_number = Ticket.create_ticket(
                mysql, current_user.user_id, category_id, subject, description, priority
            )
            flash(f'Ticket {ticket_number} created successfully!', 'success')
            return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
        except Exception as e:
            flash('Error creating ticket.', 'danger')
            return redirect(url_for('tickets.create_ticket'))
    
    return render_template('create_ticket.html', categories=categories)

@tickets_bp.route('/history')
@login_required
def ticket_history():
    mysql = current_app.mysql
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    
    filters = {}
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    
    tickets = Ticket.get_user_tickets(mysql, current_user.user_id)
    
    if filters:
        if 'status' in filters:
            tickets = [t for t in tickets if t['status'] == filters['status']]
        if 'priority' in filters:
            tickets = [t for t in tickets if t['priority'] == filters['priority']]
    
    return render_template('ticket_history.html', tickets=tickets)

@tickets_bp.route('/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    mysql = current_app.mysql
    ticket = Ticket.get_by_id(mysql, ticket_id)
    
    if not ticket:
        flash('Ticket not found.', 'danger')
        return redirect(url_for('tickets.ticket_history'))
    
    if not current_user.is_agent() and ticket['user_id'] != current_user.user_id:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('tickets.ticket_history'))
    
    responses = TicketResponse.get_ticket_responses(mysql, ticket_id, include_internal=current_user.is_agent())
    
    return render_template('view_ticket.html', ticket=ticket, responses=responses)

@tickets_bp.route('/<int:ticket_id>/reply', methods=['POST'])
@login_required
def add_reply(ticket_id):
    mysql = current_app.mysql
    ticket = Ticket.get_by_id(mysql, ticket_id)
    
    if not ticket:
        flash('Ticket not found.', 'danger')
        return redirect(url_for('tickets.ticket_history'))
    
    if not current_user.is_agent() and ticket['user_id'] != current_user.user_id:
        flash('You do not have permission to reply to this ticket.', 'danger')
        return redirect(url_for('tickets.ticket_history'))
    
    response_text = request.form.get('response_text')
    
    if not response_text or len(response_text) < 10:
        flash('Response must be at least 10 characters.', 'danger')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    
    try:
        TicketResponse.add_response(mysql, ticket_id, current_user.user_id, response_text)
        
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE tickets SET updated_at = NOW() WHERE ticket_id = %s",
            (ticket_id,)
        )
        mysql.connection.commit()
        cursor.close()
        
        flash('Reply added successfully!', 'success')
    except Exception as e:
        flash('Error adding reply.', 'danger')
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
