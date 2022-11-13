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