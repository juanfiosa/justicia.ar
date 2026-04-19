"""
SCRAPER LEGISLACIÓN PROVINCIAL
================================
Descarga y chunka por artículo los textos completos de:
  - Constituciones provinciales (24 + CABA)
  - Códigos procesales civiles y penales por provincia

Estrategia de fuentes (en orden de prioridad):
  1. SAIJ XML via descarga-archivo?guid= (endpoint real con texto completo)
  2. URL oficial registrada en fuentes_textos_provinciales.json
  3. Log de error -> requiere intervencion manual

Salida: datos/textos_provinciales/{provincia_id}_{tipo}.json
  { "provincia", "tipo", "nombre", "numero", "articulos": [
      {"numero": "1", "titulo": "...", "texto": "..."}
  ]}
"""

import re
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False

# Regex para detectar artículos en textos legales argentinos
ARTICULO_RE = re.compile(
    r'(?:^|\n)\s*'
    r'(?:ART[ÍI]CULO|Art[íi]culo|ARTICULO|Articulo|ART\.?)\s+'
    r'(\d+(?:\s*(?:bis|ter|quáter|quater|quinquies))?)\s*'
    r'[°ºo]?\s*\.?\s*[-—–\.]*\s*',
    re.IGNORECASE | re.MULTILINE
)

# Timeout para requests HTTP (segundos)
HTTP_TIMEOUT = 30


# ── Descarga HTTP ────────────────────────────────────────────────────────────

