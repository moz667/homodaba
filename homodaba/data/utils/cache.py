import codecs
import json
import pickle

from data.models import get_table_cache_objects, MAX_CACHE_KEY_SIZE
from .facade_model import FacadeCredit

from homodaba.settings import NO_CACHE, UPDATE_CACHE

TABLE_CACHE_OBJS = get_table_cache_objects()

def is_cache_key_valid(key):
    return key and len(key) <= MAX_CACHE_KEY_SIZE

def add_cache(key, value):
    if is_cache_key_valid(key) and value and (not NO_CACHE or UPDATE_CACHE):
        # Si no hemos buscado en la cache pero tenemos el forzado de actualizar
        # cache, tenemos que eliminar antes la cache existente
        if NO_CACHE and UPDATE_CACHE:
            delete_cache(key)
        
        TABLE_CACHE_OBJS.create(
            key=key,
            value=serialize(value)
        )

    return value

def delete_cache(key):
    if is_cache_key_valid(key):
        TABLE_CACHE_OBJS.filter(key=key).delete()

def get_cache(key):
    if not NO_CACHE and is_cache_key_valid(key):
        cache_data = TABLE_CACHE_OBJS.filter(key=key).all()

        if cache_data.count() > 0:
            if not UPDATE_CACHE and cache_data[0].is_alive:
                return unserialize(cache_data[0].value)
            else:
                delete_cache(key=key)
    
    return None

"""
TODO: funcion privada
"""
def serialize(obj):
    return codecs.encode(pickle.dumps(obj), "base64").decode()

"""
TODO: funcion privada
"""
def unserialize(str_obj):
    return pickle.loads(codecs.decode(str_obj.encode(), "base64"))

def cache_obj_str_to_json_str(str_obj):
    obj = unserialize(str_obj=str_obj)
    data = None
    if isinstance(obj, list):
        data = []
        for item in obj:
            data.append({k: v for k, v in item.__dict__.items() if isinstance(v, (str, int, float, bool, list, dict))})
    else:
        data = {k: v for k, v in obj.__dict__.items() if isinstance(v, (str, int, float, bool, list, dict))}

    return json.dumps(data, indent=4, sort_keys=True, default=str)
