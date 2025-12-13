#!/usr/bin/env python3
"""
Script para descargar imágenes de ejemplo de Unsplash
Ejecutar desde la raíz del proyecto: python descargar_imagenes.py
"""

import os
import requests
from pathlib import Path

# URLs de imágenes de alta calidad de Unsplash
IMAGENES_UNSPLASH = {
    'brazos.jpg': 'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&q=80',
    'piernas.jpg': 'https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=800&q=80',
    'abdominales.jpg': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80',
    'pecho.jpg': 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800&q=80',
    'espalda.jpg': 'https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=800&q=80',
    'hombros.jpg': 'https://images.unsplash.com/photo-1532384816664-01b8b7238c8d?w=800&q=80',
    'pantorrillas.jpg': 'https://images.unsplash.com/photo-1434682772747-f16d3ea162c3?w=800&q=80',
    'default.jpg': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80'
}


def descargar_imagenes():
    """Descarga las imágenes de ejemplo"""

    # Crear directorio
    directorio = Path('app/static/images/ejercicios')
    directorio.mkdir(parents=True, exist_ok=True)

    print("🎯 Descargando imágenes de ejemplo...\n")

    for nombre_archivo, url in IMAGENES_UNSPLASH.items():
        ruta_completa = directorio / nombre_archivo

        # Si ya existe, preguntar si sobrescribir
        if ruta_completa.exists():
            respuesta = input(f"⚠️  {nombre_archivo} ya existe. ¿Sobrescribir? (s/n): ")
            if respuesta.lower() != 's':
                print(f"⏭️  Saltando {nombre_archivo}")
                continue

        try:
            print(f"📥 Descargando {nombre_archivo}...", end=' ')
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(ruta_completa, 'wb') as f:
                f.write(response.content)

            tamaño = len(response.content) / 1024  # KB
            print(f"✅ ({tamaño:.1f} KB)")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n{'=' * 60}")
    print("✨ ¡Descarga completada!")
    print(f"📁 Imágenes guardadas en: {directorio.absolute()}")
    print(f"{'=' * 60}\n")

    # Listar archivos descargados
    print("📋 Archivos descargados:")
    for archivo in sorted(directorio.glob('*.jpg')):
        tamaño = archivo.stat().st_size / 1024
        print(f"   ✓ {archivo.name} ({tamaño:.1f} KB)")

    print("\n🚀 Ahora puedes reiniciar tu servidor Django:")
    print("   docker-compose restart")
    print("   # o")
    print("   python manage.py runserver")


if __name__ == '__main__':
    try:
        descargar_imagenes()
    except KeyboardInterrupt:
        print("\n\n⚠️  Descarga cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")