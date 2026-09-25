-- Data Definition Language (DDL) for accounts db
CREATE TABLE accounts (
    username VARCHAR(50) PRIMARY KEY,
    email VARCHAR(254) DEFAULT NULL,
    password VARCHAR(128) NOT NULL,
    full_name VARCHAR(100) DEFAULT NULL,
    phone_number INTEGER(15) DEFAULT NULL,
    created DATE
);

-- will add MFA fields later
