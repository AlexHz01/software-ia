"""
Estilos y temas para la aplicación con soporte para escalado dinámico
"""

def get_scale_factor(widget):
    """Calcular factor de escala basado en el DPI de la pantalla"""
    try:
        screen = widget.screen()
        if screen:
            # 96 es el DPI estándar
            return screen.logicalDotsPerInch() / 96.0
    except:
        pass
    return 1.0

def apply_light_theme(widget):
    """Aplicar tema claro a un widget"""
    f = get_scale_factor(widget)
    widget.setStyleSheet(f"""
        QMainWindow {{
            background-color: #f8f9fa;
        }}
        QWidget {{
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: {int(11 * f)}px;
        }}
    """)

def apply_dark_theme(widget):
    """Aplicar tema oscuro a un widget"""
    f = get_scale_factor(widget)
    widget.setStyleSheet(f"""
        QMainWindow {{
            background-color: #2c3e50;
            color: #ecf0f1;
        }}
        QWidget {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #2c3e50;
            color: #ecf0f1;
            font-size: {int(11 * f)}px;
        }}
    """)

def get_sidebar_style():
    """Estilo para la barra lateral"""
    return """
        QWidget {
            background-color: #34495e;
            color: white;
        }
    """

def get_button_style(scale_factor=1.0):
    """Estilo para botones con escalado opcional"""
    f = scale_factor
    return f"""
        QPushButton {{
            background-color: #3498db;
            color: white;
            border: none;
            padding: {int(8 * f)}px {int(16 * f)}px;
            border-radius: {int(4 * f)}px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #2980b9;
        }}
        QPushButton:pressed {{
            background-color: #21618c;
        }}
        QPushButton:disabled {{
            background-color: #bdc3c7;
            color: #7f8c8d;
        }}
    """