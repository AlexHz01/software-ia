import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
# Importar JSON para SQLite y JSONB para PostgreSQL
from sqlalchemy.dialects.postgresql import JSONB
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os
from config.config_manager import config_manager
from typing import List, Dict, Any, Optional

Base = declarative_base()

# Función para determinar el tipo de columna JSON según el motor de BD
def get_json_column():
    """Retorna JSONB para PostgreSQL, JSON para otros motores"""
    if config_manager.get_tipo_bd() == "postgresql":
        return JSONB
    else:
        return sa.JSON  # Usar JSON nativo de SQLAlchemy para SQLite

class Libro(Base):
    __tablename__ = 'libros'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(500), nullable=False)
    autor = Column(String(300))
    isbn = Column(String(20))
    genero = Column(String(100))
    total_paginas = Column(Integer, default=0)
    total_fragmentos = Column(Integer, default=0)
    fecha_procesado = Column(DateTime, default=datetime.utcnow)
    estado = Column(String(50), default='procesado')
    # Usar la función para determinar el tipo de columna
    metadatos = Column(get_json_column(), default=dict)
    guia_fuente = Column(Text, nullable=True)
    guion_podcast = Column(Text, nullable=True)
    mapa_mental = Column(Text, nullable=True)
    informe_estudio = Column(Text, nullable=True)
    cuestionario = Column(Text, nullable=True)
    ruta_audio_podcast = Column(Text, nullable=True)

class Fragmento(Base):
    __tablename__ = 'fragmentos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    libro_id = Column(Integer, sa.ForeignKey('libros.id'), nullable=False)
    contenido = Column(Text, nullable=False)
    numero_pagina = Column(Integer)
    
    # 🚀 EMBEDDING DINÁMICO CORREGIDO
    if config_manager.get_tipo_bd() == "postgresql":
        from sqlalchemy.dialects.postgresql import ARRAY
        embedding = Column(ARRAY(Float))  # PostgreSQL: array nativo
    else:
        embedding = Column(LargeBinary)  # SQLite: bytes serializados
    
    token_count = Column(Integer, default=0)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    libro = sa.orm.relationship("Libro", backref="fragmentos")
    
class Consulta(Base):
    __tablename__ = 'consultas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(200), nullable=True)  # Nuevo campo para renombrar historial
    pregunta = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)
    # Usar la función para determinar el tipo de columna
    libros_referenciados = Column(get_json_column(), default=list)
    fragmentos_utilizados = Column(get_json_column(), default=list)
    fecha_consulta = Column(DateTime, default=datetime.utcnow)
    modelo_utilizado = Column(String(100))
    tokens_utilizados = Column(Integer, default=0)

