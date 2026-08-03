import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nexora-secret-key-12345_secure_and_random')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Allow Render or other hosted platforms to provide a full database URL.
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Resolve Heroku/Render legacy postgres scheme error
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        print(f"[*] Using database URL from environment: {DATABASE_URL}")
    else:
        # PostgreSQL configurations (can be overridden via environment variables)
        DB_USER = os.environ.get('DB_USER', 'postgres')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = int(os.environ.get('DB_PORT', 5432))
        DB_NAME = os.environ.get('DB_NAME', 'nexora_db')

        # Determine the database URI with a PostgreSQL check
        connected = False
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Check connection to default database to initialize our target database if missing
            connection = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
                database='postgres',
                connect_timeout=2
            )
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
            
            # Create DB if it does not exist
            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f"CREATE DATABASE {DB_NAME}")
                print(f"[*] Created database '{DB_NAME}' in PostgreSQL.")
                
            cursor.close()
            connection.close()

            # Set connection URI
            SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            print(f"[*] PostgreSQL Connected: Database '{DB_NAME}' is ready. Flask will use PostgreSQL.")
            connected = True
        except Exception as e:
            print(f"[!] PostgreSQL connection via psycopg2 failed: {e}")

        if not connected:
            try:
                import pg8000
                
                # Check connection to default database to initialize our target database if missing
                connection = pg8000.dbapi.connect(
                    host=DB_HOST,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    port=DB_PORT,
                    database='postgres',
                    timeout=2
                )
                connection.autocommit = True
                cursor = connection.cursor()
                
                # Create DB if it does not exist
                cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
                exists = cursor.fetchone()
                if not exists:
                    cursor.execute(f"CREATE DATABASE {DB_NAME}")
                    print(f"[*] Created database '{DB_NAME}' in PostgreSQL via pg8000.")
                    
                cursor.close()
                connection.close()

                # Set connection URI with pg8000
                SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                print(f"[*] PostgreSQL Connected (via pg8000): Database '{DB_NAME}' is ready. Flask will use PostgreSQL.")
                connected = True
            except Exception as e_pg:
                print(f"[!] PostgreSQL connection via pg8000 failed: {e_pg}")

        if not connected:
            # Fall back to SQLite for easy local development and fallback stability
            db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'nexora.db')
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
            print(f"[*] Fallback enabled: Flask will use local SQLite database at '{db_path}'.")
