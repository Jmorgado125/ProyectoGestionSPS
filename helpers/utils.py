from functools import wraps

def requiere_rol(rol_permitido):
    """
    Decorador para verificar si el usuario tiene el rol permitido.
    """
    def decorador(func):
        @wraps(func)
        def wrapper(usuario_actual, *args, **kwargs):
            if usuario_actual.get('rol') != rol_permitido:
                print(f"Permiso denegado: se requiere rol '{rol_permitido}'.")
                return {
                    "status": "error",
                    "message": f"No tiene permiso para realizar esta acción. Rol requerido: {rol_permitido}."
                }
            return func(usuario_actual, *args, **kwargs)
        return wrapper
    return decorador
