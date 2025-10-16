from PyQt5.QtCore import QObject, pyqtSignal

class NavigationController(QObject):
    """Controlador de navegación entre aplicaciones"""
    
    app_changed = pyqtSignal(str)
    apps_updated = pyqtSignal()  # NUEVA SEÑAL
    
    def __init__(self):
        super().__init__()
        self.apps = {}
        self.current_app = None
        
    def register_app(self, app_name: str, app):
        """Registrar una aplicación"""
        self.apps[app_name] = app
        # EMITIR señal cuando se registre una app
        self.apps_updated.emit()
        
    def get_app(self, app_name: str):
        """Obtener una aplicación por nombre"""
        return self.apps.get(app_name)
        
    def get_available_apps(self):
        """Obtener todas las aplicaciones disponibles"""
        return self.apps.copy()
        
    def set_current_app(self, app_name: str):
        """Establecer la aplicación actual"""
        if app_name in self.apps:
            self.current_app = app_name
            self.app_changed.emit(app_name)