-- Data Definition Language (DDL) for movement db
CREATE TABLE movement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_room VARCHAR(50) NOT NULL,
    end_room VARCHAR(50) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    CONSTRAINT fk_user
    FOREIGN KEY (user_id)
    REFERENCES accounts(user_id)
);
