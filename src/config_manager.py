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
                "auto_limpieza": True
            },
            "transcripcion": {
                "segment_length_min": 10,
                "formatear_automaticamente": True
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
                    # Merge con configuración por defecto
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
    
    def get_api_key(self) -> str:
        """Obtener API key de forma segura"""
        return self.get("ia", "api_key", "")
    
    def get_modelo(self) -> str:
        """Obtener modelo seleccionado"""
        return self.get("ia", "modelo", "gpt-3.5-turbo")
    
    def get_temperatura(self) -> float:
        """Obtener temperatura"""
        return self.get("ia", "temperatura", 0.7)

# Instancia global
config_manager = ConfigManager()