-- APE Database Initialization Script
-- Run this to create the database and user

-- Create database
CREATE DATABASE ape_db;

-- Create user (if not exists)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ape_user') THEN
      CREATE USER ape_user WITH PASSWORD 'ape_password';
   END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ape_db TO ape_user;

-- Connect to the database
\c ape_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO ape_user;

-- Note: Tables will be created by SQLAlchemy on application startup
-- Run: python -c "from server.database.config import init_db; init_db()"
