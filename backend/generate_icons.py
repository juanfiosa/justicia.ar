"""
Generador de íconos para PWA de JUSTICIA.ar
Ejecutar: python generate_icons.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Crea un ícono cuadrado con el logo de JUSTICIA.ar"""
    
    # Crear imagen con fondo morado
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Símbolo de balanza ⚖️ 
    # Como no podemos usar emoji directamente, dibujamos un diseño simple
    
    # Fondo circular blanco
    padding = size // 6
    circle_size = size - (2 * padding)
    circle_bbox = [padding, padding, padding + circle_size, padding + circle_size]
    draw.ellipse(circle_bbox, fill='white')
    
    # Dibujar una balanza estilizada
    center_x = size // 2
    center_y = size // 2
    
    # Base de la balanza
    base_width = int(size * 0.15)
    base_height = int(size * 0.1)
    base_y = int(size * 0.7)
    draw.rectangle(
        [center_x - base_width, base_y, center_x + base_width, base_y + base_height],
        fill='#667eea'
    )
    
    # Poste vertical
    post_width = int(size * 0.05)
    post_height = int(size * 0.35)
    post_y = base_y - post_height
    draw.rectangle(
        [center_x - post_width//2, post_y, center_x + post_width//2, base_y],
        fill='#667eea'
    )
    
    # Barra horizontal
    bar_width = int(size * 0.5)
    bar_height = int(size * 0.04)
    bar_y = post_y + int(size * 0.05)
    draw.rectangle(
        [center_x - bar_width//2, bar_y, center_x + bar_width//2, bar_y + bar_height],
        fill='#667eea'
    )
    
    # Platos (círculos a los lados)
    plate_radius = int(size * 0.1)
    left_plate_x = center_x - bar_width//2
    right_plate_x = center_x + bar_width//2
    plate_y = bar_y + bar_height
    
    # Plato izquierdo
    draw.ellipse(
        [left_plate_x - plate_radius, plate_y, left_plate_x + plate_radius, plate_y + plate_radius * 2],
        fill='#667eea'
    )
    
    # Plato derecho
    draw.ellipse(
        [right_plate_x - plate_radius, plate_y, right_plate_x + plate_radius, plate_y + plate_radius * 2],
        fill='#667eea'
    )
    
    # Guardar imagen
    img.save(output_path, 'PNG', quality=100)
    print(f"✓ Ícono generado: {output_path} ({size}x{size})")

def main():
    """Genera todos los íconos necesarios para la PWA"""
    
    print("Generando íconos para PWA de JUSTICIA.ar...\n")
    
    # Crear directorio si no existe
    output_dir = '../frontend'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Tamaños estándar para PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        output_path = os.path.join(output_dir, f'icon-{size}x{size}.png')
        create_icon(size, output_path)
    
    print(f"\n✅ {len(sizes)} íconos generados exitosamente en {output_dir}/")
    print("\nÍconos creados:")
    for size in sizes:
        print(f"  - icon-{size}x{size}.png")
    
    print("\n🎨 Nota: Si quieres un diseño personalizado, puedes editar estos íconos")
    print("   con cualquier editor de imágenes (Photoshop, GIMP, Figma, etc.)")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Error: Pillow no está instalado")
        print("Instala con: pip install Pillow")
        print("\nAlternativamente, puedes:")
        print("1. Crear los íconos manualmente con cualquier editor de imágenes")
        print("2. Usar un generador online: https://www.pwabuilder.com/imageGenerator")
