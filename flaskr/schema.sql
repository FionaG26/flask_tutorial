-- Drop the tables if they exist
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS user;

-- Create the user table
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Create the post table
CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    summary TEXT,
    image TEXT,
    category TEXT,
    tags TEXT,
    publish_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    seo_title TEXT,
    seo_description TEXT,
    seo_keywords TEXT,
    FOREIGN KEY (author_id) REFERENCES user (id)
);
