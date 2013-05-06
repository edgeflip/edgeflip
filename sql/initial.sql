CREATE USER edgeflip@localhost IDENTIFIED BY 'edgeflip';
CREATE DATABASE edgeflip;
GRANT ALL PRIVILEGES ON edgeflip.* TO edgeflip@localhost;
COMMIT;
