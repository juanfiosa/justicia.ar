"""
JUSTICIA.ar - API Backend
Servidor Flask con endpoints para el sistema de resolución asistida
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import json

from clasificador import ClasificadorCasos
from motor_decision import MotorDecision

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde el frontend

DB_PATH = 'justicia.db'

# Inicializar componentes
clasificador = ClasificadorCasos(DB_PATH)
motor_decision = MotorDecision(DB_PATH)

# ===== UTILIDADES =====

def get_db():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
    return conn

def dict_from_row(row):
    """Convierte Row de sqlite3 a diccionario"""
    return dict(zip(row.keys(), row))

# ===== ENDPOINTS - CASOS =====

@app.route('/api/casos', methods=['POST'])
def crear_caso():
    """
    Crea un nuevo caso y lo clasifica automáticamente
    """
    try:
        data = request.json
        
        # Validar datos requeridos
        campos_requeridos = ['tipo_caso', 'actor_id', 'demandado_nombre', 
                            'monto_reclamado', 'descripcion_hechos']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'error': f'Campo requerido faltante: {campo}'}), 400
        
        # Clasificar el caso
        nivel, confianza, justificacion = clasificador.clasificar_caso(data)
        
        # Guardar en BD
        conn = get_db()
        cursor = conn.cursor()
        
        # Generar número de expediente
        cursor.execute("SELECT COUNT(*) as total FROM casos")
        total_casos = cursor.fetchone()['total']
        numero_expediente = f"JUS-{datetime.now().year}-{total_casos + 1:05d}"
        
        cursor.execute("""
            INSERT INTO casos (
                numero_expediente, tipo_caso, actor_id, demandado_nombre,
                monto_reclamado, descripcion_hechos, pruebas,
                nivel_clasificacion, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'clasificado')
        """, (
            numero_expediente,
            data['tipo_caso'],
            data['actor_id'],
            data['demandado_nombre'],
            data['monto_reclamado'],
            data['descripcion_hechos'],
            data.get('pruebas', ''),
            nivel
        ))
        
        caso_id = cursor.lastrowid
        
        # Registrar auditoría
        cursor.execute("""
            INSERT INTO auditoria (caso_id, tipo_evento, descripcion, usuario_id)
            VALUES (?, 'clasificacion', ?, ?)
        """, (caso_id, f"Caso clasificado como Nivel {nivel}", data['actor_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'caso_id': caso_id,
            'numero_expediente': numero_expediente,
            'nivel': nivel,
            'confianza': confianza,
            'justificacion': justificacion
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/casos/<int:caso_id>', methods=['GET'])
def obtener_caso(caso_id):
    """Obtiene detalles de un caso específico"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, u.nombre as actor_nombre, u.email as actor_email
            FROM casos c
            JOIN usuarios u ON c.actor_id = u.id
            WHERE c.id = ?
        """, (caso_id,))
        
        caso = cursor.fetchone()
        
        if not caso:
            return jsonify({'error': 'Caso no encontrado'}), 404
        
        # Obtener decisión si existe
        cursor.execute("""
            SELECT * FROM decisiones WHERE caso_id = ? ORDER BY fecha_decision DESC LIMIT 1
        """, (caso_id,))
        
        decision = cursor.fetchone()
        
        conn.close()
        
        resultado = {
            'caso': dict_from_row(caso),
            'decision': dict_from_row(decision) if decision else None
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/casos', methods=['GET'])
def listar_casos():
    """Lista todos los casos con filtros opcionales"""
    try:
        # Parámetros de filtro
        estado = request.args.get('estado')
        nivel = request.args.get('nivel')
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT c.*, u.nombre as actor_nombre
            FROM casos c
            JOIN usuarios u ON c.actor_id = u.id
            WHERE 1=1
        """
        params = []
        
        if estado:
            query += " AND c.estado = ?"
            params.append(estado)
        
        if nivel:
            query += " AND c.nivel_clasificacion = ?"
            params.append(nivel)
        
        query += " ORDER BY c.fecha_ingreso DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        casos = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'casos': [dict_from_row(caso) for caso in casos],
            'total': len(casos)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ENDPOINTS - DECISIONES =====

