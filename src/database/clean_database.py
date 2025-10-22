import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

def clean_database():
    print("🧹 Limpiando base de datos...")
    
    try:
        db = DatabaseManager()
        
        # Forzar recreación de la base de datos
        if db.tipo_bd == "sqlite":
            sqlite_config = db.get_sqlite_config()
            ruta_db = sqlite_config['ruta_db']
            
            if os.path.exists(ruta_db):
                # Cerrar conexiones
                db.Session.remove()
                db.engine.dispose()
                
                # Eliminar archivo
                os.remove(ruta_db)
                print("🗑️ Base de datos SQLite eliminada")
            
            # Reconectar y recrear
            db.engine = db._crear_engine()
            db.Session = db.scoped_session(db.sessionmaker(bind=db.engine))
            db.Base.metadata.create_all(db.engine)
            print("✅ Base de datos recreada exitosamente")
        
        print("🎉 Base de datos limpiada y lista para usar!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_database()