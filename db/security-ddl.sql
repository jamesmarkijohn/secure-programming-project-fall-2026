-- Data Definition Language (DDL) for security db
CREATE TABLE security (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_time TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_desc VARCHAR(255) DEFAULT NULL,
    CONSTRAINT fk_user
    FOREIGN KEY (user_id)
    REFERENCES accounts(user_id)
);
