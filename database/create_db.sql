--SELECT 'CREATE DATABASE courseregistrationservice'
--WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'courseregistrationservice')\gexec;

--GRANT ALL PRIVILEGES ON DATABASE courseregistrationservice TO postgres;
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'courseregistrationservice') THEN
    CREATE DATABASE courseregistrationservice;
    GRANT ALL PRIVILEGES ON DATABASE courseregistrationservice TO postgres;
  END IF;
END $$;