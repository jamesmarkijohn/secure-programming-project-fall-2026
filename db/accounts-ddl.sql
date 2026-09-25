-- Data Definition Language (DDL) for accounts db
CREATE TABLE accounts (
    user_id INTEGER AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(254) DEFAULT NULL,
    password VARCHAR(128) NOT NULL,
    full_name VARCHAR(100) DEFAULT NULL,
    phone_number INTEGER(15) DEFAULT NULL,
    created TIMESTAMP NOT NULL,
    role VARCHAR(8) NOT NULL
);

-- will add MFA fields later
