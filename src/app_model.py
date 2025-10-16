"""
Modelos de datos para la aplicación
"""

class AppInfo:
    """Información de una aplicación del sistema"""
    
    def __init__(self, name: str, title: str, icon: str, description: str = ""):
        self.name = name
        self.title = title
        self.icon = icon
        self.description = description
        self.enabled = True

class Book:
    """Modelo de libro"""
    
    def __init__(self):
        self.id = None
        self.title = ""
        self.file_path = ""
        self.content = ""
        self.vectors_path = ""
        self.processed_at = ""
        self.created_at = ""