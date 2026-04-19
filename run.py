"""
JUSTICIA ARGENTINA - Script de lanzamiento
Uso: python run.py [--indexar] [--max N] [--port PORT]
"""
import sys
import os
import argparse

# Asegurar paths
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

# Cargar variables de entorno desde .env
_env_path = os.path.join(ROOT, '.env')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                _v = _v.strip()
                if _v:
                    os.environ.setdefault(_k.strip(), _v)

def main():
    parser = argparse.ArgumentParser(description='JUSTICIA ARGENTINA')
    parser.add_argument('--indexar', action='store_true', help='Ejecutar indexación de SAIJ antes de iniciar')
    parser.add_argument('--max', type=int, default=0, help='Máximo registros a indexar (0=todos)')
    parser.add_argument('--port', type=int, default=8000, help='Puerto del servidor')
    parser.add_argument('--solo-indexar', action='store_true', help='Solo indexar, no iniciar servidor')
    args = parser.parse_args()

    if args.indexar or args.solo_indexar:
        print("\n=== INDEXACIÓN ===\n")
        from indexador.pipeline import IndexadorJurisprudencia
        idx = IndexadorJurisprudencia()
        idx.indexar_dataset(max_registros=args.max)
        if args.solo_indexar:
            return

    print("\n=== INICIANDO SERVIDOR ===\n")
    import uvicorn
    from api.servidor import app
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == '__main__':
    main()