@app.route('/api/casos/<int:caso_id>/decidir', methods=['POST'])
def decidir_caso(caso_id):
    """
    Genera decisión para un caso según su nivel
    """
    try:
        # Obtener el caso
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM casos WHERE id = ?", (caso_id,))
        caso_row = cursor.fetchone()
        
        if not caso_row:
            return jsonify({'error': 'Caso no encontrado'}), 404
        
        caso = dict_from_row(caso_row)
        
        # Generar decisión según nivel
        nivel = caso['nivel_clasificacion']
        
        caso_para_decision = {
            'tipo_caso': caso['tipo_caso'],
            'monto_reclamado': caso['monto_reclamado'],
            'descripcion_hechos': caso['descripcion_hechos'],
            'pruebas': caso['pruebas'],
            'tiene_contestacion': True,  # Simplificación
            'plantea_cuestion_constitucional': False  # Simplificación
        }
        
        decision_generada = motor_decision.decidir_caso(caso_para_decision, nivel)
        
        # Guardar decisión en BD
        cursor.execute("""
            INSERT INTO decisiones (
                caso_id, tipo_decision, resultado, monto_otorgado,
                fundamentacion, confianza_ia
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            caso_id,
            decision_generada['tipo_decision'],
            decision_generada.get('resultado', 'pendiente'),
            decision_generada.get('monto_otorgado'),
            decision_generada['fundamentacion'],
            decision_generada.get('confianza', 0.0)
        ))
        
        decision_id = cursor.lastrowid
        
        # Actualizar estado del caso
        nuevo_estado = 'resuelto' if nivel == 1 else 'en_revision'
        cursor.execute("""
            UPDATE casos SET estado = ?, fecha_resolucion = ? WHERE id = ?
        """, (nuevo_estado, datetime.now(), caso_id))
        
        # Auditoría
        cursor.execute("""
            INSERT INTO auditoria (caso_id, decision_id, tipo_evento, descripcion)
            VALUES (?, ?, 'decision_generada', ?)
        """, (caso_id, decision_id, f"Decisión de tipo {decision_generada['tipo_decision']} generada"))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'decision_id': decision_id,
            'decision': decision_generada
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/decisiones/<int:decision_id>/aprobar', methods=['POST'])
def aprobar_decision(decision_id):
    """
    Permite a un funcionario aprobar una decisión de Nivel 2
    """
    try:
        data = request.json
        funcionario_id = data.get('funcionario_id')
        observaciones = data.get('observaciones', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Actualizar decisión
        cursor.execute("""
            UPDATE decisiones 
            SET funcionario_id = ?
            WHERE id = ?
        """, (funcionario_id, decision_id))
        
        # Actualizar caso a resuelto
        cursor.execute("""
            UPDATE casos 
            SET estado = 'resuelto', fecha_resolucion = ?
            WHERE id = (SELECT caso_id FROM decisiones WHERE id = ?)
        """, (datetime.now(), decision_id))
        
        # Auditoría
        cursor.execute("""
            INSERT INTO auditoria (
                caso_id, decision_id, tipo_evento, descripcion, usuario_id
            )
            SELECT caso_id, ?, 'decision_aprobada', ?, ?
            FROM decisiones WHERE id = ?
        """, (decision_id, f"Decisión aprobada. Obs: {observaciones}", funcionario_id, decision_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ENDPOINTS - ESTADÍSTICAS =====

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas del sistema"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Total de casos por nivel
        cursor.execute("""
            SELECT nivel_clasificacion, COUNT(*) as total
            FROM casos
            GROUP BY nivel_clasificacion
        """)
        casos_por_nivel = {row['nivel_clasificacion']: row['total'] for row in cursor.fetchall()}
        
        # Total de casos por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as total
            FROM casos
            GROUP BY estado
        """)
        casos_por_estado = {row['estado']: row['total'] for row in cursor.fetchall()}
        
        # Casos resueltos vs pendientes
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN estado = 'resuelto' THEN 1 ELSE 0 END) as resueltos,
                SUM(CASE WHEN estado != 'resuelto' THEN 1 ELSE 0 END) as pendientes
            FROM casos
        """)
        resolucion = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'casos_por_nivel': casos_por_nivel,
            'casos_por_estado': casos_por_estado,
            'resueltos': resolucion['resueltos'] or 0,
            'pendientes': resolucion['pendientes'] or 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ENDPOINTS - UTILIDADES =====

@app.route('/api/articulos', methods=['GET'])
def listar_articulos():
    """Lista artículos legales disponibles"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articulos_legales ORDER BY numero_articulo")
        articulos = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'articulos': [dict_from_row(art) for art in articulos]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/precedentes', methods=['GET'])
def listar_precedentes():
    """Lista casos precedentes"""
    try:
        tipo_caso = request.args.get('tipo_caso')
        
        conn = get_db()
        cursor = conn.cursor()
        
        if tipo_caso:
            cursor.execute("""
                SELECT * FROM casos_precedentes 
                WHERE tipo_caso = ?
                ORDER BY fecha_sentencia DESC
            """, (tipo_caso,))
        else:
            cursor.execute("""
                SELECT * FROM casos_precedentes 
                ORDER BY fecha_sentencia DESC
            """)
        
        precedentes = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'precedentes': [dict_from_row(p) for p in precedentes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'JUSTICIA.ar API',
        'version': '0.1.0'
    }), 200

# ===== INICIO DEL SERVIDOR =====

if __name__ == '__main__':
    print("=" * 70)
    print("JUSTICIA.ar - Sistema de Resolución Asistida")
    print("API Backend iniciando...")
    print("=" * 70)
    print("\nEndpoints disponibles:")
    print("  POST   /api/casos                  - Crear nuevo caso")
    print("  GET    /api/casos                  - Listar casos")
    print("  GET    /api/casos/<id>             - Obtener caso específico")
    print("  POST   /api/casos/<id>/decidir     - Generar decisión")
    print("  POST   /api/decisiones/<id>/aprobar - Aprobar decisión")
    print("  GET    /api/estadisticas           - Estadísticas del sistema")
    print("  GET    /api/articulos              - Listar artículos legales")
    print("  GET    /api/precedentes            - Listar precedentes")
    print("  GET    /api/health                 - Health check")
    print("\n" + "=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
