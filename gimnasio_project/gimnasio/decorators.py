from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    """
    Decorador para verificar que el usuario sea administrador
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('gimnasio:login')

        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.rol == 'admin':
            return view_func(request, *args, **kwargs)

        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('gimnasio:inicio')

    return _wrapped_view


def socio_required(view_func):
    """
    Decorador para verificar que el usuario sea socio o admin
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('gimnasio:login')

        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.activo:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Tu cuenta no está activa.")
        return redirect('gimnasio:inicio')

    return _wrapped_view