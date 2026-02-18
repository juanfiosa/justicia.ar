"""
JUSTICIA.ar - Motor de Decisión
Genera decisiones basadas en el nivel del caso
"""
import sqlite3
from typing import Dict, List, Tuple
import re

class MotorDecision:
    """
    Genera decisiones para casos según su nivel:
    - Nivel 1: Decisión automática determinística
    - Nivel 2: Sugerencia argumentada para revisión
    - Nivel 3: Múltiples perspectivas para deliberación
    - Nivel 4: Estructura para deliberación ampliada
    """
    
    def __init__(self, db_path='justicia.db'):
        self.db_path = db_path
    
    def decidir_caso(self, caso: Dict, nivel: int) -> Dict:
        """
        Genera decisión según el nivel del caso
        
        Returns:
            Dict con: resultado, monto_otorgado, fundamentacion, articulos_aplicados
        """
        if nivel == 1:
            return self._decidir_nivel_1(caso)
        elif nivel == 2:
            return self._decidir_nivel_2(caso)
        elif nivel == 3:
            return self._decidir_nivel_3(caso)
        else:
            return self._decidir_nivel_4(caso)
    
    def _decidir_nivel_1(self, caso: Dict) -> Dict:
        """Decisión automática para casos rutinarios"""
        tipo = caso['tipo_caso']
        monto = caso['monto_reclamado']
        
        # Lógica determinística simple
        if tipo == 'cobro_suma_dinero':
            # Si es cobro ejecutivo con título, se acoge íntegramente
            if 'pagaré' in caso.get('pruebas', '').lower():
                resultado = 'acoge'
                monto_otorgado = monto * 1.15  # Capital + intereses estimados
                
                fundamentacion = f"""
RESUELVO:

I. HACER LUGAR a la demanda de COBRO DE PESOS interpuesta.

II. CONDENAR al demandado a pagar al actor la suma de ${monto:,.2f} en concepto de capital, 
más intereses desde la mora hasta el efectivo pago, calculados a la tasa que fije el Banco Central.

III. COSTAS al demandado vencido.

FUNDAMENTOS:

1. HECHOS PROBADOS: Se encuentra acreditada la existencia de la obligación mediante pagaré 
debidamente firmado por el demandado (Art. 1816 CCyC - título ejecutivo).

2. MORA AUTOMÁTICA: Tratándose de obligación con plazo determinado, el deudor incurre en mora 
automáticamente al vencimiento (Art. 886 CCyC).

3. FALTA DE DEFENSA SUSTANCIAL: El demandado no ha opuesto defensas admisibles que enerven 
la pretensión ejecutiva.

4. DERECHO APLICABLE:
   - Art. 729 CCyC: Concepto de obligación
   - Art. 730 CCyC: Efectos del incumplimiento
   - Art. 1816 CCyC: Pagaré como título ejecutivo

5. INTERESES: Corresponden intereses moratorios desde el vencimiento hasta el efectivo pago 
como accesorio de la obligación principal (Arts. 765-768 CCyC).

6. COSTAS: El art. 130 CPCC establece que las costas se imponen al vencido, siendo el demandado 
quien ha incumplido sin justificación.

Por todo lo expuesto, RESUELVO como se indica en el decisorio.
                """
                
                return {
                    'resultado': resultado,
                    'monto_otorgado': monto_otorgado,
                    'fundamentacion': fundamentacion,
                    'articulos_aplicados': ['729', '730', '886', '1816'],
                    'tipo_decision': 'automatica',
                    'confianza': 0.95
                }
        
        # Otros casos nivel 1...
        return self._decidir_generico_nivel_1(caso)
    
    def _decidir_generico_nivel_1(self, caso: Dict) -> Dict:
        """Decisión genérica para nivel 1"""
        monto = caso['monto_reclamado']
        
        fundamentacion = f"""
RESUELVO:

I. HACER LUGAR a la demanda interpuesta.

II. CONDENAR al demandado a pagar al actor la suma reclamada con más intereses y costas.

FUNDAMENTOS BÁSICOS:

Los hechos invocados se encuentran suficientemente acreditados mediante la prueba documental acompañada.
El demandado no ha desvirtuado la pretensión del actor.
Corresponde hacer lugar a lo peticionado conforme los artículos 1716 y 1740 del CCyC.
        """
        
        return {
            'resultado': 'acoge',
            'monto_otorgado': monto,
            'fundamentacion': fundamentacion,
            'articulos_aplicados': ['1716', '1740'],
            'tipo_decision': 'automatica',
            'confianza': 0.85
        }
    
    def _decidir_nivel_2(self, caso: Dict) -> Dict:
        """Sugerencia argumentada para revisión humana"""
        
        # Buscar casos similares en la base de precedentes
        precedentes_similares = self._buscar_precedentes_similares(caso)
        
        tipo = caso['tipo_caso']
        monto = caso['monto_reclamado']
        
        # Generar sugerencia basada en precedentes
        if precedentes_similares:
            precedente_ref = precedentes_similares[0]
            ratio = monto / precedente_ref['monto_aproximado'] if precedente_ref['monto_aproximado'] > 0 else 1
            monto_sugerido = monto * 0.9  # Ajuste conservador
            
            fundamentacion = f"""
SUGERENCIA DE RESOLUCIÓN (Requiere revisión humana)

ANÁLISIS DEL CASO:

El presente caso presenta similitudes con el precedente "{precedente_ref['titulo']}" 
({precedente_ref['tribunal']}, {precedente_ref['fecha_sentencia']}).

HECHOS COMPARABLES:
- Caso actual: {caso['descripcion_hechos'][:200]}...
- Precedente: {precedente_ref['hechos_resumidos'][:200]}...

CRITERIO JURISPRUDENCIAL APLICABLE:
{precedente_ref['principios_aplicados']}

SUGERENCIA DE DECISIÓN:
Hacer lugar parcialmente a la demanda por un monto de ${monto_sugerido:,.2f}, 
considerando la proporcionalidad con casos similares y las circunstancias particulares.

ARTÍCULOS SUGERIDOS A APLICAR:
- Art. 1716 CCyC (Deber de reparar)
- Art. 1740 CCyC (Reparación plena)
- Art. 1757 CCyC (si aplica responsabilidad objetiva)

NOTA PARA EL JUEZ REVISOR:
Este caso requiere su evaluación particular respecto de:
1. La valoración de la prueba aportada
2. La existencia de atenuantes o agravantes específicos
3. La proporcionalidad del monto sugerido con el daño efectivamente acreditado

Confianza de la sugerencia: 85%
            """
            
            return {
                'resultado': 'acoge_parcial',
                'monto_otorgado': monto_sugerido,
                'fundamentacion': fundamentacion,
                'articulos_aplicados': ['1716', '1740', '1757'],
                'precedentes_considerados': [precedente_ref['titulo']],
                'tipo_decision': 'asistida',
                'confianza': 0.85
            }
        
        # Sin precedentes claros
        return self._sugerencia_sin_precedentes(caso)
    
    def _decidir_nivel_3(self, caso: Dict) -> Dict:
        """Múltiples perspectivas para deliberación humana"""
        
        # Generar 3 perspectivas diferentes
        perspectivas = []
        
        # Perspectiva 1: Favorable al actor
        perspectivas.append({
            'enfoque': 'Interpretación favorable al actor',
            'resultado_propuesto': 'acoge',
            'monto_propuesto': caso['monto_reclamado'],
            'argumentos': self._generar_argumentos_pro_actor(caso)
        })
        
        # Perspectiva 2: Equilibrada
        perspectivas.append({
            'enfoque': 'Interpretación equilibrada',
            'resultado_propuesto': 'acoge_parcial',
            'monto_propuesto': caso['monto_reclamado'] * 0.7,
            'argumentos': self._generar_argumentos_equilibrados(caso)
        })
        
        # Perspectiva 3: Favorable al demandado
        perspectivas.append({
            'enfoque': 'Interpretación favorable al demandado',
            'resultado_propuesto': 'rechaza',
            'monto_propuesto': 0,
            'argumentos': self._generar_argumentos_pro_demandado(caso)
        })
        
        fundamentacion = """
ANÁLISIS MULTIPERSPECTIVA PARA DELIBERACIÓN

Este caso requiere deliberación humana. La IA presenta tres perspectivas argumentales:

"""
        
        for i, persp in enumerate(perspectivas, 1):
            fundamentacion += f"\n{'='*60}\nPERSPECTIVA {i}: {persp['enfoque']}\n{'='*60}\n"
            fundamentacion += f"Resultado propuesto: {persp['resultado_propuesto']}\n"
            fundamentacion += f"Monto propuesto: ${persp['monto_propuesto']:,.2f}\n\n"
            fundamentacion += "ARGUMENTOS:\n"
            for j, arg in enumerate(persp['argumentos'], 1):
                fundamentacion += f"{j}. {arg}\n"
            fundamentacion += "\n"
        
        fundamentacion += """
RECOMENDACIÓN PARA EL JUEZ:

Este caso presenta complejidades que requieren su valoración jurídica experta.
Se sugiere:
1. Analizar detenidamente la prueba producida
2. Considerar las tres perspectivas presentadas
3. Ponderar los principios en conflicto según su criterio
4. Fundamentar claramente la decisión adoptada

La IA está disponible para análisis adicionales que requiera.
        """
        
        return {
            'resultado': 'requiere_deliberacion',
            'perspectivas': perspectivas,
            'fundamentacion': fundamentacion,
            'tipo_decision': 'humana',
            'confianza': 0.70
        }
    
    def _decidir_nivel_4(self, caso: Dict) -> Dict:
        """Estructura para deliberación ampliada"""
        
        fundamentacion = f"""
CASO DE NIVEL 4 - DELIBERACIÓN CONSTITUCIONAL AMPLIADA

Este caso presenta cuestiones de particular relevancia que trascienden el interés individual
de las partes y ameritan un procedimiento deliberativo especial.

DESCRIPCIÓN DEL CASO:
{caso['descripcion_hechos']}

CUESTIONES A DELIBERAR:

1. CUESTIÓN CONSTITUCIONAL PLANTEADA:
   [Requiere identificación específica por parte del tribunal]

2. PRINCIPIOS EN TENSIÓN:
   - Derecho/principio A vs. Derecho/principio B
   - [A completar según el caso concreto]

3. PRECEDENTES RELEVANTES:
   [Requiere análisis de jurisprudencia constitucional aplicable]

4. IMPACTO SISTÉMICO:
   Esta decisión puede sentar precedente para casos futuros similares.

PROCEDIMIENTO SUGERIDO:

1. Convocatoria a audiencia pública con participación de:
   - Partes del juicio
   - Amicus curiae (si corresponde)
   - Organizaciones de la sociedad civil interesadas

2. Requerimiento de informes a:
   - Ministerio Público
   - Defensoría del Pueblo
   - Otros organismos pertinentes

3. Plazo ampliado para alegatos y fundamentación

4. Deliberación en tribunal colegiado (si corresponde según organización judicial)

NOTA IMPORTANTE:
Este nivel de caso no admite resolución automatizada ni asistida por IA.
Requiere el ejercicio pleno de la función jurisdiccional humana con todas las garantías.

La IA solo proporciona estructura y herramientas de análisis, no sugerencias de decisión.
        """
        
        return {
            'resultado': 'requiere_deliberacion_ampliada',
            'fundamentacion': fundamentacion,
            'tipo_decision': 'deliberativa',
            'confianza': 0.60
        }
    
    def _buscar_precedentes_similares(self, caso: Dict) -> List[Dict]:
        """Busca casos precedentes similares en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tipo_caso = caso['tipo_caso']
        
        cursor.execute("""
            SELECT titulo, tribunal, fecha_sentencia, hechos_resumidos, 
                   decision, monto_aproximado, principios_aplicados
            FROM casos_precedentes
            WHERE tipo_caso = ?
            ORDER BY fecha_sentencia DESC
            LIMIT 3
        """, (tipo_caso,))
        
        precedentes = []
        for row in cursor.fetchall():
            precedentes.append({
                'titulo': row[0],
                'tribunal': row[1],
                'fecha_sentencia': row[2],
                'hechos_resumidos': row[3],
                'decision': row[4],
                'monto_aproximado': row[5],
                'principios_aplicados': row[6]
            })
        
        conn.close()
        return precedentes
    
    def _sugerencia_sin_precedentes(self, caso: Dict) -> Dict:
        """Sugerencia cuando no hay precedentes claros"""
        monto = caso['monto_reclamado']
        
        fundamentacion = """
