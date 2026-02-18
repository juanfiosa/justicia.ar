"""
JUSTICIA.ar - Motor de Clasificación de Casos
Clasifica casos en 4 niveles según complejidad
"""
import sqlite3
from typing import Dict, List, Tuple

class ClasificadorCasos:
    """
    Clasifica casos civiles en 4 niveles:
    - Nivel 1: Rutinario (resolución automática)
    - Nivel 2: Complejo (IA sugiere, humano revisa rápido)
    - Nivel 3: Difícil (deliberación humana asistida por IA)
    - Nivel 4: Constitucional (deliberación ampliada)
    """
    
    def __init__(self, db_path='justicia.db'):
        self.db_path = db_path
        self.criterios = self._cargar_criterios()
    
    def _cargar_criterios(self) -> List[Dict]:
        """Carga los criterios de clasificación desde la BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT factor, descripcion, peso, nivel_minimo 
            FROM criterios_clasificacion
        """)
        
        criterios = []
        for row in cursor.fetchall():
            criterios.append({
                'factor': row[0],
                'descripcion': row[1],
                'peso': row[2],
                'nivel_minimo': row[3]
            })
        
        conn.close()
        return criterios
    
    def clasificar_caso(self, caso: Dict) -> Tuple[int, float, str]:
        """
        Clasifica un caso y retorna (nivel, confianza, justificacion)
        
        Args:
            caso: Dict con keys: tipo_caso, monto_reclamado, descripcion_hechos, 
                  pruebas, tiene_contestacion, plantea_cuestion_constitucional
        
        Returns:
            Tuple de (nivel 1-4, confianza 0-1, justificación texto)
        """
        puntos = 0
        nivel_minimo_forzado = 1
        factores_aplicados = []
        
        # Análisis de monto
        monto = caso.get('monto_reclamado', 0)
        if monto < 300000:
            puntos += 2
            factores_aplicados.append("Monto bajo (< $300.000)")
        elif monto > 800000:
            puntos -= 1
            factores_aplicados.append("Monto elevado (> $800.000)")
        
        # Análisis de pruebas
        pruebas = caso.get('pruebas', '').lower()
        if any(palabra in pruebas for palabra in ['pagaré', 'contrato firmado', 'sentencia', 'documento fehaciente']):
            puntos += 3
            factores_aplicados.append("Prueba documental clara")
        
        # Análisis de contestación
        if not caso.get('tiene_contestacion', True):
            puntos += 3
            factores_aplicados.append("Demandado no contestó o admite hechos")
        
        # Análisis de tipo de caso y precedentes
        tipo_caso = caso.get('tipo_caso', '')
        if tipo_caso == 'cobro_suma_dinero' and 'pagaré' in pruebas:
            puntos += 3
            factores_aplicados.append("Cobro ejecutivo con título")
        
        # Análisis de complejidad fáctica
        descripcion = caso.get('descripcion_hechos', '').lower()
        palabras_complejidad = ['pericial', 'técnico', 'controvertido', 'testigos contradictorios', 'versiones encontradas']
        if any(palabra in descripcion for palabra in palabras_complejidad):
            puntos -= 2
            nivel_minimo_forzado = max(nivel_minimo_forzado, 2)
            factores_aplicados.append("Requiere prueba compleja o hechos controvertidos")
        
        # Análisis de cuestiones constitucionales
        if caso.get('plantea_cuestion_constitucional', False):
            puntos -= 4
            nivel_minimo_forzado = 4
            factores_aplicados.append("Plantea cuestión constitucional")
        
        # Análisis de cuestiones novedosas
        if 'novedoso' in descripcion or 'sin precedentes' in descripcion:
            puntos -= 3
            nivel_minimo_forzado = max(nivel_minimo_forzado, 3)
            factores_aplicados.append("Cuestión jurídica novedosa sin precedentes claros")
        
        # Determinar nivel basado en puntos
        if puntos >= 6:
            nivel_calculado = 1
            confianza = 0.95
        elif puntos >= 2:
            nivel_calculado = 2
            confianza = 0.85
        elif puntos >= -2:
            nivel_calculado = 3
            confianza = 0.75
        else:
            nivel_calculado = 4
            confianza = 0.65
        
        # Aplicar nivel mínimo forzado
        nivel_final = max(nivel_calculado, nivel_minimo_forzado)
        
        # Generar justificación
        justificacion = self._generar_justificacion(nivel_final, factores_aplicados, puntos)
        
        return nivel_final, confianza, justificacion
    
    def _generar_justificacion(self, nivel: int, factores: List[str], puntos: int) -> str:
        """Genera justificación textual de la clasificación"""
        
        descripciones_nivel = {
            1: "NIVEL 1 - CASO RUTINARIO (Resolución automática)",
            2: "NIVEL 2 - CASO COMPLEJO (IA sugiere, revisión humana rápida)",
            3: "NIVEL 3 - CASO DIFÍCIL (Deliberación humana asistida por IA)",
            4: "NIVEL 4 - CASO CONSTITUCIONAL (Deliberación ampliada)"
        }
        
        justificacion = f"{descripciones_nivel[nivel]}\n\n"
        justificacion += f"Puntaje de clasificación: {puntos}\n\n"
        justificacion += "Factores considerados:\n"
        
        for i, factor in enumerate(factores, 1):
            justificacion += f"{i}. {factor}\n"
        
        if nivel == 1:
            justificacion += "\nEste caso puede resolverse automáticamente por la IA dado que presenta:\n"
            justificacion += "- Hechos claros y no controvertidos\n"
            justificacion += "- Prueba suficiente y fehaciente\n"
            justificacion += "- Jurisprudencia uniforme aplicable\n"
        elif nivel == 2:
            justificacion += "\nEste caso requiere revisión humana porque presenta cierta complejidad,\n"
            justificacion += "pero puede ser resuelta rápidamente con asistencia de la IA.\n"
        elif nivel == 3:
            justificacion += "\nEste caso requiere deliberación humana completa porque presenta:\n"
            justificacion += "- Cuestiones de hecho o derecho complejas\n"
            justificacion += "- Necesidad de valoración jurídica sofisticada\n"
            justificacion += "La IA asistirá generando múltiples perspectivas argumentales.\n"
        else:
            justificacion += "\nEste caso requiere el máximo nivel de deliberación porque involucra:\n"
            justificacion += "- Cuestiones constitucionales o de derechos fundamentales\n"
            justificacion += "- Necesidad de participación ampliada\n"
        
        return justificacion


