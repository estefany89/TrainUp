# view_rutinas.py - API + DICCIONARIO DE RESPALDO
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import requests

# ===== DICCIONARIO DE RESPALDO (solo se usa si falta info de la API) =====
CATEGORIAS_RESPALDO = {
    8: {  # Arms
        'nombre': 'Brazos',
        'imagen': '/static/images/ejercicios/brazos.jpg',
        'nombres_ejercicios': [
            'Curl de bíceps con mancuerna',
            'Extensión de tríceps',
            'Curl martillo',
            'Fondos en paralelas',
            'Curl con barra',
            'Press francés',
        ],
        'descripciones': [
            'Ejercicio fundamental para desarrollo de bíceps. Mantén los codos fijos.',
            'Trabaja los tríceps de forma aislada. Mantén una postura estable.',
            'Variante del curl que trabaja bíceps y antebrazo.',
            'Ejercicio compuesto para tríceps, pecho y hombros.',
            'Ejercicio básico para masa de bíceps.',
            'Movimiento de aislamiento para tríceps.',
        ]
    },
    9: {  # Legs
        'nombre': 'Piernas',
        'imagen': '/static/images/ejercicios/piernas.jpg',
        'nombres_ejercicios': [
            'Sentadilla con barra',
            'Prensa de piernas',
            'Peso muerto rumano',
            'Zancadas',
            'Extensión de cuádriceps',
            'Curl femoral',
        ],
        'descripciones': [
            'El rey de los ejercicios de pierna. Trabaja cuádriceps y glúteos.',
            'Ejercicio de máquina ideal para volumen.',
            'Enfoque en isquiotibiales y glúteos.',
            'Ejercicio unilateral excelente para equilibrio.',
            'Aislamiento de cuádriceps en máquina.',
            'Trabaja específicamente los isquiotibiales.',
        ]
    },
    10: {  # Abs
        'nombre': 'Abdominales',
        'imagen': '/static/images/ejercicios/abdominales.jpg',
        'nombres_ejercicios': [
            'Plancha frontal',
            'Crunch abdominal',
            'Elevación de piernas',
            'Plancha lateral',
            'Russian twist',
            'Mountain climbers',
        ],
        'descripciones': [
            'Ejercicio isométrico fundamental para core.',
            'Básico para recto abdominal.',
            'Trabaja la parte baja del abdomen.',
            'Fortalece oblicuos y estabilidad lateral.',
            'Ejercicio dinámico para oblicuos.',
            'Cardio funcional que trabaja core completo.',
        ]
    },
    11: {  # Chest
        'nombre': 'Pecho',
        'imagen': '/static/images/ejercicios/pecho.jpg',
        'nombres_ejercicios': [
            'Press de banca con barra',
            'Press con mancuernas',
            'Aperturas con mancuernas',
            'Press inclinado',
            'Fondos en paralelas',
            'Cruces en polea',
        ],
        'descripciones': [
            'Ejercicio fundamental para pecho.',
            'Permite mayor rango de movimiento.',
            'Aislamiento perfecto para pecho.',
            'Enfatiza pecho superior.',
            'Excelente para pecho inferior y tríceps.',
            'Aislamiento con tensión constante.',
        ]
    },
    12: {  # Back
        'nombre': 'Espalda',
        'imagen': '/static/images/ejercicios/espalda.jpg',
        'nombres_ejercicios': [
            'Dominadas',
            'Remo con barra',
            'Peso muerto',
            'Remo con mancuerna',
            'Pull-over',
            'Jalón al pecho',
        ],
        'descripciones': [
            'Rey de ejercicios de espalda. Trabaja todo el dorsal.',
            'Fundamental para espesor de espalda.',
            'Ejercicio compuesto rey. Trabaja toda la cadena posterior.',
            'Permite trabajar cada lado independientemente.',
            'Aislamiento de dorsal.',
            'Alternativa a dominadas.',
        ]
    },
    13: {  # Shoulders
        'nombre': 'Hombros',
        'imagen': '/static/images/ejercicios/hombros.jpg',
        'nombres_ejercicios': [
            'Press militar',
            'Elevaciones laterales',
            'Elevaciones frontales',
            'Press Arnold',
            'Pájaros (deltoides posterior)',
            'Remo al mentón',
        ],
        'descripciones': [
            'Básico para desarrollo de hombros.',
            'Aislamiento de deltoides lateral.',
            'Trabaja deltoides anterior.',
            'Variante con rotación.',
            'Fundamental para deltoides posterior.',
            'Trabaja deltoides y trapecios.',
        ]
    },
    14: {  # Calves
        'nombre': 'Pantorrillas',
        'imagen': '/static/images/ejercicios/pantorrillas.jpg',
        'nombres_ejercicios': [
            'Elevación de talones de pie',
            'Elevación de talones sentado',
            'Elevación en prensa',
            'Elevación unilateral',
        ],
        'descripciones': [
            'Ejercicio fundamental para gemelos.',
            'Trabaja el sóleo específicamente.',
            'Variante en prensa de piernas.',
            'Trabaja equilibrio y simetría.',
        ]
    }
}


