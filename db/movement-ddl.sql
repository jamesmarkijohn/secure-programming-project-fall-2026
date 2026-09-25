-- Data Definition Language (DDL) for movement db
CREATE TABLE movement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    start_room VARCHAR(50) NOT NULL,
    end_room VARCHAR(50) NOT NULL,
    event_time TIMESTAMP NOT NULL
);
