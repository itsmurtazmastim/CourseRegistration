DO $$
BEGIN
 IF NOT EXISTS(SELECT FROM pg_database WHERE datname = 'courseregistrationservice') THEN
    CREATE DATABASE courseregistrationservice;
    GRANT ALL PRIVILEGES ON DATABASE courseregistrationservice TO postgres;
 END IF;
END $$;