def test_clasificador():
    """Función de prueba del clasificador"""
    clasificador = ClasificadorCasos()
    
    # Caso de prueba 1: Muy rutinario
    caso1 = {
        'tipo_caso': 'cobro_suma_dinero',
        'monto_reclamado': 200000,
        'descripcion_hechos': 'Préstamo documentado en pagaré vencido hace 6 meses',
        'pruebas': 'pagaré firmado y certificado notarialmente',
        'tiene_contestacion': False,
        'plantea_cuestion_constitucional': False
    }
    
    nivel, confianza, just = clasificador.clasificar_caso(caso1)
    print("=" * 70)
    print("CASO 1: Cobro de pagaré sin contestación")
    print("=" * 70)
    print(just)
    print(f"\nConfianza: {confianza:.2%}\n")
    
    # Caso de prueba 2: Complejo
    caso2 = {
        'tipo_caso': 'daños_perjuicios',
        'monto_reclamado': 450000,
        'descripcion_hechos': 'Accidente de tránsito con versiones contradictorias sobre quién tenía prioridad',
        'pruebas': 'Testigos con versiones encontradas, necesita pericial',
        'tiene_contestacion': True,
        'plantea_cuestion_constitucional': False
    }
    
    nivel, confianza, just = clasificador.clasificar_caso(caso2)
    print("=" * 70)
    print("CASO 2: Accidente con versiones contradictorias")
    print("=" * 70)
    print(just)
    print(f"\nConfianza: {confianza:.2%}\n")
    
    # Caso de prueba 3: Constitucional
    caso3 = {
        'tipo_caso': 'daños_perjuicios',
        'monto_reclamado': 500000,
        'descripcion_hechos': 'Caso novedoso sobre responsabilidad por daño moral en redes sociales',
        'pruebas': 'Capturas de pantalla, pericias técnicas',
        'tiene_contestacion': True,
        'plantea_cuestion_constitucional': True
    }
    
    nivel, confianza, just = clasificador.clasificar_caso(caso3)
    print("=" * 70)
    print("CASO 3: Cuestión constitucional novedosa")
    print("=" * 70)
    print(just)
    print(f"\nConfianza: {confianza:.2%}\n")

if __name__ == '__main__':
    test_clasificador()
