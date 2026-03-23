import os
import tempfile
from pydub import AudioSegment
from openai import OpenAI
from config.config_manager import config_manager

class AudioProcessor:
    def __init__(self):
        # Usar la API key configurada
        self.api_key = config_manager.get_api_key()
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            
        # Voces de OpenAI TTS
        self.voz_alex = "onyx"   # Voz masculina
        self.voz_sofi = "nova"   # Voz femenina
        self.modelo_tts = "tts-1" # Más rápido. Para mayor calidad usar "tts-1-hd"
        
    def generar_podcast_audio(self, guion_texto: str, libro_id: int, titulo_libro: str) -> str:
        """
        Toma el guion escrito, genera el audio de las voces usando TTS,
        los une y rertorna la ruta del archivo mp3 final.
        """
        # Tratar de obtener la API si se configuró después de iniciar
        if not self.client:
            self.api_key = config_manager.get_api_key()
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key)
            else:
                raise ValueError("API Key de OpenAI no configurada.")
            
        lineas = guion_texto.split('\n')
        audios_generados = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            ultimo_hablante = "Alex"
            
            for i, linea in enumerate(lineas):
                linea = linea.strip()
                if not linea:
                    continue
                    
                hablante = None
                texto = linea
                
                # Eliminar marcas de negrita si existen
                linea_limpia = linea.replace("**", "")
                
                if linea_limpia.startswith("Alex:"):
                    hablante = "Alex"
                    texto = linea_limpia.split(":", 1)[1].strip()
                elif linea_limpia.startswith("Sofi:"):
                    hablante = "Sofi"
                    texto = linea_limpia.split(":", 1)[1].strip()
                else:
                    # Continuación del hablante anterior o texto descriptivo
                    if len(texto) > 5:
                        hablante = ultimo_hablante
                    else:
                        continue
                        
                if not texto.strip():
                    continue
                    
                ultimo_hablante = hablante
                voz = self.voz_alex if hablante == "Alex" else self.voz_sofi
                
                temp_file = os.path.join(temp_dir, f"segment_{i}.mp3")
                
                response = self.client.audio.speech.create(
                    model=self.modelo_tts,
                    voice=voz,
                    input=texto
                )
                response.stream_to_file(temp_file)
                
                segmento = AudioSegment.from_mp3(temp_file)
                audios_generados.append(segmento)
                
            if not audios_generados:
                raise ValueError("No se pudo extraer texto del guion para generar el audio.")
                
            # Unir segmentos con un ligero silencio para mayor naturalidad (400ms)
            silencio = AudioSegment.silent(duration=400)
            audio_final = audios_generados[0]
            
            for segmento in audios_generados[1:]:
                audio_final += silencio + segmento
                
            # Directorio final
            ruta_datos = config_manager.get("almacenamiento", "ruta_datos", "./data")
            dir_podcasts = os.path.join(ruta_datos, "podcasts")
            os.makedirs(dir_podcasts, exist_ok=True)
            
            # Nombre seguro
            nombre_seguro = "".join([c for c in titulo_libro if c.isalnum() or c.isspace()]).strip()
            nombre_archivo = f"podcast_{libro_id}_{nombre_seguro.replace(' ', '_')}.mp3"
            ruta_final = os.path.join(dir_podcasts, nombre_archivo)
            
            audio_final.export(ruta_final, format="mp3")
            return ruta_final
            
        finally:
            # Limpiar
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except: pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except: pass
            if os.path.exists(temp_dir):
                try: os.rmdir(temp_dir)
                except: pass
