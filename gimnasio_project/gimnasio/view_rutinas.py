# view_rutinas.py - VERSIÓN MEJORADA CON IMÁGENES
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import requests


@method_decorator(login_required, name='dispatch')
class RutinasSocioView(View):
    def get(self, request):
        return render(request, 'gimnasio/rutinas_socio.html')


@method_decorator(login_required, name='dispatch')
class RutinasAPI(View):
    def get(self, request):
        try:
            # ===== PASO 1: Obtener TODAS las imágenes disponibles =====
            print("📸 Obteniendo imágenes...")
            imagenes_dict = {}
            imagenes_url = "https://wger.de/api/v2/exerciseimage/"

            while imagenes_url:
                imagenes_response = requests.get(imagenes_url, timeout=15)
                if imagenes_response.ok:
                    imagenes_data = imagenes_response.json()

                    # Procesar imágenes
                    for img in imagenes_data.get('results', []):
                        exercise_base = img.get('exercise_base')
                        if exercise_base:
                            # Almacenar tanto la imagen principal como alternativas
                            if exercise_base not in imagenes_dict:
                                imagenes_dict[exercise_base] = []

                            imagenes_dict[exercise_base].append({
                                'url': img.get('image'),
                                'is_main': img.get('is_main', False)
                            })

                    # Siguiente página
                    imagenes_url = imagenes_data.get('next')
                else:
                    break

            print(f"✅ Se obtuvieron imágenes para {len(imagenes_dict)} ejercicios base")

            # ===== PASO 2: Crear diccionario optimizado de imágenes =====
            imagenes_finales = {}
            for exercise_base, imgs in imagenes_dict.items():
                # Priorizar imagen principal
                img_principal = next((img['url'] for img in imgs if img['is_main']), None)

                # Si no hay principal, usar la primera disponible
                if not img_principal and imgs:
                    img_principal = imgs[0]['url']

                if img_principal:
                    imagenes_finales[exercise_base] = img_principal

            print(f"🎯 Imágenes finales procesadas: {len(imagenes_finales)}")

            # ===== PASO 3: Obtener categorías =====
            categorias_dict = {}
            try:
                categorias_response = requests.get(
                    "https://wger.de/api/v2/exercisecategory/",
                    timeout=10
                )
                if categorias_response.ok:
                    categorias_data = categorias_response.json()
                    for cat in categorias_data.get('results', []):
                        categorias_dict[cat['id']] = cat['name']
            except Exception as e:
                print(f"⚠️ Error obteniendo categorías: {e}")

            # ===== PASO 4: Obtener músculos =====
            musculos_dict = {}
            try:
                musculos_response = requests.get(
                    "https://wger.de/api/v2/muscle/",
                    timeout=10
                )
                if musculos_response.ok:
                    musculos_data = musculos_response.json()
                    for musc in musculos_data.get('results', []):
                        musculos_dict[musc['id']] = musc['name']
            except Exception as e:
                print(f"⚠️ Error obteniendo músculos: {e}")

            # ===== PASO 5: Obtener equipamiento =====
            equipos_dict = {}
            try:
                equipos_response = requests.get(
                    "https://wger.de/api/v2/equipment/",
                    timeout=10
                )
                if equipos_response.ok:
                    equipos_data = equipos_response.json()
                    for equip in equipos_data.get('results', []):
                        equipos_dict[equip['id']] = equip['name']
            except Exception as e:
                print(f"⚠️ Error obteniendo equipamiento: {e}")

            # ===== PASO 6: Obtener ejercicios en español =====
            print("💪 Obteniendo ejercicios en español...")
            ejercicios_response = requests.get(
                "https://wger.de/api/v2/exercise/?language=2&limit=100",
                timeout=15
            )
            ejercicios_response.raise_for_status()
            ejercicios_data = ejercicios_response.json()

            print(f"📋 Ejercicios obtenidos: {len(ejercicios_data.get('results', []))}")

            # ===== PASO 7: Construir lista de rutinas =====
            rutinas = []
            ejercicios_con_imagen = 0
            ejercicios_sin_imagen = 0

            for item in ejercicios_data.get('results', []):
                nombre = item.get('name', '').strip()

                # Validar nombre
                if not nombre:
                    nombre = "Ejercicio sin nombre"

                exercise_base = item.get('exercise_base')
                categoria_id = item.get('category')

                # Buscar imagen
                imagen = imagenes_finales.get(exercise_base)

                if imagen:
                    ejercicios_con_imagen += 1
                else:
                    ejercicios_sin_imagen += 1

                # Obtener información adicional
                categoria_nombre = categorias_dict.get(categoria_id, 'General')

                musculos_ids = item.get('muscles', [])
                musculos_nombres = [musculos_dict.get(m_id, '') for m_id in musculos_ids]
                musculos_nombres = [m for m in musculos_nombres if m]

                equipos_ids = item.get('equipment', [])
                equipos_nombres = [equipos_dict.get(e_id, '') for e_id in equipos_ids]
                equipos_nombres = [e for e in equipos_nombres if e]

                # Limpiar descripción HTML
                descripcion = item.get('description', 'Sin descripción disponible').strip()
                if not descripcion or descripcion == '':
                    descripcion = 'Sin descripción disponible'

                rutinas.append({
                    'id': item.get('id'),
                    'name': nombre,
                    'description': descripcion,
                    'category': categoria_nombre,
                    'muscles': musculos_nombres if musculos_nombres else ['No especificado'],
                    'equipment': equipos_nombres if equipos_nombres else ['Sin equipo'],
                    'image': imagen,
                    'exercise_base': exercise_base  # Para debug
                })

            # ===== ESTADÍSTICAS =====
            print(f"\n{'=' * 50}")
            print(f"📊 ESTADÍSTICAS FINALES:")
            print(f"   Total de rutinas: {len(rutinas)}")
            print(f"   ✅ Con imagen: {ejercicios_con_imagen}")
            print(f"   ❌ Sin imagen: {ejercicios_sin_imagen}")
            print(f"   📈 Porcentaje con imagen: {(ejercicios_con_imagen / len(rutinas) * 100):.1f}%")
            print(f"{'=' * 50}\n")

            if rutinas:
                print(f"🔍 Ejemplo de rutina:")
                print(f"   Nombre: {rutinas[0]['name']}")
                print(f"   Exercise Base: {rutinas[0]['exercise_base']}")
                print(f"   Imagen: {rutinas[0]['image']}")
                print(f"   Categoría: {rutinas[0]['category']}")

            return JsonResponse(rutinas, safe=False)

        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR DE RED: {str(e)}")
            return JsonResponse({
                'error': f'Error al conectar con la API: {str(e)}'
            }, status=500)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': f'Error interno: {str(e)}'
            }, status=500)