
CREATE DATABASE IF NOT EXISTS customer_support_db;
USE customer_support_db;


CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    role ENUM('customer', 'agent', 'admin') DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_role (role)
);


CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO categories (category_name, description) VALUES
('Technical Issue', 'Technical problems with products or services'),
('Billing', 'Payment and billing related queries'),
('Product Inquiry', 'Questions about products'),
('Account Management', 'Account related issues'),
('Delivery', 'Shipping and delivery concerns'),
('Return/Refund', 'Return and refund requests'),
('Other', 'General inquiries');


CREATE TABLE tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    assigned_to INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_ticket_number (ticket_number),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_created_at (created_at)
);


CREATE TABLE ticket_responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    user_id INT NOT NULL,
    response_text TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_created_at (created_at)
);


CREATE TABLE ticket_attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    uploaded_by INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE CASCADE
);


INSERT INTO users (full_name, email, password_hash, role) VALUES
('Admin User', 'admin@flipkart.com', 'pbkdf2:sha256:260000$default$hash', 'admin');


INSERT INTO users (full_name, email, password_hash, role) VALUES
('Agent One', 'agent1@flipkart.com', 'pbkdf2:sha256:260000$default$hash', 'agent'),
('Agent Two', 'agent2@flipkart.com', 'pbkdf2:sha256:260000$hash', 'agent');


CREATE VIEW ticket_details AS
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.subject,
    t.description,
    t.priority,
    t.status,
    t.created_at,
    t.updated_at,
    t.resolved_at,
    t.closed_at,
    u.full_name AS customer_name,
    u.email AS customer_email,
    c.category_name,
    a.full_name AS assigned_agent,
    TIMESTAMPDIFF(HOUR, t.created_at, COALESCE(t.resolved_at, NOW())) AS resolution_time_hours
FROM tickets t
JOIN users u ON t.user_id = u.user_id
JOIN categories c ON t.category_id = c.category_id
LEFT JOIN users a ON t.assigned_to = a.user_id;


CREATE VIEW agent_performance AS
SELECT 
    u.user_id,
    u.full_name,
    COUNT(t.ticket_id) AS total_tickets_assigned,
    SUM(CASE WHEN t.status = 'resolved' THEN 1 ELSE 0 END) AS tickets_resolved,
    SUM(CASE WHEN t.status = 'closed' THEN 1 ELSE 0 END) AS tickets_closed,
    AVG(TIMESTAMPDIFF(HOUR, t.created_at, t.resolved_at)) AS avg_resolution_time_hours
FROM users u
LEFT JOIN tickets t ON u.user_id = t.assigned_to
WHERE u.role IN ('agent', 'admin')
GROUP BY u.user_id, u.full_name;


DELIMITER //
CREATE PROCEDURE generate_ticket_number(OUT new_ticket_number VARCHAR(20))
BEGIN
    DECLARE ticket_count INT;
    SELECT COUNT(*) INTO ticket_count FROM tickets;
    SET new_ticket_number = CONCAT('TKT', YEAR(NOW()), LPAD(ticket_count + 1, 6, '0'));
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION get_resolution_time(ticket_id_param INT) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE res_time INT;
    SELECT TIMESTAMPDIFF(HOUR, created_at, resolved_at) 
    INTO res_time
    FROM tickets 
    WHERE ticket_id = ticket_id_param;
    RETURN res_time;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER update_resolved_timestamp
BEFORE UPDATE ON tickets
FOR EACH ROW
BEGIN
    IF NEW.status = 'resolved' AND OLD.status != 'resolved' THEN
        SET NEW.resolved_at = NOW();
    END IF;
    IF NEW.status = 'closed' AND OLD.status != 'closed' THEN
        SET NEW.closed_at = NOW();
    END IF;
END //
DELIMITER ;

