from PyQt5.QtWidgets import QWidget
from abc import ABC, abstractmethod

class BaseApp(QWidget):
    """Clase base para todas las aplicaciones del sistema"""
    
    def __init__(self):
        super().__init__()
        
    @abstractmethod
    def get_title(self) -> str:
        """Obtener título de la aplicación"""
        pass
        
    @abstractmethod
    def get_icon(self) -> str:
        """Obtener icono de la aplicación"""
        pass
        
    def get_name(self) -> str:
        """Obtener nombre interno de la aplicación"""
        return self.__class__.__name__.lower().replace('app', '')
        
    def setup_ui(self):
        """Configurar la interfaz de la aplicación (puede ser sobreescrito)"""
        pass