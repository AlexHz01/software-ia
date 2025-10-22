import psycopg2
from config.config_manager import config_manager

def crear_base_datos():
    """Crear la base de datos PostgreSQL si no existe"""
    pg_config = config_manager.get_postgres_config()
    
    try:
        # Conectar a PostgreSQL (sin especificar base de datos)
        conn = psycopg2.connect(
            host=pg_config['host'],
            port=pg_config['puerto'],
            user=pg_config['usuario'],
            password=pg_config['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{pg_config['nombre_bd']}'")
        existe = cursor.fetchone()
        
        if not existe:
            cursor.execute(f'CREATE DATABASE {pg_config["nombre_bd"]}')
            print(f"✅ Base de datos '{pg_config['nombre_bd']}' creada")
        else:
            print(f"✅ Base de datos '{pg_config['nombre_bd']}' ya existe")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")

if __name__ == "__main__":
    crear_base_datos()