def _fetch_url(url: str, intentos: int = 3) -> bytes:
    """Descarga URL con reintentos. Retorna bytes o lanza excepción."""
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (compatible; JusticiaArgentinaBot/1.0; '
            '+https://github.com/justicia-ar)'
        )
    }
    for intento in range(1, intentos + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(f"404: {url}")
            if intento == intentos:
                raise
            time.sleep(5 * intento)
        except Exception:
            if intento == intentos:
                raise
            time.sleep(5 * intento)


def _saij_xml_texto(saij_url: str) -> str | None:
    """
    Obtiene el texto completo de una norma SAIJ via:
    1. Busca el UUID en la API JSON de SAIJ usando el id-infojus (e.g. LPW1000000)
    2. Descarga el XML via descarga-archivo?guid={uuid}
    3. Extrae el contenido del tag <sancion>

    Retorna el texto extraído o None si falla.
    """
    if not saij_url:
        return None
    # Extraer el id-infojus del URL (ej: LPW1000000, LPB0007425)
    raw = saij_url.strip().rstrip('/')
    id_infojus = raw.split('/')[-1].upper()
    if not id_infojus:
        return None

    # Buscar en la API (con retry si rate-limited)
    uuid = None
    for intento in range(3):
        try:
            params = urllib.parse.urlencode({
                'r': f'id-infojus:{id_infojus}',
                'o': 0, 'p': 1, 'f': 'Total'
            })
            api_url = f'https://www.saij.gob.ar/busqueda?{params}'
            raw_bytes = _fetch_url(api_url, intentos=2)
            data = json.loads(raw_bytes)
            docs = data.get('searchResults', {}).get('documentResultList', [])
            if docs:
                abstract = json.loads(docs[0]['documentAbstract'])
                uuid = abstract['document']['metadata']['uuid']
                break
            # 0 resultados = posible rate limiting; esperar y reintentar
            if intento < 2:
                time.sleep(10 * (intento + 1))
        except Exception as e:
            print(f"    SAIJ API error para {id_infojus}: {e}")
            if intento < 2:
                time.sleep(5)
    if not uuid:
        return None

    # Descargar XML
    time.sleep(1)  # pausa entre la busqueda y la descarga
    try:
        xml_url = (f'https://www.saij.gob.ar/descarga-archivo'
                   f'?guid={uuid}&name=doc.xml')
        xml_bytes = _fetch_url(xml_url, intentos=2)
    except Exception as e:
        print(f"    SAIJ descarga error para {uuid}: {e}")
        return None

    # Parsear XML y extraer articulos estructurados o <sancion> como fallback
    try:
        xml_text = xml_bytes.decode('utf-8', errors='replace')
        xml_text = re.sub(r' xmlns[^"]*"[^"]*"', '', xml_text)
        root = ET.fromstring(xml_text)

        # Opcion 1: articulos estructurados con <articulo><numero-articulo><texto>
        articulos_els = root.findall('.//articulo')
        if articulos_els:
            partes = []
            for art in articulos_els:
                texto_el = art.find('texto')
                if texto_el is not None:
                    t = _limpiar_texto(''.join(texto_el.itertext()))
                else:
                    t = _limpiar_texto(''.join(art.itertext()))
                if t and len(t) > 20:
                    partes.append(t)
            if len(partes) >= 3:  # al menos 3 artículos para considerar válido
                return '\n\n'.join(partes)

        # Opcion 2: tag <sancion> con texto plano suficientemente largo
        sancion = root.find('.//sancion')
        if sancion is not None:
            t = _limpiar_texto(''.join(sancion.itertext()))
            if len(t) > 500:
                return t

        # Sin texto de calidad -> None (no usar el XML crudo como fallback)
        return None
    except Exception as e:
        print(f"    SAIJ XML parse error: {e}")
        return None


def _wayback_url(saij_url: str) -> str | None:
    """Consulta Wayback Machine CDX API para obtener la snapshot más reciente."""
    if not saij_url or 'saij.gob.ar' not in saij_url:
        return None
    # Asegura protocolo
    raw = saij_url if saij_url.startswith('http') else 'http://' + saij_url
    api = (f'https://archive.org/wayback/available?url={raw}'
           f'&timestamp=20240101')
    try:
        data = json.loads(_fetch_url(api, intentos=2))
        snap = data.get('archived_snapshots', {}).get('closest', {})
        if snap.get('available'):
            return snap['url']
    except Exception:
        pass
    return None


# ── Extracción de texto ──────────────────────────────────────────────────────

def _limpiar_texto(raw: str) -> str:
    """Limpieza básica de texto legal."""
    # Quitar markup SAIJ
    raw = re.sub(r'\[\[/?[a-z][^\]]*\]\]', ' ', raw)
    # Colapsar espacios múltiples / tabs
    raw = re.sub(r'[ \t]+', ' ', raw)
    # Máximo dos saltos de línea consecutivos
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


_JS_BOILERPLATE = [
    'function(i,s,o,g,r,a,m)',
    'GoogleAnalyticsObject',
    'window._paq',
    'window.dataLayer',
    'document.documentElement.className',
    'Sistema de Informaci',  # SAIJ header sin contenido
    '123456789-0abc',       # UUID genérico de SAIJ (XML metadatos sin texto)
]


def _es_contenido_valido(texto: str) -> bool:
    """Devuelve False si el texto parece ser boilerplate JS en vez de texto legal."""
    if len(texto) < 200:
        return False
    for marker in _JS_BOILERPLATE:
        if marker in texto[:500]:
            return False
    # Al menos debe tener alguna palabra legal característica
    palabras_legales = ['artículo', 'articulo', 'ley', 'decreto', 'código',
                        'provincia', 'derechos', 'capítulo', 'sección']
    texto_lower = texto.lower()
    return any(p in texto_lower for p in palabras_legales)


def _extraer_texto_html(html_bytes: bytes, encoding: str = 'utf-8') -> str:
    """Extrae texto de HTML usando BeautifulSoup si está disponible."""
    if not BS4_OK:
        text = html_bytes.decode(encoding, errors='replace')
        text = re.sub(r'<[^>]+>', ' ', text)
        return _limpiar_texto(text)

    soup = BeautifulSoup(html_bytes, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
        tag.decompose()

    # Intentar extraer solo el contenido principal
    contenido = None
    for selector in ['main', 'article', '#content', '.content',
                     '.texto-norma', '.norma', '#texto', '.articulo']:
        el = soup.select_one(selector)
        if el:
            contenido = el.get_text(separator='\n')
            break
    if not contenido:
        contenido = soup.get_text(separator='\n')

    return _limpiar_texto(contenido)


def _extraer_texto_pdf(pdf_bytes: bytes) -> str:
    """Extrae texto de PDF usando pdfplumber."""
    if not PDF_OK:
        raise RuntimeError(
            "pdfplumber no instalado. Ejecutar: pip install pdfplumber"
        )
    import io
    texto = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto.append(t)
    return _limpiar_texto('\n'.join(texto))


def _detectar_formato(url: str, content_type: str = '') -> str:
    """Detecta formato del recurso: 'pdf', 'html', 'text'."""
    url_lower = url.lower()
    if '.pdf' in url_lower:
        return 'pdf'
    if 'pdf' in content_type.lower():
        return 'pdf'
    return 'html'


# ── Chunking por artículo ────────────────────────────────────────────────────

def chunkear_por_articulo(texto: str) -> list[dict]:
    """
    Divide el texto de una norma en chunks por artículo.

    Retorna lista de dicts: {"numero": str, "texto": str}

    Si el texto no tiene artículos detectables (norma muy corta o sin
    estructura), retorna un único chunk con todo el texto.
    """
    matches = list(ARTICULO_RE.finditer(texto))

    if not matches:
        return [{"numero": "único", "texto": texto[:3000]}]

    articulos = []
    for i, match in enumerate(matches):
        num_art = match.group(1).strip()
        inicio  = match.end()
        fin     = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        texto_art = texto[inicio:fin].strip()
        if len(texto_art) < 10:
            continue
        articulos.append({
            "numero": num_art,
            "texto":  texto_art[:3000],
        })

    return articulos if articulos else [{"numero": "único",
                                         "texto": texto[:3000]}]


# ── Descargador principal ────────────────────────────────────────────────────

def descargar_y_procesar(fuente: dict,
                          salida_dir: Path,
                          forzar: bool = False) -> dict | None:
    """
    Descarga y procesa una norma a partir de su descriptor de fuente.

    fuente = {
      "provincia":    str,
      "provincia_id": str,
      "tipo":         str,   # 'constitucion' | 'codigo_procesal' | ...
      "nombre":       str,
      "numero":       str,
      "url_oficial":  str | None,
      "saij_url":     str | None,   # para fallback Wayback Machine
      "formato":      str,  # 'html' | 'pdf' | 'auto'
    }

    Retorna el dict del documento procesado o None si falló.
    """
    prov_id = fuente.get('provincia_id', 'xx').replace('/', '_')
    tipo    = fuente.get('tipo', 'norma').replace(' ', '_').lower()
    archivo = salida_dir / f"{prov_id}_{tipo}.json"

    if archivo.exists() and not forzar:
        print(f"  Ya existe: {archivo.name}")
        return None

    urls_a_probar = []
    if fuente.get('url_oficial'):
        urls_a_probar.append(fuente['url_oficial'])
    # SAIJ directo (el sitio volvió a estar activo en 2026)
    saij_url = fuente.get('saij_url', '')
    if saij_url:
        direct = saij_url if saij_url.startswith('http') else 'http://' + saij_url
        urls_a_probar.append(direct)
    # Fallback Wayback Machine
    wayback = _wayback_url(saij_url)
    if wayback:
        urls_a_probar.append(wayback)

    if not urls_a_probar:
        print(f"  [SIN URL] {fuente['nombre']}")
        return None

    texto = None

    # Prioridad 1: SAIJ XML (fuente directa con texto completo)
    saij_url = fuente.get('saij_url', '')
    if saij_url:
        print(f"  SAIJ XML: {saij_url.split('/')[-1]}...")
        texto = _saij_xml_texto(saij_url)
        if texto and _es_contenido_valido(texto):
            print(f"    -> SAIJ XML OK ({len(texto)} chars)")
        else:
            if texto:
                print(f"    -> SAIJ XML invalido ({len(texto)} chars)")
            texto = None

    # Prioridad 2: URLs oficiales como fallback
    if not texto:
        for url in urls_a_probar:
            try:
                print(f"  Descargando: {url[:80]}...")
                raw = _fetch_url(url)
                fmt = fuente.get('formato', 'auto')
                if fmt == 'auto':
                    fmt = _detectar_formato(url)
                if fmt == 'pdf':
                    texto = _extraer_texto_pdf(raw)
                else:
                    texto = _extraer_texto_html(raw)
                if _es_contenido_valido(texto):
                    break
                print(f"    Contenido invalido (JS boilerplate o muy corto): {url[:60]}")
                texto = None  # intentar siguiente URL
            except FileNotFoundError:
                print(f"    404 en {url[:60]}")
            except Exception as e:
                print(f"    Error en {url[:60]}: {e}")

    if not texto:
        print(f"  [FALLO] No se pudo obtener texto de: {fuente['nombre']}")
        return None

    articulos = chunkear_por_articulo(texto)
    doc = {
        "provincia":    fuente['provincia'],
        "provincia_id": fuente['provincia_id'],
        "tipo":         tipo,
        "nombre":       fuente['nombre'],
        "numero":       fuente.get('numero', ''),
        "articulos":    articulos,
        "texto_completo_len": len(texto),
    }

    salida_dir.mkdir(parents=True, exist_ok=True)
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    print(f"  OK: {fuente['nombre']} -> {len(articulos)} articulos")
    return doc


def descargar_todas_las_fuentes(fuentes_json: str = None,
                                 salida_dir: str = None,
                                 tipos_filtro: list = None,
                                 forzar: bool = False) -> dict:
    """
    Lee el catálogo de fuentes y descarga los textos que faltan.

    Args:
        fuentes_json: path a fuentes_textos_provinciales.json
        salida_dir:   carpeta de salida para los JSONs
        tipos_filtro: lista de tipos a descargar (None = todos)
                      ej: ['constitucion', 'codigo_procesal']
        forzar:       re-descarga aunque ya exista

    Retorna: {"ok": int, "fallo": int, "saltados": int}
    """
    base = Path(__file__).parent.parent.parent

    if fuentes_json is None:
        fuentes_json = str(base / 'datos' / 'fuentes_textos_provinciales.json')
    if salida_dir is None:
        salida_dir = str(base / 'datos' / 'textos_provinciales')

    with open(fuentes_json, encoding='utf-8') as f:
        catalogo = json.load(f)

    salida = Path(salida_dir)
    stats = {"ok": 0, "fallo": 0, "saltados": 0}

    for fuente in catalogo.get('fuentes', []):
        tipo = fuente.get('tipo', '')
        if tipos_filtro and tipo not in tipos_filtro:
            continue

        resultado = descargar_y_procesar(fuente, salida, forzar=forzar)
        if resultado is None:
            # Verificar si ya existía
            prov_id = fuente.get('provincia_id', 'xx').replace('/', '_')
            tipo_fn = tipo.replace(' ', '_').lower()
            if (salida / f"{prov_id}_{tipo_fn}.json").exists():
                stats["saltados"] += 1
            else:
                stats["fallo"] += 1
        else:
            stats["ok"] += 1

        time.sleep(3)  # pausa entre requests para evitar rate limiting SAIJ

    print(f"\nScraping: {stats['ok']} OK, "
          f"{stats['fallo']} fallos, {stats['saltados']} saltados")
    return stats