class DatabaseManager:
    def __init__(self):
        self.tipo_bd = config_manager.get_tipo_bd()
        self.engine = self._crear_engine()
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self._libros_cache = None
        self._last_cache_update = None
        self.init_database()
    
    def _crear_engine(self):
        """Crear engine de SQLAlchemy según la configuración"""
        if self.tipo_bd == "postgresql":
            pg_config = config_manager.get_postgres_config()
            connection_string = (
                f"postgresql://{pg_config['usuario']}:{pg_config['password']}"
                f"@{pg_config['host']}:{pg_config['puerto']}/{pg_config['nombre_bd']}"
            )
            engine = create_engine(
                connection_string,
                pool_size=pg_config.get('pool_min', 1),
                max_overflow=pg_config.get('pool_max', 10) - pg_config.get('pool_min', 1),
                pool_pre_ping=True
            )
            print("✅ Conectado a PostgreSQL")
        else:
            sqlite_config = config_manager.get_sqlite_config()
            ruta_db = sqlite_config['ruta_db']
            os.makedirs(os.path.dirname(ruta_db), exist_ok=True)
            connection_string = f"sqlite:///{ruta_db}"
            
            # Crear engine con optimizaciones
            engine = create_engine(
                connection_string,
                connect_args={'check_same_thread': False}
            )
            
            # Configurar PRAGMAs para cada conexión (Performance Tuning)
            def set_lite_optimizer(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL") # Write-Ahead Logging
                cursor.execute("PRAGMA synchronous=NORMAL") # Faster writes
                cursor.execute("PRAGMA cache_size=-64000") # 64MB Cache
                cursor.execute("PRAGMA temp_store=MEMORY") # RAM for temp tables
                cursor.close()
                
            sa.event.listen(engine, 'connect', set_lite_optimizer)
            
            print("✅ Conectado a SQLite (Optimizado)")
        
        return engine
    
    def init_database(self):
        try:
            Base.metadata.create_all(self.engine)
            
            # CREAR ÍNDICES PARA BÚSQUEDAS MÁS RÁPIDAS
            if self.tipo_bd == "postgresql":
                # Índices para PostgreSQL
                with self.engine.connect() as conn:
                    # Índice para búsqueda por similitud de embeddings (PostgreSQL)
                    conn.execute(sa.text("""
                        CREATE INDEX IF NOT EXISTS idx_fragmentos_libro_id 
                        ON fragmentos(libro_id);
                    """))
                    conn.execute(sa.text("""
                        CREATE INDEX IF NOT EXISTS idx_libros_fecha 
                        ON libros(fecha_procesado DESC);
                    """))
                    
                    # Índice GIN para búsquedas JSONB (solo PostgreSQL)
                    conn.execute(sa.text("""
                        CREATE INDEX IF NOT EXISTS idx_libros_metadatos 
                        ON libros USING GIN (metadatos);
                    """))
                
                self._configurar_postgres_avanzado()
                    
            else:
                # Índices para SQLite
                with self.engine.connect() as conn:
                    conn.execute(sa.text("""
                        CREATE INDEX IF NOT EXISTS idx_fragmentos_libro_id 
                        ON fragmentos(libro_id);
                    """))
                    conn.execute(sa.text("""
                        CREATE INDEX IF NOT EXISTS idx_libros_titulo 
                        ON libros(titulo);
                    """))
            
            print("✅ Índices de base de datos optimizados")

            # MIGRACIÓN: Agregar columnas si no existen (SQLite)
            if self.tipo_bd == "sqlite":
                with self.engine.connect() as conn:
                    # Verificar columnas en tabla libros
                    cursor = conn.execute(sa.text("PRAGMA table_info(libros)"))
                    columnas = [row[1] for row in cursor.fetchall()]
                    
                    if 'guia_fuente' not in columnas:
                        conn.execute(sa.text("ALTER TABLE libros ADD COLUMN guia_fuente TEXT"))
                        print("➕ Columna 'guia_fuente' agregada a SQLite")
                        
                    if 'guion_podcast' not in columnas:
                        conn.execute(sa.text("ALTER TABLE libros ADD COLUMN guion_podcast TEXT"))
                        print("➕ Columna 'guion_podcast' agregada a SQLite")
                        
                    if 'mapa_mental' not in columnas:
                        conn.execute(sa.text("ALTER TABLE libros ADD COLUMN mapa_mental TEXT"))
                        print("➕ Columna 'mapa_mental' agregada a SQLite")
                        
                    if 'informe_estudio' not in columnas:
                        conn.execute(sa.text("ALTER TABLE libros ADD COLUMN informe_estudio TEXT"))
                        print("➕ Columna 'informe_estudio' agregada a SQLite")
                        
                    if 'cuestionario' not in columnas:
                        conn.execute(sa.text("ALTER TABLE libros ADD COLUMN cuestionario TEXT"))
                        print("➕ Columna 'cuestionario' agregada a SQLite")
                        
                    if 'ruta_audio_podcast' not in columnas:
                        conn.execute(sa.text("ALTER TABLE libros ADD COLUMN ruta_audio_podcast TEXT"))
                        print("➕ Columna 'ruta_audio_podcast' agregada a SQLite")
                
                # Verificar columnas en tabla consultas (SQLite)
                with self.engine.connect() as conn:
                    cursor = conn.execute(sa.text("PRAGMA table_info(consultas)"))
                    columnas = [row[1] for row in cursor.fetchall()]
                    
                    if 'titulo' not in columnas:
                        conn.execute(sa.text("ALTER TABLE consultas ADD COLUMN titulo VARCHAR(200)"))
                        print("➕ Columna 'titulo' agregada a tabla 'consultas' en SQLite")
            
        except Exception as e:
            print(f"❌ Error optimizando índices: {e}")

    def _recrear_base_datos_sqlite(self):
        """Recrear la base de datos SQLite si hay problemas"""
        try:
            sqlite_config = config_manager.get_sqlite_config()
            ruta_db = sqlite_config['ruta_db']
            
            # Cerrar conexiones existentes
            self.Session.remove()
            self.engine.dispose()
            
            # Eliminar archivo de base de datos corrupto
            if os.path.exists(ruta_db):
                os.remove(ruta_db)
                print("🗑️ Base de datos SQLite eliminada (estaba corrupta)")
            
            # Reconectar y recrear
            self.engine = self._crear_engine()
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            Base.metadata.create_all(self.engine)
            print("✅ Base de datos SQLite recreada exitosamente")
            
        except Exception as e:
            print(f"❌ Error recreando base de datos: {e}")
    
    def get_session(self):
        """Obtener una nueva sesión de base de datos"""
        return self.Session()
    
    def agregar_libro(self, titulo: str, autor: str = None, isbn: str = None, 
                     genero: str = None, total_paginas: int = 0, metadata: Dict = None) -> int:
        """Agregar un nuevo libro a la base de datos"""
        session = self.get_session()
        try:
            libro = Libro(
                titulo=titulo,
                autor=autor,
                isbn=isbn,
                genero=genero,
                total_paginas=total_paginas,
                metadatos=metadata or {}
            )
            session.add(libro)
            session.commit()
            
            # Invalidate cache
            self._libros_cache = None
            
            return libro.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def actualizar_guia_fuente(self, libro_id: int, guia_texto: str) -> bool:
        """Guardar o actualizar la Guía de Fuente permanente de un libro"""
        session = self.get_session()
        try:
            libro = session.query(Libro).get(libro_id)
            if libro:
                libro.guia_fuente = guia_texto
                session.commit()
                self._libros_cache = None # Invalida cache
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error actualizando guía de fuente: {e}")
            return False
        finally:
            session.close()

    def actualizar_guion_podcast(self, libro_id: int, guion_texto: str) -> bool:
        """Guardar o actualizar el guion de podcast permanente de un libro"""
        session = self.get_session()
        try:
            libro = session.query(Libro).get(libro_id)
            if libro:
                libro.guion_podcast = guion_texto
                session.commit()
                self._libros_cache = None
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error actualizando guion: {e}")
            return False
        finally:
            session.close()

    def actualizar_ruta_audio_podcast(self, libro_id: int, ruta: str) -> bool:
        """Guardar o actualizar la ruta del audio de podcast de un libro"""
        session = self.get_session()
        try:
            libro = session.query(Libro).get(libro_id)
            if libro:
                libro.ruta_audio_podcast = ruta
                session.commit()
                self._libros_cache = None
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error actualizando ruta de podcast: {e}")
            return False
        finally:
            session.close()
    
    def agregar_fragmentos(self, libro_id: int, fragmentos: List[Dict]):
        """Agregar fragmentos de texto de un libro con embeddings"""
        session = self.get_session()
        try:
            for fragmento in fragmentos:
                # Serializar embedding a bytes si existe
                embedding_data = None
                if 'embedding' in fragmento and fragmento['embedding']:
                    if self.tipo_bd == "postgresql":
                        embedding_data = fragmento['embedding']  # PostgreSQL: array directo
                    else:
                        embedding_data = np.array(fragmento['embedding'], dtype=np.float32).tobytes()
                
                frag = Fragmento(
                    libro_id=libro_id,
                    contenido=fragmento['contenido'],
                    numero_pagina=fragmento.get('pagina'),
                    embedding=embedding_data,
                    token_count=fragmento.get('token_count', 0)
                )
                session.add(frag)
            
            # Actualizar contador de fragmentos del libro
            libro = session.query(Libro).get(libro_id)
            if libro:
                libro.total_fragmentos = len(fragmentos)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def guardar_consulta(self, pregunta: str, respuesta: str, 
                        libros_referenciados: List[int] = None, 
                        fragmentos_utilizados: List[int] = None,
                        modelo: str = None, tokens_utilizados: int = 0):
        """Guardar una consulta y su respuesta"""
        session = self.get_session()
        try:
            consulta = Consulta(
                pregunta=pregunta,
                respuesta=respuesta,
                libros_referenciados=libros_referenciados or [],
                fragmentos_utilizados=fragmentos_utilizados or [],
                modelo_utilizado=modelo,
                tokens_utilizados=tokens_utilizados
            )
            session.add(consulta)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def obtener_libros(self, force_refresh: bool = False) -> List[Dict]:
        """Obtener todos los libros (con cache simple)"""
        if not force_refresh and self._libros_cache is not None:
            # Verificar si el cache es reciente (opcional, aquí lo usamos siempre hasta que se invalide)
            return self._libros_cache

        session = self.get_session()
        try:
            libros = session.query(Libro).order_by(Libro.fecha_procesado.desc()).all()
            self._libros_cache = [
                {
                    'id': libro.id,
                    'titulo': libro.titulo,
                    'autor': libro.autor,
                    'isbn': libro.isbn,
                    'genero': libro.genero,
                    'total_paginas': libro.total_paginas,
                    'total_fragmentos': libro.total_fragmentos,
                    'fecha_procesado': libro.fecha_procesado,
                    'estado': libro.estado,
                    'metadata': libro.metadatos or {},
                    'guia_fuente': libro.guia_fuente,
                    'guion_podcast': libro.guion_podcast,
                    'mapa_mental': libro.mapa_mental,
                    'informe_estudio': libro.informe_estudio,
                    'cuestionario': libro.cuestionario,
                    'ruta_audio_podcast': libro.ruta_audio_podcast
                }
                for libro in libros
            ]
            self._last_cache_update = datetime.utcnow()
            return self._libros_cache
        except Exception as e:
            print(f"❌ Error obteniendo libros: {e}")
            return []
        finally:
            session.close()
    
    def obtener_fragmentos_libro(self, libro_id: int) -> List[Dict]:
        """Obtener fragmentos de un libro específico con embeddings"""
        session = self.get_session()
        try:
            fragmentos = session.query(Fragmento).filter(Fragmento.libro_id == libro_id).all()
            resultado = []
            
            for frag in fragmentos:
                fragmento_dict = {
                    'id': frag.id,
                    'libro_id': frag.libro_id,
                    'contenido': frag.contenido,
                    'pagina': frag.numero_pagina,
                    'token_count': frag.token_count
                }
                
                # Convertir embedding de bytes a lista si existe
                if frag.embedding:
                    try:
                        fragmento_dict['embedding'] = np.frombuffer(frag.embedding, dtype=np.float32).tolist()
                    except Exception as e:
                        print(f"⚠️ Error convirtiendo embedding: {e}")
                        fragmento_dict['embedding'] = None
                
                resultado.append(fragmento_dict)
            
            return resultado
        except Exception as e:
            print(f"❌ Error obteniendo fragmentos: {e}")
            return []
        finally:
            session.close()
    
    def obtener_todos_fragmentos(self) -> List[Dict]:
        """Obtener todos los fragmentos de todos los libros (para búsqueda)"""
        session = self.get_session()
        try:
            fragmentos = session.query(Fragmento, Libro).join(Libro).all()
            resultado = []
            
            for frag, libro in fragmentos:
                fragmento_dict = {
                    'id': frag.id,
                    'libro_id': frag.libro_id,
                    'contenido': frag.contenido,
                    'pagina': frag.numero_pagina,
                    'token_count': frag.token_count,
                    'libro_titulo': libro.titulo,
                    'libro_autor': libro.autor
                }
                
                if frag.embedding:
                    try:
                        fragmento_dict['embedding'] = np.frombuffer(frag.embedding, dtype=np.float32).tolist()
                    except Exception as e:
                        print(f"⚠️ Error convirtiendo embedding: {e}")
                        fragmento_dict['embedding'] = None
                
                resultado.append(fragmento_dict)
            
            return resultado
        except Exception as e:
            print(f"❌ Error obteniendo todos los fragmentos: {e}")
            return []
        finally:
            session.close()
    
    def obtener_fragmentos_por_libros(self, libros_ids: List[int]) -> List[Dict]:
        """Obtener fragmentos solo de los libros especificados"""
        session = self.get_session()
        try:
            if not libros_ids:
                return self.obtener_todos_fragmentos()
                
            # Usar SQLAlchemy ORM que es más seguro y limpio
            fragmentos = session.query(Fragmento, Libro)\
                .join(Libro)\
                .filter(Fragmento.libro_id.in_(libros_ids))\
                .order_by(Fragmento.libro_id, Fragmento.numero_pagina)\
                .all()
            
            resultado = []
            for frag, libro in fragmentos:
                fragmento_dict = {
                    'id': frag.id,
                    'libro_id': frag.libro_id,
                    'contenido': frag.contenido,
                    'numero_pagina': frag.numero_pagina,
                    'token_count': frag.token_count,
                    'libro_titulo': libro.titulo,
                    'libro_autor': libro.autor
                }
                
                if frag.embedding:
                    try:
                        fragmento_dict['embedding'] = np.frombuffer(frag.embedding, dtype=np.float32).tolist()
                    except Exception as e:
                        print(f"⚠️ Error convirtiendo embedding ID {frag.id}: {e}")
                        fragmento_dict['embedding'] = None
                else:
                    # DEBUG: Imprimir si falta embedding
                    # print(f"⚠️ Fragmento ID {frag.id} del libro {frag.libro_id} NO TIENE embedding en BD")
                    fragmento_dict['embedding'] = None
                
                resultado.append(fragmento_dict)
            
            # DEBUG INFO
            con_emb = len([f for f in resultado if f.get('embedding')])
            print(f"✅ DB: Obtenidos {len(resultado)} fragmentos para libros {libros_ids}. {con_emb} tienen embeddings.")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error obteniendo fragmentos por libros: {e}")
            return []
        finally:
            session.close()

    def _configurar_postgres_avanzado(self):
        """Configuraciones avanzadas para PostgreSQL - pgvector"""
        try:
            with self.engine.connect() as conn:
                # Intentar crear extensión pgvector para búsquedas vectoriales rápidas
                try:
                    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    print("✅ Extensión pgvector habilitada - Búsquedas vectoriales optimizadas")
                    
                    # Opcional: Crear índice para búsquedas por similitud vectorial
                    # Esto acelera las búsquedas cuando tengas muchos vectores
                    try:
                        conn.execute(sa.text("""
                            CREATE INDEX IF NOT EXISTS idx_fragmentos_embedding 
                            ON fragmentos USING ivfflat (embedding vector_cosine_ops)
                            WITH (lists = 100);
                        """))
                        print("✅ Índice vectorial creado para búsquedas rápidas")
                    except Exception as e:
                        print(f"ℹ️  No se pudo crear índice vectorial: {e}")
                        
                except Exception as e:
                    print(f"ℹ️  pgvector no disponible: {e}. Usando arrays nativos de PostgreSQL")
                    
        except Exception as e:
            print(f"⚠️ Error en configuración PostgreSQL avanzada: {e}")

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        session = self.get_session()
        try:
            # Verificar si las tablas existen
            inspector = sa.inspect(self.engine)
            tablas_existentes = inspector.get_table_names()
            
            if 'libros' not in tablas_existentes:
                return self._estadisticas_por_defecto()
            
            # Total libros
            total_libros = session.query(Libro).count()
            
            # Total fragmentos
            total_fragmentos = session.query(Fragmento).count()
            
            # Total consultas
            total_consultas = session.query(Consulta).count()
            
            # Última actividad
            ultimo_libro = session.query(Libro).order_by(Libro.fecha_procesado.desc()).first()
            ultima_consulta = session.query(Consulta).order_by(Consulta.fecha_consulta.desc()).first()
            
            ultima_actividad = None
            if ultimo_libro and ultima_consulta:
                ultima_actividad = max(ultimo_libro.fecha_procesado, ultima_consulta.fecha_consulta)
            elif ultimo_libro:
                ultima_actividad = ultimo_libro.fecha_procesado
            elif ultima_consulta:
                ultima_actividad = ultima_consulta.fecha_consulta
            
            return {
                'total_libros': total_libros,
                'total_fragmentos': total_fragmentos,
                'total_consultas': total_consultas,
                'ultima_actividad': ultima_actividad,
                'tipo_bd': self.tipo_bd
            }
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return self._estadisticas_por_defecto()
        finally:
            session.close()
    
    def _estadisticas_por_defecto(self) -> Dict[str, Any]:
        """Estadísticas por defecto cuando no hay base de datos"""
        return {
            'total_libros': 0,
            'total_fragmentos': 0,
            'total_consultas': 0,
            'ultima_actividad': None,
            'tipo_bd': self.tipo_bd
        }
    
    def obtener_estadisticas_avanzadas(self) -> Dict[str, Any]:
        """Estadísticas detalladas del sistema"""
        session = self.get_session()
        try:
            stats_basicas = self.obtener_estadisticas()
            
            # Estadísticas por género
            generos = session.query(Libro.genero).filter(Libro.genero.isnot(None)).all()
            conteo_generos = {}
            for genero in generos:
                if genero[0]:
                    conteo_generos[genero[0]] = conteo_generos.get(genero[0], 0) + 1
            
            # Total de tokens en el sistema
            total_tokens = session.query(sa.func.sum(Fragmento.token_count)).scalar() or 0
            
            # Libro más grande (más fragmentos)
            libro_mas_grande = session.query(Libro).order_by(Libro.total_fragmentos.desc()).first()
            
            return {
                **stats_basicas,
                'total_tokens': total_tokens,
                'conteo_generos': conteo_generos,
                'libro_mas_grande': {
                    'id': libro_mas_grande.id if libro_mas_grande else None,
                    'titulo': libro_mas_grande.titulo if libro_mas_grande else None,
                    'fragmentos': libro_mas_grande.total_fragmentos if libro_mas_grande else 0
                } if libro_mas_grande else None,
                'espacio_estimado_mb': self._calcular_espacio_estimado()
            }
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas avanzadas: {e}")
            return self._estadisticas_por_defecto()
        finally:
            session.close()

    def _calcular_espacio_estimado(self) -> float:
        """Calcular espacio aproximado usado en MB"""
        try:
            if self.tipo_bd == "sqlite":
                db_path = config_manager.get_sqlite_config()['ruta_db']
                if os.path.exists(db_path):
                    return round(os.path.getsize(db_path) / (1024 * 1024), 2)
            return 0.0
        except:
            return 0.0
        
    def buscar_libros_por_metadata(self, criterios: Dict) -> List[Dict]:
        """Buscar libros por criterios en metadatos"""
        session = self.get_session()
        try:
            query = session.query(Libro)
            
            # Buscar en campos normales
            if 'titulo' in criterios:
                query = query.filter(Libro.titulo.ilike(f"%{criterios['titulo']}%"))
            if 'autor' in criterios:
                query = query.filter(Libro.autor.ilike(f"%{criterios['autor']}%"))
            
            # Buscar en metadatos JSON (depende del motor)
            if 'tamano_min' in criterios and self.tipo_bd == "postgresql":
                query = query.filter(Libro.metadatos['tamano_archivo_mb'].astext.cast(Float) > criterios['tamano_min'])
            
            libros = query.order_by(Libro.fecha_procesado.desc()).all()
            return [
                {
                    'id': libro.id,
                    'titulo': libro.titulo,
                    'autor': libro.autor,
                    'total_paginas': libro.total_paginas,
                    'total_fragmentos': libro.total_fragmentos,
                    'fecha_procesado': libro.fecha_procesado,
                    'metadata': libro.metadatos or {},
                    'guia_fuente': libro.guia_fuente,
                    'guion_podcast': libro.guion_podcast,
                    'mapa_mental': libro.mapa_mental,
                    'informe_estudio': libro.informe_estudio,
                    'cuestionario': libro.cuestionario,
                    'ruta_audio_podcast': libro.ruta_audio_podcast
                }
                for libro in libros
            ]
        except Exception as e:
            print(f"❌ Error buscando libros: {e}")
            return []
        finally:
            session.close()


    def update_consultas_chart(self):
        """Actualizar gráfico de consultas usando métodos existentes"""
        self.clear_layout(self.bars_container_consultas)
        
        try:
            # Obtener consultas usando el método existente
            session = self.get_session()
            total_consultas = session.query(Consulta).count()
            consultas_ultima_semana = session.query(Consulta)\
                .filter(Consulta.fecha_consulta >= datetime.utcnow() - sa.text("INTERVAL '7 days'"))\
                .count()
            consultas_ultimo_mes = session.query(Consulta)\
                .filter(Consulta.fecha_consulta >= datetime.utcnow() - sa.text("INTERVAL '30 days'"))\
                .count()
            session.close()
            
            # Crear barras
            self.add_bar_to_chart(self.bars_container_consultas, "Última Semana", consultas_ultima_semana, total_consultas)
            self.add_bar_to_chart(self.bars_container_consultas, "Último Mes", consultas_ultimo_mes, total_consultas)
            self.add_bar_to_chart(self.bars_container_consultas, "Total Consultas", total_consultas, total_consultas)
                
        except Exception as e:
            print(f"❌ Error actualizando gráfico de consultas: {e}")


    def update_libros_chart(self):
        """Actualizar gráfico de libros usando métodos existentes"""
        self.clear_layout(self.bars_container_libros)
        
        try:
            # Obtener libros usando el método existente
            session = self.get_session()
            total_libros = session.query(Libro).count()
            libros_ultima_semana = session.query(Libro)\
                .filter(Libro.fecha_procesado >= datetime.utcnow() - sa.text("INTERVAL '7 days'"))\
                .count()
            libros_ultimo_mes = session.query(Libro)\
                .filter(Libro.fecha_procesado >= datetime.utcnow() - sa.text("INTERVAL '30 days'"))\
                .count()
            session.close()
            
            # Crear barras
            self.add_bar_to_chart(self.bars_container_libros, "Última Semana", libros_ultima_semana, total_libros)
            self.add_bar_to_chart(self.bars_container_libros, "Último Mes", libros_ultimo_mes, total_libros)
            self.add_bar_to_chart(self.bars_container_libros, "Total Libros", total_libros, total_libros)
                
        except Exception as e:
            print(f"❌ Error actualizando gráfico de libros: {e}")

    def update_recent_activity(self):
        """Actualizar actividad reciente usando métodos existentes"""
        self.list_recent_activity.clear()
        
        try:
            session = self.get_session()
            # Obtener últimas 10 actividades (libros procesados y consultas)
            ultimos_libros = session.query(Libro).order_by(Libro.fecha_procesado.desc()).limit(5).all()
            ultimas_consultas = session.query(Consulta).order_by(Consulta.fecha_consulta.desc()).limit(5).all()
            session.close()
            
            actividades = []
            for libro in ultimos_libros:
                actividades.append((libro.fecha_procesado, f"📚 Libro procesado: {libro.titulo}"))
            for consulta in ultimas_consultas:
                actividades.append((consulta.fecha_consulta, f"❓ Consulta realizada: {consulta.pregunta[:30]}..."))
            
            # Ordenar por fecha y tomar las 10 más recientes
            actividades.sort(key=lambda x: x[0], reverse=True)
            actividades = actividades[:10]
            
            for fecha, descripcion in actividades:
                item_text = f"{fecha.strftime('%Y-%m-%d %H:%M:%S')} - {descripcion}"
                self.list_recent_activity.addItem(item_text)
                
        except Exception as e:
            print(f"❌ Error actualizando actividad reciente: {e}")
    def actualizar_studio_libro(self, libro_id: int, tipo: str, contenido: str) -> bool:
        """Actualizar el contenido de Notebook Studio para un libro"""
        session = self.get_session()
        try:
            libro = session.query(Libro).filter(Libro.id == libro_id).first()
            if not libro:
                return False
                
            if tipo == "mapa":
                libro.mapa_mental = contenido
            elif tipo == "informe":
                libro.informe_estudio = contenido
            elif tipo == "cuestionario":
                libro.cuestionario = contenido
            else:
                return False
                
            session.commit()
            self._libros_cache = None # Invalida cache
            print(f"✅ Notebook Studio: {tipo} actualizado para libro {libro_id}")
            return True
        except Exception as e:
            session.rollback()
            print(f"❌ Error actualizando studio de libro: {e}")
            return False
        finally:
            session.close()

    def eliminar_libro(self, libro_id: int) -> bool:
        """Eliminar un libro y todos sus fragmentos"""
        session = self.get_session()
        try:
            # Eliminar fragmentos primero (por la foreign key)
            session.query(Fragmento).filter(Fragmento.libro_id == libro_id).delete()
            
            # Eliminar el libro
            libro = session.query(Libro).get(libro_id)
            if libro:
                session.delete(libro)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"❌ Error eliminando libro: {e}")
            return False
        finally:
            self._libros_cache = None  # Invalida cache
            session.close()
    
    def obtener_historial_consultas(self, limite: int = 50, busqueda: str = None) -> List[Dict]:
        """Obtener historial con soporte para búsqueda por texto y títulos de libros"""
        session = self.get_session()
        try:
            query = session.query(Consulta)
            
            # Si hay búsqueda, filtrar por pregunta, respuesta o intentar buscar por libro
            if busqueda:
                # Buscar IDs de libros que coincidan con el título
                libros_match = session.query(Libro.id).filter(Libro.titulo.ilike(f"%{busqueda}%")).all()
                libros_ids = [l[0] for l in libros_match]
                
                filters = [
                    Consulta.pregunta.ilike(f"%{busqueda}%"),
                    Consulta.respuesta.ilike(f"%{busqueda}%")
                ]
                
                # Para SQLite/JSON, la búsqueda en libros_referenciados es más compleja, 
                # así que complementamos con una búsqueda de IDs si encontramos libros que coincidan
                for lid in libros_ids:
                    filters.append(sa.text(f"libros_referenciados LIKE '%{lid}%'"))
                
                query = query.filter(sa.or_(*filters))
            
            consultas = query.order_by(Consulta.fecha_consulta.desc()).limit(limite).all()
            
            # Obtener nombres de libros para todas las consultas (optimizado)
            todos_libros_ids = set()
            for c in consultas:
                if c.libros_referenciados:
                    todos_libros_ids.update(c.libros_referenciados)
            
            nombres_libros = {}
            if todos_libros_ids:
                libros_info = session.query(Libro.id, Libro.titulo).filter(Libro.id.in_(list(todos_libros_ids))).all()
                nombres_libros = {l.id: l.titulo for l in libros_info}
            
            return [
                {
                    'id': c.id,
                    'titulo': c.titulo, # Nuevo campo
                    'pregunta': c.pregunta,
                    'respuesta': c.respuesta,
                    'fecha': c.fecha_consulta,
                    'libros_referenciados': c.libros_referenciados,
                    'libros_titulos': [nombres_libros.get(lid, f"Libro {lid}") for lid in (c.libros_referenciados or [])],
                    'modelo': c.modelo_utilizado
                }
                for c in consultas
            ]
        except Exception as e:
            print(f"❌ Error obteniendo historial: {e}")
            return []
        finally:
            session.close()

    def eliminar_consulta(self, consulta_id: int) -> bool:
        """Eliminar una consulta específica del historial"""
        session = self.get_session()
        try:
            consulta = session.query(Consulta).filter(Consulta.id == consulta_id).first()
            if consulta:
                session.delete(consulta)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error eliminando consulta: {e}")
            return False
    def actualizar_titulo_consulta(self, consulta_id: int, nuevo_titulo: str) -> bool:
        """Actualizar el título personalizado de una consulta del historial"""
        session = self.get_session()
        try:
            consulta = session.query(Consulta).filter(Consulta.id == consulta_id).first()
            if consulta:
                consulta.titulo = nuevo_titulo
                session.commit()
                print(f"✅ Historial {consulta_id} renombrado a: {nuevo_titulo}")
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error al renombrar historial: {e}")
            return False
        finally:
            session.close()

    def probar_conexion(self) -> bool:
        """Probar la conexión a la base de datos"""
        try:
            session = self.get_session()
            # Para SQLite, usar una consulta simple
            if self.tipo_bd == "sqlite":
                session.execute("SELECT 1")
            else:
                session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            print(f"❌ Error probando conexión a BD: {e}")
            return False