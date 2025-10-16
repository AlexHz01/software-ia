"""
Estilos y temas para la aplicación
"""

def apply_light_theme(widget):
    """Aplicar tema claro a un widget"""
    widget.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)

def apply_dark_theme(widget):
    """Aplicar tema oscuro a un widget"""
    widget.setStyleSheet("""
        QMainWindow {
            background-color: #2c3e50;
            color: #ecf0f1;
        }
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #2c3e50;
            color: #ecf0f1;
        }
    """)

def get_sidebar_style():
    """Estilo para la barra lateral"""
    return """
        QWidget {
            background-color: #34495e;
            color: white;
        }
    """

def get_button_style():
    """Estilo para botones"""
    return """
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #21618c;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
    """