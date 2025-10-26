from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import Ticket, Category, TicketResponse

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard showing ticket overview"""
    mysql = current_app.mysql
    
    # Get user's tickets
    tickets = Ticket.get_user_tickets(mysql, current_user.user_id, limit=5)
    
    # Get ticket statistics
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_count,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
        FROM tickets
        WHERE user_id = %s
    """, (current_user.user_id,))
    stats = cursor.fetchone()
    cursor.close()
    
    return render_template('user/dashboard.html', tickets=tickets, stats=stats)


@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    """Create a new support ticket"""
    mysql = current_app.mysql
    
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        
        # Validation
        errors = []
        
        if not category_id:
            errors.append('Please select a category.')
        
        if not subject or len(subject) < 5:
            errors.append('Subject must be at least 5 characters long.')
        
        if not description or len(description) < 20:
            errors.append('Description must be at least 20 characters long.')
        
        if priority not in ['low', 'medium', 'high', 'urgent']:
            errors.append('Invalid priority level.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            categories = Category.get_all(mysql)
            return render_template('user/create_ticket.html', categories=categories)
        
        try:
            ticket_id, ticket_number = Ticket.create_ticket(
                mysql, current_user.user_id, category_id, subject, description, priority
            )
            flash(f'Ticket {ticket_number} created successfully!', 'success')
            return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    # Get categories for the form
    categories = Category.get_all(mysql)
    return render_template('user/create_ticket.html', categories=categories)


@tickets_bp.route('/my-tickets')
@login_required
def ticket_history():
    """View all user's tickets"""
    mysql = current_app.mysql
    
    # Get filter parameters
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # Get tickets
    tickets = Ticket.get_user_tickets(mysql, current_user.user_id)
    
    # Apply filters
    if status_filter:
        tickets = [t for t in tickets if t['status'] == status_filter]
    if priority_filter:
        tickets = [t for t in tickets if t['priority'] == priority_filter]
    
    return render_template('user/ticket_history.html', tickets=tickets)


@tickets_bp.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    """View ticket details"""
    mysql = current_app.mysql
    
    ticket = Ticket.get_by_id(mysql, ticket_id)
    
    if not ticket:
        flash('Ticket not found.', 'danger')
        return redirect(url_for('tickets.user_dashboard'))
    
    # Check if user owns the ticket or is an agent
    if ticket['user_id'] != current_user.user_id and not current_user.is_agent():
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('tickets.user_dashboard'))
    
    # Get ticket responses
    include_internal = current_user.is_agent()
    responses = TicketResponse.get_ticket_responses(mysql, ticket_id, include_internal)
    
    return render_template('user/view_ticket.html', ticket=ticket, responses=responses)


@tickets_bp.route('/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
def add_reply(ticket_id):
    """Add a reply to a ticket"""
    mysql = current_app.mysql
    
    ticket = Ticket.get_by_id(mysql, ticket_id)
    
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket not found'}), 404
    
    # Check permissions
    if ticket['user_id'] != current_user.user_id and not current_user.is_agent():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    response_text = request.form.get('response_text', '').strip()
    
    if not response_text or len(response_text) < 10:
        return jsonify({'success': False, 'message': 'Response must be at least 10 characters'}), 400
    
    try:
        TicketResponse.add_response(mysql, ticket_id, current_user.user_id, response_text, False)
        flash('Reply added successfully!', 'success')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))


@tickets_bp.route('/search')
@login_required
def search_tickets():
    """Search user's tickets"""
    mysql = current_app.mysql
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('tickets.ticket_history'))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT t.*, c.category_name
        FROM tickets t
        JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s 
        AND (t.subject LIKE %s OR t.description LIKE %s OR t.ticket_number LIKE %s)
        ORDER BY t.created_at DESC
    """, (current_user.user_id, f'%{query}%', f'%{query}%', f'%{query}%'))
    tickets = cursor.fetchall()
    cursor.close()
    
    return render_template('user/ticket_history.html', tickets=tickets, search_query=query)