@method_decorator(login_required, name='dispatch')
class RutinasSocioView(View):
    def get(self, request):
        return render(request, 'gimnasio/rutinas_socio.html')


@method_decorator(login_required, name='dispatch')
class RutinasAPI(View):
    def get(self, request):
        try:
            print("🚀 Iniciando carga desde API + Diccionario de respaldo...")

            # ===== PASO 1: Obtener TODAS las imágenes de la API =====
            print("📸 Obteniendo imágenes de la API...")
            imagenes_dict = {}
            imagenes_url = "https://wger.de/api/v2/exerciseimage/"

            while imagenes_url:
                imagenes_response = requests.get(imagenes_url, timeout=15)
                if imagenes_response.ok:
                    imagenes_data = imagenes_response.json()

                    for img in imagenes_data.get('results', []):
                        exercise_base = img.get('exercise_base')
                        if exercise_base:
                            if exercise_base not in imagenes_dict:
                                imagenes_dict[exercise_base] = []

                            imagenes_dict[exercise_base].append({
                                'url': img.get('image'),
                                'is_main': img.get('is_main', False)
                            })

                    imagenes_url = imagenes_data.get('next')
                else:
                    break

            # Crear diccionario final de imágenes de la API
            imagenes_api = {}
            for exercise_base, imgs in imagenes_dict.items():
                img_principal = next((img['url'] for img in imgs if img['is_main']), None)
                if not img_principal and imgs:
                    img_principal = imgs[0]['url']
                if img_principal:
                    imagenes_api[exercise_base] = img_principal

            print(f"✅ Imágenes de API: {len(imagenes_api)}")

            # ===== PASO 2: Obtener categorías =====
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
                print(f"⚠️ Error categorías: {e}")

            # ===== PASO 3: Obtener músculos =====
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
                print(f"⚠️ Error músculos: {e}")

            # ===== PASO 4: Obtener equipamiento =====
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
                print(f"⚠️ Error equipamiento: {e}")

            # ===== PASO 5: Obtener ejercicios =====
            print("💪 Obteniendo ejercicios de la API...")
            ejercicios_response = requests.get(
                "https://wger.de/api/v2/exercise/?language=2&limit=200",
                timeout=15
            )
            ejercicios_response.raise_for_status()
            ejercicios_data = ejercicios_response.json()
            ejercicios_raw = ejercicios_data.get('results', [])

            print(f"📥 Ejercicios obtenidos: {len(ejercicios_raw)}")

            # ===== PASO 6: Construir rutinas (API + respaldo) =====
            rutinas = []
            contador_respaldo = {}
            stats = {
                'nombre_api': 0,
                'nombre_respaldo': 0,
                'descripcion_api': 0,
                'descripcion_respaldo': 0,
                'imagen_api': 0,
                'imagen_respaldo': 0,
            }

            for ejercicio_api in ejercicios_raw:
                categoria_id = ejercicio_api.get('category')
                exercise_base = ejercicio_api.get('exercise_base')

                # Inicializar contador de respaldo para esta categoría
                if categoria_id not in contador_respaldo:
                    contador_respaldo[categoria_id] = 0

                # ===== NOMBRE: Prioridad a API, respaldo si falta =====
                nombre_api = ejercicio_api.get('name', '').strip()

                if nombre_api:
                    nombre = nombre_api
                    stats['nombre_api'] += 1
                else:
                    # Usar nombre del diccionario de respaldo
                    categoria_respaldo = CATEGORIAS_RESPALDO.get(categoria_id)
                    if categoria_respaldo:
                        indice = contador_respaldo[categoria_id] % len(categoria_respaldo['nombres_ejercicios'])
                        nombre = categoria_respaldo['nombres_ejercicios'][indice]
                        contador_respaldo[categoria_id] += 1
                        stats['nombre_respaldo'] += 1
                    else:
                        nombre = f"Ejercicio #{ejercicio_api.get('id', '?')}"
                        stats['nombre_respaldo'] += 1

                # ===== DESCRIPCIÓN: Prioridad a API, respaldo si falta =====
                descripcion_api = ejercicio_api.get('description', '').strip()

                if descripcion_api:
                    descripcion = descripcion_api
                    stats['descripcion_api'] += 1
                else:
                    # Usar descripción del diccionario de respaldo
                    categoria_respaldo = CATEGORIAS_RESPALDO.get(categoria_id)
                    if categoria_respaldo and contador_respaldo[categoria_id] > 0:
                        indice = (contador_respaldo[categoria_id] - 1) % len(categoria_respaldo['descripciones'])
                        descripcion = categoria_respaldo['descripciones'][indice]
                        stats['descripcion_respaldo'] += 1
                    else:
                        cat_nombre = categorias_dict.get(categoria_id, 'gimnasio')
                        descripcion = f"Ejercicio de {cat_nombre.lower()}. Consulta con tu entrenador."
                        stats['descripcion_respaldo'] += 1

                # ===== IMAGEN: Prioridad a API, respaldo si falta =====
                imagen_api = imagenes_api.get(exercise_base)

                if imagen_api:
                    imagen = imagen_api
                    es_imagen_respaldo = False
                    stats['imagen_api'] += 1
                else:
                    # Usar imagen del diccionario de respaldo
                    categoria_respaldo = CATEGORIAS_RESPALDO.get(categoria_id)
                    if categoria_respaldo:
                        imagen = categoria_respaldo['imagen']
                    else:
                        imagen = '/static/images/ejercicios/default.jpg'
                    es_imagen_respaldo = True
                    stats['imagen_respaldo'] += 1

                # ===== CATEGORÍA =====
                categoria_nombre_api = categorias_dict.get(categoria_id)
                if categoria_nombre_api:
                    categoria_nombre = categoria_nombre_api
                else:
                    categoria_respaldo = CATEGORIAS_RESPALDO.get(categoria_id)
                    categoria_nombre = categoria_respaldo['nombre'] if categoria_respaldo else 'General'

                # ===== MÚSCULOS Y EQUIPAMIENTO =====
                musculos_ids = ejercicio_api.get('muscles', [])
                musculos_nombres = [musculos_dict.get(m_id, '') for m_id in musculos_ids]
                musculos_nombres = [m for m in musculos_nombres if m]

                equipos_ids = ejercicio_api.get('equipment', [])
                equipos_nombres = [equipos_dict.get(e_id, '') for e_id in equipos_ids]
                equipos_nombres = [e for e in equipos_nombres if e]

                rutinas.append({
                    'id': ejercicio_api.get('id'),
                    'name': nombre,
                    'description': descripcion,
                    'category': categoria_nombre,
                    'muscles': musculos_nombres if musculos_nombres else ['No especificado'],
                    'equipment': equipos_nombres if equipos_nombres else ['Sin equipo'],
                    'image': imagen,
                    'is_fallback_image': es_imagen_respaldo
                })

            # ===== ESTADÍSTICAS DETALLADAS =====
            total = len(rutinas)
            print(f"\n{'=' * 70}")
            print(f"📊 ESTADÍSTICAS DETALLADAS:")
            print(f"   Total de rutinas: {total}")
            print(f"\n   📝 NOMBRES:")
            print(f"      ✅ Desde API: {stats['nombre_api']} ({stats['nombre_api'] / total * 100:.1f}%)")
            print(
                f"      🔄 Desde diccionario: {stats['nombre_respaldo']} ({stats['nombre_respaldo'] / total * 100:.1f}%)")
            print(f"\n   📄 DESCRIPCIONES:")
            print(f"      ✅ Desde API: {stats['descripcion_api']} ({stats['descripcion_api'] / total * 100:.1f}%)")
            print(
                f"      🔄 Desde diccionario: {stats['descripcion_respaldo']} ({stats['descripcion_respaldo'] / total * 100:.1f}%)")
            print(f"\n   🖼️ IMÁGENES:")
            print(f"      ✅ Desde API: {stats['imagen_api']} ({stats['imagen_api'] / total * 100:.1f}%)")
            print(
                f"      🔄 Desde diccionario: {stats['imagen_respaldo']} ({stats['imagen_respaldo'] / total * 100:.1f}%)")
            print(f"\n   📈 COBERTURA TOTAL: 100% (API + Respaldo)")
            print(f"{'=' * 70}\n")

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