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

/*Recipes*/
CREATE TABLE recipes (
    id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    preparation_time CHAR(4) NOT NULL,
    cook_time CHAR(4) NOT NULL,
    servings INT NOT NULL,
    creation_date DATETIME NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE ingredients (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE measurement_units (
    id INTEGER NOT NULL AUTO_INCREMENT,
    unit VARCHAR(10) NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE recipe_ingredients (
    recipe_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    measurement_id INTEGER NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes (id),
    FOREIGN KEY (measurement_id) REFERENCES measurement_units (id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
);

CREATE TABLE instructions (
    id INTEGER NOT NULL AUTO_INCREMENT,
    recipe_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    instruction VARCHAR(1000) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (recipe_id) REFERENCES recipes (id)
);