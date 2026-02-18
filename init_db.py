"""
JUSTICIA.ar - Inicializador de Base de Datos
"""
import sqlite3
import os

def init_database(db_path='justicia.db'):
    """Inicializa la base de datos con el esquema y datos iniciales"""
    
    # Eliminar base de datos existente si existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Base de datos anterior eliminada: {db_path}")
    
    # Crear conexión
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creando esquema de base de datos...")
    
    # Leer y ejecutar schema.sql
    with open('../database/schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    print("Esquema creado exitosamente.")
    print("Poblando base de datos con datos iniciales...")
    
    # Leer y ejecutar seed_data.sql
    with open('../database/seed_data.sql', 'r', encoding='utf-8') as f:
        seed_sql = f.read()
        cursor.executescript(seed_sql)
    
    conn.commit()
    print("Datos iniciales cargados exitosamente.")
    
    # Verificar que los datos se cargaron
    cursor.execute("SELECT COUNT(*) FROM articulos_legales")
    articulos_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM casos_precedentes")
    precedentes_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios_count = cursor.fetchone()[0]
    
    print(f"\n✓ {articulos_count} artículos legales cargados")
    print(f"✓ {precedentes_count} casos precedentes cargados")
    print(f"✓ {usuarios_count} usuarios de ejemplo creados")
    print(f"\n¡Base de datos inicializada correctamente en {db_path}!")
    
    conn.close()

if __name__ == '__main__':
    init_database()
