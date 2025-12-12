#!/bin/bash

# Esperar a que la base de datos esté lista
echo "Esperando a PostgreSQL..."
while ! pg_isready -h db -p 5432 -U postgres; do
  sleep 1
done
echo "PostgreSQL está listo!"

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Crear superusuario si no existe (opcional)
# python manage.py createsuperuser --noinput --username admin --email admin@trainup.com || true

# Ejecutar el comando pasado al contenedor
exec "$@"
