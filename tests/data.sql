-- tests/data.sql

INSERT INTO user (id, username, password)
VALUES (1, 'test', 'pbkdf2:sha256:150000$8Jd3bKuw$9e6efbf8b1bb4b5fbad5e4f441c1232bb1e5ed295d5dff99b0a91a0c5e45e293'); -- Replace with actual hash

INSERT INTO post (id, title, body, created, author_id)
VALUES (1, 'test title', 'test\nbody', '2023-01-01', 1);
