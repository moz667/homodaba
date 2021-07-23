from django.utils.text import slugify

import os, sys, re, json

from data.utils import Trace as trace

from ..utils import save_json, split_filename_parts

VIDEO_EXT = [
    'mp4', 'avi', 'mkv', 'wmv', 'iso', 'mpg', 'mpeg'
]

SUB_EXT = [
    'srt', 'sub', 'sup', 'idx'
]

AUDIO_EXT = [
    'ac3'
]

VALID_EXT = VIDEO_EXT + SUB_EXT + AUDIO_EXT

def slugify_directory(directory):
    return slugify(directory.replace("../", "_").replace("/", "-"))

def get_output_filename(filename, directory, output='.'):
    slug_directory = slugify_directory(directory)
    return os.path.join(output, '%s-%s' % (slug_directory, filename))

class JSONDirectoryScan(object):
    @staticmethod
    def is_valid_filegroup(filegroup):
        video_count = 0

        for f in filegroup:
            if 'ext' in f and f['ext'].lower() in VIDEO_EXT:
                video_count = video_count + 1
        
        # Para que sea valido tiene que existir SOLO un video
        return video_count == 1

    @staticmethod
    def populate_new_item(filegroup):
        new_item = {
            'fullname': None,
            'name': None,
            'ext': None,
            'subs': [],
            'audios': [],
        }

        for f in filegroup:
            ext_low = f['ext'].lower()

            if ext_low in SUB_EXT:
                new_item['subs'].append(f)
            elif ext_low in AUDIO_EXT:
                new_item['audios'].append(f)
            elif ext_low in VIDEO_EXT:
                new_item['fullname'] = f['fullname']
                new_item['name'] = f['name']
                new_item['ext'] = f['ext']
            else:
                raise NotImplementedError 

        return new_item

    @staticmethod
    def generate_json_files(directory, output='.'):
        files_clean = []

        files_no_extension = []
        files_invalid = []
        files_orphans_subs = []
        files_orphans_audios = []

        i = 0
        
        full_list = os.listdir(directory)
        full_list.sort()

        while i < len(full_list):
            cur_item = split_filename_parts(full_list[i])

            # Si empieza por . lo ignoramos:
            if cur_item['fullname'].startswith('.'):
                trace.debug("El archivo '%s' va a ser ignorado." % cur_item['fullname'])
                i = i + 1
                continue
            
            # Comprobamos que tiene extension...
            if not 'ext' in cur_item:
                trace.warning("El archivo '%s' no tiene extension." % cur_item['fullname'])
                files_no_extension.append(cur_item)
                i = i + 1
                continue
            
            # ...y que tenga una extension valida
            if not cur_item['ext'].lower() in VALID_EXT:
                trace.warning("El archivo '%s' no una extension valida." % cur_item['fullname'])
                files_invalid.append(cur_item)
                i = i + 1
                continue
            
            
            # Mientras que haya siguientes y los archivos se llamen igual que este 
            # hacemos una lista temporal con archivos que se llamen igual
            filegroup = [cur_item]
            
            i = i + 1
            
            while i < len(full_list):
                next_item = split_filename_parts(full_list[i])

                if not 'name' in next_item or next_item['name'] != cur_item['name']:
                    break
                
                filegroup.append(next_item)
                i = i + 1

            # Si no es valido el grupo de archivos, para cada uno lo añadimos 
            # a la lista que competa
            if not JSONDirectoryScan.is_valid_filegroup(filegroup):
                for f in filegroup:
                    if f['ext'].lower() in SUB_EXT:
                        trace.warning("El archivo '%s' es un subtitulo huerfano." % f['fullname'])
                        files_orphans_subs.append(f)
                    elif f['ext'].lower() in AUDIO_EXT:
                        trace.warning("El archivo '%s' es un audio huerfano." % f['fullname'])
                        files_orphans_audios.append(f)
                    else:
                        trace.warning("El archivo '%s' no tiene una extension valida o es un video con varias fuentes de video." % f['fullname'])
                        files_invalid.append(f)
            # Si es valido el grupo, construimos la estructura con el grupo de archivos
            else:
                files_clean.append(JSONDirectoryScan.populate_new_item(filegroup))

        json_files = JSONDirectoryScan.get_json_filenames(
            directory, output, 
            files_clean=files_clean, files_no_extension=files_no_extension, 
            files_invalid=files_invalid, files_orphans_subs=files_orphans_subs, 
            files_orphans_audios=files_orphans_audios
        )

        for jf in json_files:
            if os.path.exists(jf['filename']):
                os.remove(jf['filename'])

            if len(jf['obj']) > 0:
                save_json(jf['obj'], jf['filename'])
        
        return {
            'clean': files_clean,
            'no_extension': files_no_extension,
            'invalid': files_invalid,
            'orphans_subs': files_orphans_subs,
            'orphans_audios': files_orphans_audios,
        }

    @staticmethod
    def load_json_files(directory, output='.'):
        json_files = JSONDirectoryScan.get_json_filenames(
            directory, output
        )

        results =  {
            'clean': None,
            'no_extension': None,
            'invalid': None,
            'orphans_subs': None,
            'orphans_audios': None,
        }

        for jf in json_files:
            if jf['id'] in results:
                obj = None
                if os.path.exists(jf['filename']):
                    obj = json.load(open(jf['filename'], 'r', newline=''))
                results[jf['id']] = obj if not obj is None else []

        return results

    @staticmethod
    def get_json_filenames(directory, output='.', files_clean=None, 
        files_no_extension=None, files_invalid=None, files_orphans_subs=None, 
        files_orphans_audios=None):

        return [
            {
                'id': 'clean',
                'obj': files_clean, 
                'filename': get_output_filename('files_clean.json', directory, output)
            },
            {
                'id': 'no_extension',
                'obj': files_no_extension, 
                'filename': get_output_filename('files_no_extension.json', directory, output)
            },
            {
                'id': 'invalid',
                'obj': files_invalid, 
                'filename': get_output_filename('files_invalid.json', directory, output)
            },
            {
                'id': 'orphans_subs',
                'obj': files_orphans_subs, 
                'filename': get_output_filename('files_orphans_subs.json', directory, output)
            },
            {
                'id': 'orphans_audios',
                'obj': files_orphans_audios, 
                'filename': get_output_filename('files_orphans_audios.json', directory, output)
            },
        ]