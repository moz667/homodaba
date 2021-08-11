from distutils.util import strtobool
import json
import re
import requests

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render

from .models import KodiHost


@login_required
def json_kodi_play(request):
    host_id = request.GET["host_id"] if "host_id" in request.GET.keys() else None
    storage_path = request.GET["storage_path"] if "storage_path" in request.GET.keys() else None

    kodi_host = None

    for k in KodiHost.objects.filter(id=host_id, owner=request.user).all():
        kodi_host = k
    
    if kodi_host:
        payload = json.dumps({ 
            "id": 1, 
            "jsonrpc": "2.0", 
            "method": "Player.Open", 
            "params": {
                "item": {
                    "file": storage_path
                }
            }
        })

        headers = {'content-type': "application/json", 'cache-control': "no-cache"}

        try:
            response = requests.request(
                "POST", kodi_host.get_json_rpc_url(), 
                data=payload, 
                headers=headers, 
                auth=(kodi_host.login_username, kodi_host.login_password)
            )

            return JsonResponse(json.loads(response.text))
        except Exception as e:
            print("Error al conectar con el servidor kodi.")
            print(e)

    raise Http404('No encontramos el servidor kodi.')

@login_required
def json_get_kodi_hosts(request):
    data = {
        "kodi_hosts": [],
    }

    for kodi_host in KodiHost.objects.filter(owner=request.user).all():
        data["kodi_hosts"].append({
            "id": kodi_host.id,
            "name": kodi_host.host_name,
            # "url": kodi_host.host_url, # No hace falta
            # "jsonrpc_url": kodi_host.get_json_rpc_url(), # Problema con CORS
            # "username": kodi_host.login_username, # No hace falta
            # "password": kodi_host.login_password, # No hace falta
        })

    return JsonResponse(data)

def scraper_search(request):
    if len(request.GET.keys()):
        for k in request.GET.keys():
            print("%s='%s'" % (k, request.GET[k]))
    return render(request, 'kodi/scraper_search.html', {"foo": "bar"}, content_type="application/xhtml+xml")

def scraper_detail(request):
    if len(request.GET.keys()):
        for k in request.GET.keys():
            print("%s='%s'" % (k, request.GET[k]))
    return render(request, 'kodi/scraper_detail.html', {"foo": "bar"}, content_type="application/xhtml+xml")