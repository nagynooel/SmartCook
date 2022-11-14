/*
    @package: smartcook
    @author: Noel Nagy
    @website: https://github.com/nagynooel
    ©2022 Noel Nagy - All rights reserved.
*/
/*Create TABLE and INDEX commands for creating new database*/

CREATE TABLE users (
    id INT NOT NULL UNIQUE AUTO_INCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hash VARCHAR(64) NOT NULL,
    salt VARCHAR(5) NOT NULL,
    creation_date DATETIME NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX idx_uid ON users (id);
CREATE UNIQUE INDEX idx_username ON users (username);

CREATE TABLE password_reset_tokens (
    token VARCHAR(86) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expiration_date DATETIME NOT NULL DEFAULT (NOW() + INTERVAL 15 MINUTE),
    used BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (token),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX idx_password_reset_token ON password_reset_tokens (token);