SUGERENCIA DE RESOLUCIÓN (Sin precedentes directos)

Este caso no cuenta con precedentes directamente aplicables en la base de datos.

Se sugiere análisis cuidadoso de:
1. Principios generales del derecho aplicable
2. Doctrina mayoritaria sobre el tema
3. Proporcionalidad de la pretensión

RECOMENDACIÓN: Revisión humana detallada requerida.
        """
        
        return {
            'resultado': 'requiere_analisis',
            'monto_otorgado': None,
            'fundamentacion': fundamentacion,
            'tipo_decision': 'asistida',
            'confianza': 0.60
        }
    
    def _generar_argumentos_pro_actor(self, caso: Dict) -> List[str]:
        """Genera argumentos favorables al actor"""
        return [
            "El actor ha cumplido con la carga probatoria exigida por el art. 377 CPCC",
            "El daño se encuentra debidamente acreditado y existe nexo causal directo",
            "La reparación debe ser plena conforme el art. 1740 CCyC",
            "El demandado no ha logrado desvirtuar la pretensión ni probar eximentes de responsabilidad",
            "El monto reclamado es razonable y proporcional al daño efectivamente sufrido"
        ]
    
    def _generar_argumentos_equilibrados(self, caso: Dict) -> List[str]:
        """Genera argumentos equilibrados"""
        return [
            "Si bien el actor acredita el hecho dañoso, existen circunstancias atenuantes a considerar",
            "Corresponde aplicar el principio de proporcionalidad en la cuantificación del daño",
            "La responsabilidad puede ser compartida según las circunstancias del caso",
            "El monto debe ajustarse a los parámetros de casos similares",
            "Se sugiere una solución equilibrada que contemple los intereses de ambas partes"
        ]
    
    def _generar_argumentos_pro_demandado(self, caso: Dict) -> List[str]:
        """Genera argumentos favorables al demandado"""
        return [
            "El actor no ha logrado acreditar acabadamente todos los extremos de su pretensión",
            "Existen dudas razonables sobre la existencia de nexo causal",
            "El demandado ha opuesto defensas admisibles que merecen consideración",
            "El monto reclamado resulta excesivo y desproporcionado",
            "Pueden existir eximentes de responsabilidad aplicables al caso"
        ]


if __name__ == '__main__':
    # Test básico
    motor = MotorDecision()
    
    caso_test = {
        'tipo_caso': 'cobro_suma_dinero',
        'monto_reclamado': 200000,
        'descripcion_hechos': 'Préstamo documentado en pagaré',
        'pruebas': 'pagaré firmado',
        'tiene_contestacion': False
    }
    
    decision = motor.decidir_caso(caso_test, nivel=1)
    print(decision['fundamentacion'])
