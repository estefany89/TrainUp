# view_rutinas.py - VERSIÓN SIMPLIFICADA
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
            # Obtener ejercicios en español primero
            ejercicios_response = requests.get(
                "https://wger.de/api/v2/exercise/?language=2&limit=50",
                timeout=15
            )
            ejercicios_response.raise_for_status()
            ejercicios_data = ejercicios_response.json()

            print(f"DEBUG: Se obtuvieron {len(ejercicios_data.get('results', []))} ejercicios")

            # Obtener imágenes
            imagenes_response = requests.get(
                "https://wger.de/api/v2/exerciseimage/",
                timeout=15
            )
            imagenes_dict = {}
            if imagenes_response.ok:
                imagenes_data = imagenes_response.json()
                for img in imagenes_data.get('results', []):
                    exercise_base = img.get('exercise_base')
                    if img.get('is_main', False) and exercise_base:
                        imagenes_dict[exercise_base] = img.get('image')

            # Obtener categorías
            categorias_response = requests.get(
                "https://wger.de/api/v2/exercisecategory/",
                timeout=15
            )
            categorias_dict = {}
            if categorias_response.ok:
                categorias_data = categorias_response.json()
                for cat in categorias_data.get('results', []):
                    categorias_dict[cat['id']] = cat['name']

            # Obtener músculos
            musculos_response = requests.get(
                "https://wger.de/api/v2/muscle/",
                timeout=15
            )
            musculos_dict = {}
            if musculos_response.ok:
                musculos_data = musculos_response.json()
                for musc in musculos_data.get('results', []):
                    musculos_dict[musc['id']] = musc['name']

            # Obtener equipamiento
            equipos_response = requests.get(
                "https://wger.de/api/v2/equipment/",
                timeout=15
            )
            equipos_dict = {}
            if equipos_response.ok:
                equipos_data = equipos_response.json()
                for equip in equipos_data.get('results', []):
                    equipos_dict[equip['id']] = equip['name']

            # Construir la lista de rutinas
            rutinas = []
            for item in ejercicios_data.get('results', []):
                nombre = item.get('name', '').strip()

                # Saltar si no tiene nombre
                if not nombre:
                    nombre = "Ejercicio sin nombre"

                exercise_base = item.get('exercise_base')
                categoria_id = item.get('category')

                # Obtener imagen
                imagen = imagenes_dict.get(exercise_base)

                # Obtener nombres
                categoria_nombre = categorias_dict.get(categoria_id, 'General')
                musculos_ids = item.get('muscles', [])
                musculos_nombres = [musculos_dict.get(m_id, '') for m_id in musculos_ids]
                musculos_nombres = [m for m in musculos_nombres if m]  # Filtrar vacíos

                equipos_ids = item.get('equipment', [])
                equipos_nombres = [equipos_dict.get(e_id, '') for e_id in equipos_ids]
                equipos_nombres = [e for e in equipos_nombres if e]  # Filtrar vacíos

                rutinas.append({
                    'id': item.get('id'),
                    'name': nombre,
                    'description': item.get('description', 'Sin descripción disponible').strip(),
                    'category': categoria_nombre,
                    'muscles': musculos_nombres if musculos_nombres else ['No especificado'],
                    'equipment': equipos_nombres if equipos_nombres else ['Sin equipo'],
                    'image': imagen,
                })

            print(f"DEBUG: Rutinas finales: {len(rutinas)}")
            if rutinas:
                print(f"DEBUG: Ejemplo de rutina: {rutinas[0]['name']}, Imagen: {rutinas[0]['image']}")

            return JsonResponse(rutinas, safe=False)

        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)