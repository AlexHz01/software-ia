import PyPDF2
import os
import tiktoken
from typing import List, Dict, Tuple
import numpy as np
from config.config_manager import config_manager
from datetime import datetime
import hashlib

# Importar OpenAI de forma compatible
try:
    import openai
    # Verificar si es la nueva versión (1.0.0+)
    if hasattr(openai, 'OpenAI'):
        OPENAI_NEW = True
    else:
        OPENAI_NEW = False
except ImportError:
    OPENAI_NEW = False

class PDFProcessor:
    def __init__(self):
        self.api_key = config_manager.get_api_key()
        
        # Inicializar cliente OpenAI de forma compatible
        if OPENAI_NEW and self.api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=self.api_key)
                self.openai_available = True
            except Exception as e:
                print(f"⚠️ Error inicializando cliente OpenAI: {e}")
                self.openai_available = False
        else:
            self.openai_available = False
            
        # MANEJO SEGURO DE TIKTOKEN
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            print("✅ Tiktoken cargado correctamente")
        except ValueError as e:
            if "Unknown encoding" in str(e):
                print("⚠️ Error: No se encontraron archivos de codificación tiktoken")
                print("🔧 Usando modo de compatibilidad sin tiktoken")
                self.encoding = None
            else:
                raise e
        except Exception as e:
            print(f"⚠️ Error inesperado con tiktoken: {e}")
            self.encoding = None
    
        # Configuraciones desde la sección específica
        self.tamano_fragmento = config_manager.get_tamano_fragmento()
        self.solapamiento_fragmento = config_manager.get_solapamiento_fragmento()
        self.modelo_embeddings = config_manager.get_modelo_embeddings()
        self.batch_size = config_manager.get_batch_size_embeddings()
        
    def contar_tokens(self, texto: str) -> int:
        """Contar tokens en un texto de forma segura"""
        if self.encoding and texto:
            try:
                return len(self.encoding.encode(texto))
            except Exception as e:
                print(f"⚠️ Error contando tokens, usando aproximación: {e}")
                # Fallback: aproximación por palabras (4 tokens ≈ 3 palabras)
                return len(texto.split()) * 4 // 3
        else:
            # Fallback cuando tiktoken no está disponible
            return len(texto.split()) * 4 // 3 if texto else 0
    
    def extraer_texto_pdf(self, pdf_path: str) -> Tuple[List[Dict], int, List[Dict]]:
        """Extraer texto de un PDF y dividirlo en fragmentos optimizados"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_paginas = len(pdf_reader.pages)
                fragmentos = []
                
                # Extraer índice primero
                indice = self.extraer_indice_ia(pdf_path)
                
                max_fragmentos_por_pagina = config_manager.get(
                    "biblioteca_ia", "procesamiento.max_fragmentos_por_pagina", 10
                )
                min_longitud = config_manager.get(
                    "biblioteca_ia", "procesamiento.min_longitud_fragmento", 50
                )
                
                print(f"📖 Procesando PDF: {os.path.basename(pdf_path)}")
                print(f"📄 Total de páginas: {total_paginas}")
                
                for page_num in range(total_paginas):
                    page = pdf_reader.pages[page_num]
                    texto = page.extract_text()
                    
                    if texto and texto.strip():
                        # Limpiar y normalizar texto
                        texto = self._limpiar_texto(texto)
                        
                        # Dividir en fragmentos inteligentes
                        fragmentos_pagina = self._dividir_texto_en_fragmentos(
                            texto, page_num + 1, min_longitud
                        )
                        
                        # Limitar fragmentos por página si es necesario
                        if len(fragmentos_pagina) > max_fragmentos_por_pagina:
                            fragmentos_pagina = fragmentos_pagina[:max_fragmentos_por_pagina]
                        
                        fragmentos.extend(fragmentos_pagina)
                
                print(f"✅ Extraídos {len(fragmentos)} fragmentos de {total_paginas} páginas")
                return fragmentos, total_paginas, indice
                
        except Exception as e:
            print(f"❌ Error procesando PDF {pdf_path}: {e}")
            return [], 0, []

    def extraer_indice_ia(self, pdf_path: str) -> List[Dict]:
        """Extraer el índice del libro usando IA analizando las primeras páginas"""
        try:
            if not self.openai_available:
                return []
                
            print(f"🔍 Intentando extraer índice de: {os.path.basename(pdf_path)}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Analizar las primeras 10 páginas para buscar el índice
                paginas_analizar = min(10, len(pdf_reader.pages))
                texto_analisis = ""
                
                for i in range(paginas_analizar):
                    texto_analisis += f"--- PÁGINA {i+1} ---\n"
                    texto_analisis += pdf_reader.pages[i].extract_text() + "\n"
            
            prompt = f"""
            Analiza el siguiente texto extraído de las primeras páginas de un libro jurídico y extrae el ÍNDICE o TABLA DE CONTENIDO.
            Devuelve ÚNICAMENTE un objeto JSON con una lista de capítulos. Cada capítulo debe tener 'titulo' y 'pagina'.
            Si no encuentras un índice claro, devuelve una lista vacía [].
            
            Formato esperado:
            [
                {{"titulo": "Introducción", "pagina": 5}},
                {{"titulo": "Capítulo I: El Derecho Civil", "pagina": 15}}
            ]
            
            Texto a analizar:
            {texto_analisis[:8000]}
            """
            
            if OPENAI_NEW:
                response = self.openai_client.chat.completions.create(
                    model=config_manager.get_modelo(),
                    messages=[
                        {"role": "system", "content": "Eres un experto en análisis de documentos jurídicos. Tu tarea es extraer índices de libros de forma estructurada."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" } if "gpt-4" in config_manager.get_modelo() else None
                )
                contenido = response.choices[0].message.content
            else:
                import openai as openai_old
                openai_old.api_key = self.api_key
                response = openai_old.ChatCompletion.create(
                    model=config_manager.get_modelo(),
                    messages=[
                        {"role": "system", "content": "Eres un experto en análisis de documentos jurídicos."},
                        {"role": "user", "content": prompt}
                    ]
                )
                contenido = response['choices'][0]['message']['content']
            
            # Limpiar y parsear JSON
            import json
            # Si no es JSON nativo (gpt-3.5), intentar extraerlo
            if "```json" in contenido:
                contenido = contenido.split("```json")[1].split("```")[0]
            elif "```" in contenido:
                contenido = contenido.split("```")[1].split("```")[0]
            
            data = json.loads(contenido)
            indice = data.get('capitulos', data) if isinstance(data, dict) else data
            
            if isinstance(indice, list):
                print(f"✅ Índice extraído: {len(indice)} capítulos encontrados")
                return indice
            return []
            
        except Exception as e:
            print(f"⚠️ No se pudo extraer el índice: {e}")
            return []
    
    def _limpiar_texto(self, texto: str) -> str:
        """Limpiar y normalizar texto"""
        # Eliminar múltiples espacios y saltos de línea
        lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
        texto = ' '.join(lineas)
        
        # Limpiar caracteres extraños pero mantener puntuación
        texto = ' '.join(texto.split())  # Normalizar espacios
        return texto
    
    def _dividir_texto_en_fragmentos(self, texto: str, pagina: int, min_longitud: int) -> List[Dict]:
        """Dividir texto en fragmentos inteligentes"""
        fragmentos = []
        
        # Intentar dividir por párrafos naturales primero
        parrafos = [p.strip() for p in texto.split('\n\n') if p.strip() and len(p.strip()) >= min_longitud]
        
        for parrafo in parrafos:
            tokens = self.contar_tokens(parrafo)
            if tokens <= self.tamano_fragmento:
                fragmentos.append({
                    'contenido': parrafo,
                    'pagina': pagina,
                    'token_count': tokens
                })
            else:
                # Si el párrafo es muy largo, dividir por oraciones
                oraciones = [o.strip() + '.' for o in parrafo.split('.') if o.strip()]
                fragmento_actual = ""
                
                for oracion in oraciones:
                    tokens_oracion = self.contar_tokens(oracion)
                    tokens_actual = self.contar_tokens(fragmento_actual)
                    
                    if tokens_actual + tokens_oracion <= self.tamano_fragmento:
                        if fragmento_actual:
                            fragmento_actual += " " + oracion
                        else:
                            fragmento_actual = oracion
                    else:
                        if fragmento_actual and self.contar_tokens(fragmento_actual) >= min_longitud:
                            fragmentos.append({
                                'contenido': fragmento_actual.strip(),
                                'pagina': pagina,
                                'token_count': self.contar_tokens(fragmento_actual)
                            })
                        fragmento_actual = oracion
                
                # Agregar el último fragmento
                if fragmento_actual and self.contar_tokens(fragmento_actual) >= min_longitud:
                    fragmentos.append({
                        'contenido': fragmento_actual.strip(),
                        'pagina': pagina,
                        'token_count': self.contar_tokens(fragmento_actual)
                    })
        
        return fragmentos
    
    def generar_embeddings_lote(self, textos: List[str]) -> List[List[float]]:
        """Generar embeddings en lote para mejor performance"""
        try:
            if not textos or not self.openai_available:
                return []
                
            print(f"🧮 Generando embeddings para {len(textos)} textos...")
            
            if OPENAI_NEW:
                response = self.openai_client.embeddings.create(
                    model=self.modelo_embeddings,
                    input=textos
                )
                embeddings = [item.embedding for item in response.data]
            else:
                # Fallback para versiones antiguas (no recomendado)
                import openai as openai_old
                openai_old.api_key = self.api_key
                response = openai_old.Embedding.create(
                    model=self.modelo_embeddings,
                    input=textos
                )
                embeddings = [item['embedding'] for item in response['data']]
            
            print(f"✅ Embeddings generados exitosamente")
            return embeddings
            
        except Exception as e:
            print(f"❌ Error generando embeddings en lote: {e}")
            return []
    
    def generar_embedding(self, texto: str) -> List[float]:
        """Generar embedding vectorial para un texto individual"""
        try:
            if not self.openai_available:
                return []
                
            if OPENAI_NEW:
                response = self.openai_client.embeddings.create(
                    model=self.modelo_embeddings,
                    input=texto
                )
                return response.data[0].embedding
            else:
                # Fallback para versiones antiguas
                import openai as openai_old
                openai_old.api_key = self.api_key
                response = openai_old.Embedding.create(
                    model=self.modelo_embeddings,
                    input=texto
                )
                return response['data'][0]['embedding']
        except Exception as e:
            print(f"❌ Error generando embedding: {e}")
            return []
        
    def extraer_metadatos_pdf(self, pdf_path: str) -> Dict:
        """Extraer metadatos avanzados del PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Metadatos básicos del PDF
                info = pdf_reader.metadata
                
                # Calcular hash del archivo (para evitar duplicados)
                file_hash = self._calcular_hash_archivo(pdf_path)
                
                # Estadísticas del archivo
                file_stats = os.stat(pdf_path)
                
                metadatos = {
                    # Metadatos del archivo
                    'tamano_archivo_mb': round(file_stats.st_size / (1024 * 1024), 2),
                    'fecha_creacion_archivo': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    'fecha_modificacion_archivo': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    'hash_archivo': file_hash,
                    
                    # Metadatos del PDF (si están disponibles)
                    'titulo_pdf': info.get('/Title', ''),
                    'autor_pdf': info.get('/Author', ''),
                    'asunto_pdf': info.get('/Subject', ''),
                    'palabras_clave_pdf': info.get('/Keywords', ''),
                    'creador_pdf': info.get('/Creator', ''),
                    'productor_pdf': info.get('/Producer', ''),
                    'fecha_creacion_pdf': info.get('/CreationDate', ''),
                    'fecha_modificacion_pdf': info.get('/ModDate', ''),
                    
                    # Metadatos extraídos del contenido
                    'idioma_detectado': 'español',  # Podrías detectar esto
                    'tipo_documento': 'libro',      # Podrías clasificar
                    'calidad_extraccion': 'alta'    # Basado en éxito del procesamiento
                }
                
                # Limpiar metadatos vacíos
                metadatos = {k: v for k, v in metadatos.items() if v}
                
                return metadatos
                
        except Exception as e:
            print(f"⚠️ Error extrayendo metadatos: {e}")
            return {
                'tamano_archivo_mb': round(os.path.getsize(pdf_path) / (1024 * 1024), 2),
                'hash_archivo': self._calcular_hash_archivo(pdf_path),
                'error_metadatos': str(e)
            }
    
    def _calcular_hash_archivo(self, file_path: str) -> str:
        """Calcular hash MD5 del archivo para detectar duplicados"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extraer_metadatos_del_contenido(self, texto_completo: str) -> Dict:
        """Intentar extraer metadatos analizando el contenido del texto"""
        # Dividir en líneas para análisis
        lineas = texto_completo.split('\n')
        
        metadatos = {
            'total_palabras': len(texto_completo.split()),
            'total_lineas': len(lineas),
            'total_caracteres': len(texto_completo),
        }
        
        # Intentar detectar autor en primeras líneas
        primeras_lineas = lineas[:10]
        for i, linea in enumerate(primeras_lineas):
            linea_limpia = linea.strip()
            if len(linea_limpia) > 3 and len(linea_limpia) < 100:
                # Patrones comunes de nombres de autor
                if any(palabra in linea_limpia.lower() for palabra in ['por', 'author', 'autor', 'written by']):
                    metadatos['autor_detectado'] = linea_limpia
                    break
        
        # Intentar detectar ISBN (patrón específico)
        import re
        isbn_pattern = r'\b(?:ISBN(?:: ?| ))?((?:97[89])?\d{9}[\dxX])\b'
        isbn_match = re.search(isbn_pattern, texto_completo)
        if isbn_match:
            metadatos['isbn_detectado'] = isbn_match.group(1)
        
        return metadatos