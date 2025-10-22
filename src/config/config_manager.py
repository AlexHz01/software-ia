import json
import os
from typing import Dict, Any

class ConfigManager:
    """Gestor de configuración persistente para la aplicación"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config_file = "config/sistema_config.json"
        self.default_config = {
            "general": {
                "tema": "claro",
                "idioma": "es",
                "auto_inicio": False,
                "notificaciones": True
            },
            "ia": {
                "api_key": "",
                "modelo": "gpt-3.5-turbo",
                "temperatura": 0.7,
                "modelo_whisper": "whisper-1"
            },
            "almacenamiento": {
                "ruta_datos": "./data",
                "limite_almacenamiento_mb": 1000,
                "auto_limpieza": True,
                "conservar_pdfs": False
            },
            "transcripcion": {
                "segment_length_min": 10,
                "formatear_automaticamente": True
            },
            "database": {  # NUEVA SECCIÓN PARA CONFIGURACIÓN DE BD
                "tipo": "postgresql",  # postgresql o sqlite
                "postgresql": {
                    "host": "localhost",
                    "puerto": 5432,
                    "usuario": "postgres",
                    "password": "",
                    "nombre_bd": "biblioteca_ia",
                    "schema": "public",
                    "ssl_mode": "prefer",
                    "pool_min": 1,
                    "pool_max": 10,
                    "timeout": 30
                },
                "sqlite": {
                    "ruta_db": "./data/biblioteca.db",
                    "auto_backup": True,
                    "backup_interval_days": 7
                }
            },
            "biblioteca_ia": {
                "procesamiento": {
                    "tamano_fragmento": 1000,
                    "solapamiento_fragmento": 200,
                    "max_fragmentos_por_pagina": 10,
                    "min_longitud_fragmento": 50,
                    "max_tokens_por_fragmento": 500
                },
                "embeddings": {
                    "modelo": "text-embedding-ada-002",
                    "dimensiones": 1536,
                    "batch_size": 10,
                    "timeout": 30
                },
                "consulta": {
                    "top_k_fragmentos": 5,
                    "umbral_similitud": 0.7,
                    "max_tokens_respuesta": 1500,
                    "incluir_referencias": True,
                    "temperatura_consulta": 0.3
                },
                "ui": {
                    "mostrar_progreso_detallado": True,
                    "auto_actualizar_estadisticas": True,
                    "mostrar_fragmentos_relevantes": False
                }
            }
        }
        self.config = self.default_config.copy()
        self.load_config()
        self._initialized = True
    
    def load_config(self):
        """Cargar configuración desde archivo"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._deep_merge(self.config, loaded_config)
                print("✅ Configuración cargada desde archivo")
            else:
                self.save_config()
        except Exception as e:
            print(f"❌ Error cargando configuración: {e}")
    
    def save_config(self):
        """Guardar configuración en archivo"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print("✅ Configuración guardada en archivo")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def _deep_merge(self, target: Dict, source: Dict):
        """Fusión profunda de diccionarios"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get(self, section: str, key: str = None, default=None):
        """Obtener valor de configuración"""
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """Establecer valor de configuración"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()
    
    # MÉTODOS PARA IA
    def get_api_key(self) -> str:
        return self.get("ia", "api_key", "")
    
    def get_modelo(self) -> str:
        return self.get("ia", "modelo", "gpt-3.5-turbo")
    
    def get_temperatura(self) -> float:
        return self.get("ia", "temperatura", 0.7)
    
    # MÉTODOS PARA BASE DE DATOS
    def get_tipo_bd(self) -> str:
        return self.get("database", "tipo", "sqlite")
    
    def get_postgres_config(self) -> Dict[str, Any]:
        return self.get("database", "postgresql")
    
    def get_sqlite_config(self) -> Dict[str, Any]:
        return self.get("database", "sqlite")
    
    def get_connection_string(self) -> str:
        """Obtener string de conexión según el tipo de BD"""
        tipo_bd = self.get_tipo_bd()
        
        if tipo_bd == "postgresql":
            pg_config = self.get_postgres_config()
            return (
                f"postgresql://{pg_config['usuario']}:{pg_config['password']}"
                f"@{pg_config['host']}:{pg_config['puerto']}/{pg_config['nombre_bd']}"
            )
        else:
            sqlite_config = self.get_sqlite_config()
            return f"sqlite:///{sqlite_config['ruta_db']}"
    
    # MÉTODOS ESPECÍFICOS PARA BIBLIOTECA IA
    def get_tamano_fragmento(self) -> int:
        return self.get("biblioteca_ia", "procesamiento.tamano_fragmento", 1000)
    
    def get_solapamiento_fragmento(self) -> int:
        return self.get("biblioteca_ia", "procesamiento.solapamiento_fragmento", 200)
    
    def get_modelo_embeddings(self) -> str:
        return self.get("biblioteca_ia", "embeddings.modelo", "text-embedding-ada-002")
    
    def get_top_k_fragmentos(self) -> int:
        return self.get("biblioteca_ia", "consulta.top_k_fragmentos", 5)
    
    def get_umbral_similitud(self) -> float:
        return self.get("biblioteca_ia", "consulta.umbral_similitud", 0.7)
    
    def get_batch_size_embeddings(self) -> int:
        return self.get("biblioteca_ia", "embeddings.batch_size", 10)
    
    def get_max_tokens_respuesta(self) -> int:
        return self.get("biblioteca_ia", "consulta.max_tokens_respuesta", 1500)

# Instancia global
config_manager = ConfigManager()