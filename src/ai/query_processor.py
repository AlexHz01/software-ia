import openai
import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from config.config_manager import config_manager

class QueryProcessor:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=config_manager.get_api_key())
        
        # Configuraciones desde la sección específica
        self.modelo_chat = config_manager.get_modelo()
        self.temperatura = config_manager.get_temperatura()
        self.top_k = config_manager.get_top_k_fragmentos()
        self.umbral_similitud = config_manager.get_umbral_similitud()
        self.max_tokens_respuesta = config_manager.get_max_tokens_respuesta()
        self.incluir_referencias = config_manager.get("biblioteca_ia", "consulta.incluir_referencias", True)
        self.modelo_embeddings = config_manager.get_modelo_embeddings()
    
    def encontrar_fragmentos_relevantes(self, pregunta: str, fragmentos: List[Dict]) -> Tuple[List[Dict], List[int]]:
        """Encontrar los fragmentos más relevantes para la pregunta usando operaciones vectorizadas"""
        try:
            print(f"🔍 Buscando fragmentos relevantes para: '{pregunta[:50]}...'")
            
            # Generar embedding para la pregunta
            embedding_pregunta = self._generar_embedding(pregunta)
            if not embedding_pregunta:
                print("❌ No se pudo generar embedding para la pregunta")
                return fragmentos[:self.top_k], []
            
            # Filtrar fragmentos que tienen embedding
            fragmentos_con_embedding = [f for f in fragmentos if f.get('embedding')]
            if not fragmentos_con_embedding:
                print("⚠️ No hay fragmentos con embeddings para comparar")
                return [], []
                
            print(f"📊 Analizando {len(fragmentos_con_embedding)} fragmentos con embeddings")
            
            # Convertir embeddings a matriz numpy para cálculo vectorizado
            embeddings_matrix = np.array([f['embedding'] for f in fragmentos_con_embedding])
            embedding_pregunta_arr = np.array([embedding_pregunta])
            
            # Calcular similitudes en lote
            similitudes = cosine_similarity(embedding_pregunta_arr, embeddings_matrix)[0]
            
            fragmentos_con_similitud = []
            libros_referenciados = set()
            
            for i, similitud in enumerate(similitudes):
                if similitud >= self.umbral_similitud:
                    frag = fragmentos_con_embedding[i]
                    fragmentos_con_similitud.append({
                        **frag,
                        'similitud': float(similitud)
                    })
                    if frag.get('libro_id'):
                        libros_referenciados.add(frag['libro_id'])
            
            # Ordenar por similitud y tomar los top_k
            fragmentos_con_similitud.sort(key=lambda x: x.get('similitud', 0), reverse=True)
            fragmentos_finales = fragmentos_con_similitud[:self.top_k]
            
            print(f"✅ Encontrados {len(fragmentos_finales)} fragmentos relevantes")
            return fragmentos_finales, list(libros_referenciados)
            
        except Exception as e:
            print(f"❌ Error encontrando fragmentos relevantes: {e}")
            return fragmentos[:self.top_k], []
    
    def generar_respuesta(self, pregunta: str, fragmentos_relevantes: List[Dict], libros_referenciados: List[int]) -> str:
        """Generar respuesta usando los fragmentos relevantes"""
        try:
            if not fragmentos_relevantes:
                return "No encontré información relevante en los libros para responder tu pregunta. Por favor, intenta reformular tu pregunta o agrega más libros al sistema."
            
            print(f"🤖 Generando respuesta usando {len(fragmentos_relevantes)} fragmentos...")
            
            # Construir contexto con los fragmentos relevantes
            contexto = "\n\n".join([
                f"[Del libro '{frag.get('libro_titulo', 'Desconocido')}', página {frag.get('pagina', 'N/A')}]: {frag['contenido']}"
                for frag in fragmentos_relevantes
            ])
            
            # Preparar instrucciones basadas en configuración
            instrucciones_referencias = ""
            if self.incluir_referencias and len(libros_referenciados) > 0:
                instrucciones_referencias = "Incluye referencias a los libros y páginas específicas cuando sea relevante."
            
            prompt = f"""
Eres un Analista Experto en Derecho y Política.
Tu objetivo es asistir al usuario proporcionando análisis profesionales, profundos y fundamentados sobre temas jurídicos, políticos y de derechos.

CONTEXTO DE LOS DOCUMENTOS:
Basándote EXCLUSIVAMENTE en los siguientes fragmentos de libros, responde a la pregunta del usuario.

INSTRUCCIONES DE ANÁLISIS:
1.  **Rol Profesional**: Mantén un tono formal, objetivo y experto, propio de un consultor jurídico o politólogo senior.
2.  **Evidencia Estricta**: Usa SOLO la información de los fragmentos. Si un concepto clave no está en el texto, indícalo ("El texto proporcionado no aborda...") en lugar de inventar.
3.  **Terminología**: Utiliza terminología técnica jurídica y política adecuada cuando el contexto lo permita.
4.  **Estructura**: Organiza tu respuesta de manera lógica (Introducción, Análisis de Puntos Clave, Conclusión).
5.  {instrucciones_referencias}
6.  **Resolución de Conflictos**: Si hay visiones contrapuestas en los textos, exponse el debate o la contradicción claramente.

FRAGMENTOS DISPONIBLES:
{contexto}

PREGUNTA DE ANÁLISIS:
{pregunta}

ANÁLISIS EXPERTO:
"""
            
            response = self.openai_client.chat.completions.create(
                model=self.modelo_chat,
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un asistente experto en análisis jurídico, político y de derechos. Tu análisis se basa estrictamente en la evidencia documental proporcionada, manteniendo el rigor académico y profesional."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperatura,
                max_tokens=self.max_tokens_respuesta
            )
            
            respuesta = response.choices[0].message.content
            print("✅ Respuesta generada exitosamente")
            return respuesta
            
        except Exception as e:
            print(f"❌ Error generando respuesta: {e}")
            return f"Lo siento, hubo un error al procesar tu consulta: {str(e)}\n\nPor favor, verifica tu conexión a internet y tu configuración de API Key."
    
    def _generar_embedding(self, texto: str) -> List[float]:
        """Generar embedding para un texto"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.modelo_embeddings,
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generando embedding: {e}")
            return []