CREATE DATABASE IF NOT EXISTS {DATABASE};
GRANT ALL PRIVILEGES ON {DATABASE}.* TO {USER}@localhost;
GRANT ALL PRIVILEGES ON {DATABASE}.* TO {USER}@localhost IDENTIFIED BY '{USER}';
COMMIT;
