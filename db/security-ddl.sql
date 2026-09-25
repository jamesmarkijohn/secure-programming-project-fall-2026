-- Data Definition Language (DDL) for security db
CREATE TABLE security (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_time TIMESTAMP NOT NULL,
    username VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_desc VARCHAR(255) DEFAULT NULL
);
