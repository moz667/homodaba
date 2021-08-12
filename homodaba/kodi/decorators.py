from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import HttpResponseForbidden

from homodaba.settings import KODI_API_USER, KODI_API_KEY

def json_basic_auth(function):
    @wraps(function)
    def decorator(request, *args, **kwargs):
        # Permitimos a usuarios staff para simplificar pruebas
        if not request.user or not request.user.is_staff:
            if not 'Authorization' in request.headers:
                return HttpResponseForbidden()

            authorization = request.headers['Authorization']
            auth_parts = authorization.split(" ")

            if len(auth_parts) != 2:
                return HttpResponseForbidden()
            
            # Por ahora solo tenemos basic.. :P
            auth_type = auth_parts[0]

            auth_token_parts = auth_parts[1].split(":")

            if len(auth_token_parts) != 2:
                return HttpResponseForbidden()
            
            auth_username = auth_token_parts[0]
            auth_api_key = auth_token_parts[1]

            # Y como tampoco lo tenemos muy claro como vamos a hacer esto lo 
            # vamos a poner por env :D
            if auth_username != KODI_API_USER or auth_api_key != KODI_API_KEY:
                return HttpResponseForbidden()
        
        return function(request, *args, **kwargs)

    return decorator
