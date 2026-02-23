import logging
from PyQt5.QtCore import QObject, QTimer

from views.main_window import MainWindow
from controllers.navigation_controller import NavigationController

class BibliotecaAppManager(QObject):
    """Gestor principal de la aplicación Biblioteca IA"""
    
    def __init__(self):
        super().__init__()
        self.logger = self.setup_logging()
        self.main_window = None
        self.nav_controller = None
        self.setup_app()
        
    def setup_logging(self):
        """Configurar sistema de logging"""
        logger = logging.getLogger('BibliotecaIA')
        logger.setLevel(logging.DEBUG)  # Cambiado a DEBUG para más información
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        return logger
        
    def setup_app(self):
        """Configurar todos los componentes de la aplicación"""
        try:
            self.logger.info("🚀 Iniciando Sistema Biblioteca IA...")
            
            # 1. PRIMERO crear el controlador de navegación
            self.nav_controller = NavigationController()
            self.logger.info("✅ Controlador de navegación creado")
            
            # 2. LUEGO crear la ventana principal
            self.main_window = MainWindow(self.nav_controller)
            self.logger.info("✅ Ventana principal creada")
            
            # 3. CONECTAR señales CRÍTICAS antes de registrar apps
            self.setup_connections()
            
            # 4. FINALMENTE registrar aplicaciones
            self.register_apps()
            
            # 5. Configurar aplicación inicial con un pequeño delay
            QTimer.singleShot(100, self.setup_initial_app)
            
            self.logger.info("✅ Aplicación iniciada correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando aplicación: {e}")
            import traceback
            traceback.print_exc()
            raise
            
    def register_apps(self):
        """Registrar todas las aplicaciones disponibles"""
        self.logger.info("📝 Registrando aplicaciones...")
        
        try:
            # Importar las aplicaciones
            from views.apps.biblioteca_app import BibliotecaApp
            from views.apps.config_app import ConfigApp
            from views.apps.transcripcion_app import TranscripcionApp
            
            # Aplicación de Biblioteca
            biblioteca_app = BibliotecaApp()
            self.nav_controller.register_app("biblioteca", biblioteca_app)
            self.logger.info("✅ Biblioteca registrada")

            # NUEVA: Aplicación de Transcripción
            transcripcion_app = TranscripcionApp()
            self.nav_controller.register_app("transcripcion", transcripcion_app)
            self.logger.info("✅ Transcripción registrada")
            
            # Aplicación de Configuración
            config_app = ConfigApp()
            self.nav_controller.register_app("config", config_app)
            self.logger.info("✅ Configuración registrada")
            
            # VERIFICACIÓN CRÍTICA
            apps = self.nav_controller.get_available_apps()
            self.logger.info(f"📋 Aplicaciones registradas: {len(apps)}")
            
            for app_name, app in apps.items():
                self.logger.info(f"   ├─ {app_name}: {app.get_title()}")
                
            if not apps:
                self.logger.error("❌ NO se registró ninguna aplicación!")
                
        except Exception as e:
            self.logger.error(f"❌ Error registrando aplicaciones: {e}")
            import traceback
            traceback.print_exc()
        
    def setup_connections(self):
        """Conectar señales entre componentes - MÉTODO CRÍTICO"""
        try:
            # ESTA ES LA CONEXIÓN MÁS IMPORTANTE
            self.nav_controller.app_changed.connect(self.main_window.on_app_changed)
            self.logger.info("🔗 Señal app_changed conectada correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando señales: {e}")
            raise
        
    def setup_initial_app(self):
        """Configurar la aplicación inicial"""
        try:
            apps = self.nav_controller.get_available_apps()
            if not apps:
                self.logger.error("❌ No hay aplicaciones disponibles")
                return
                
            # Cargar la biblioteca por defecto
            initial_app_name = "biblioteca"
            initial_app = self.nav_controller.get_app(initial_app_name)
            
            if initial_app:
                self.main_window.show_app(initial_app)
                self.nav_controller.set_current_app(initial_app_name)
                self.logger.info("🏠 Aplicación inicial configurada: Biblioteca IA")
            else:
                # Fallback: cargar la primera aplicación disponible
                first_app_name = list(apps.keys())[0]
                first_app = apps[first_app_name]
                self.main_window.show_app(first_app)
                self.nav_controller.set_current_app(first_app_name)
                self.logger.info(f"🔄 Aplicación inicial fallback: {first_app_name}")
                
        except Exception as e:
            self.logger.error(f"❌ Error configurando app inicial: {e}")

            
        
    def show(self):
        """Mostrar la ventana principal"""
        if self.main_window:
            self.main_window.show()
        else:
            self.logger.error("❌ No hay ventana principal para mostrar")
            
    def get_main_window(self):
        """Obtener la ventana principal"""
        return self.main_window