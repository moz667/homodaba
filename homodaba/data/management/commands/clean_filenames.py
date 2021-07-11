from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from data.utils.imdbpy_facade import facade_search, get_imdb_movie

from datetime import datetime
import os, sys, re, json

from .utils import Trace as trace, save_json, split_filename_parts

verbosity = 0

HELP_TEXT = """
Buscador:

Para cada archivo...

1) Miramos si ya esta en el json, si es asi pasamos al siguiente
2) Si tiene 4 digitos numericos seguidos > 1950 y menor 2022 (current year + 1)
    - Tenemos un posible año
    - Quitamos todo el texto desde el año en adelante y hacemos strip de " " y "-" (Esto sera el titulo)
3) Si no tiene año, el titulo sera todo el texto del nombre quitando desde "[.*" y haciendo strip de " " y "-" (Esto sera el titulo)
4) Buscamos con el imdb el titulo
    4.a) Si tenemos un solo match de año y titulo lo damos por bueno creando una estrcutura tipo MiniMovie {imdb_id, title, year}
    4.b) Si tenemos varios matches:
        * Sacamos la info para que se pueda seleccionar cual es el bueno
        * Sacamos una opcion de no me convence ninguno, introducir imdb_id (manualmente buscamos en el imdb y pegamos el id)
            - Cogemos la peli por imdb_id y generamos un MiniMovie
5) Añadimos a una lista el nombre del archivo original y el nuevo generado del imdb

Una vez terminado todos los archivos generamos un json con los datos de la lista

Generador de script de renames (popper.sh):
1) Por cada item en el json generamos un mv con el archivo original y el nuevo nombre
"""

verbosity = 0

VIDEO_EXT = [
    'mp4', 'avi', 'mkv', 'wmv', 'iso'
]

SUB_EXT = [
    'srt', 'sub', 'sup', 'idx'
]

AUDIO_EXT = [
    'ac3'
]

VALID_EXT = VIDEO_EXT + SUB_EXT + AUDIO_EXT

class Command(BaseCommand):
    help = HELP_TEXT

    """
    Argumentos del comando:

    """
    def add_arguments(self, parser):
        parser.add_argument('--directory', nargs='+', type=str, help="""Directorio a chequear""")
        parser.add_argument('--output', nargs='+', type=str, help="""Directorio donde guardaremos los json generados""")
    
    def slugify_directory(self, directory):
        return slugify(directory.replace("../", "_").replace("/", "-"))

    def get_output_filename(self, filename, directory, output='.'):
        slug_directory = self.slugify_directory(directory)
        return os.path.join(output, '%s-%s' % (slug_directory, filename))

    def is_valid_filegroup(self, filegroup):
        video_count = 0

        for f in filegroup:
            if 'ext' in f and f['ext'].lower() in VIDEO_EXT:
                video_count = video_count + 1
        
        # Para que sea valido tiene que existir SOLO un video
        return video_count == 1

    def populate_new_item(self, filegroup):
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

    def generate_json_files(self, directory, output='.'):
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
            if not self.is_valid_filegroup(filegroup):
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
                files_clean.append(self.populate_new_item(filegroup))
        
        json_files = [
            {
                'obj': files_clean, 
                'filename': self.get_output_filename('files_clean.json', directory, output)
            },
            {
                'obj': files_no_extension, 
                'filename': self.get_output_filename('files_no_extension.json', directory, output)
            },
            {
                'obj': files_invalid, 
                'filename': self.get_output_filename('files_invalid.json', directory, output)
            },
            {
                'obj': files_orphans_subs, 
                'filename': self.get_output_filename('files_orphans_subs.json', directory, output)
            },
            {
                'obj': files_orphans_audios, 
                'filename': self.get_output_filename('files_orphans_audios.json', directory, output)
            },
        ]

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

    def process_files_no_extension(self, files, directory, output='.'):
        # Con los que no tienen extension por ahora no hacemos nada mas que 
        # sacarlos por pantalla
        trace.info("Se han encontrado %s archivos sin extension en el directorio '%s'." % (len(files), directory))
        debug_message = ""
        for f in files:
            debug_message = debug_message + ("\t'%s'\n" % f["fullname"])
        trace.debug("Estos archivos son:", debug_message)

    def process_files_invalid(self, files, directory, output='.'):
        # Con los que no son invalidos por ahora no hacemos nada mas que 
        # sacarlos por pantalla
        trace.info("Se han encontrado %s archivos invalidos en el directorio '%s'." % (len(files), directory))
        debug_message = ""
        for f in files:
            debug_message = debug_message + ("\t'%s'\n" % f["fullname"])
        trace.debug("Estos archivos son:", debug_message)
    
    def process_files_orphans_subs(self, files, directory, output='.'):
        slug_directory = self.slugify_directory(directory)
        
        sh_filename = self.get_output_filename('files_orphans_subs.sh', directory, output)
        sh_file = open(sh_filename, 'w', newline='')
        sh_file.write("#!/bin/sh\n")

        for f in files:
            # TODO: OJO!!! si el nombre tuviera " deberiamos escaparla de alguna forma!!!
            sh_file.write('mv "%s" "orphans/"\n' % f['fullname'])

    def process_files_orphans_audios(self, files, directory, output='.'):
        slug_directory = self.slugify_directory(directory)
        
        sh_filename = self.get_output_filename('files_orphans_audios.sh', directory, output)
        sh_file = open(sh_filename, 'w', newline='')
        sh_file.write("#!/bin/sh\n")

        for f in files:
            # TODO: OJO!!! si el nombre tuviera " deberiamos escaparla de alguna forma!!!
            sh_file.write('mv "%s" "orphans/"\n' % f['fullname'])

    def match_in_processeds(self, file, processeds):
        for p in processeds:
            if file['fullname'] == p['fullname']:
                return True
        
        return False

    def handle(self, *args, **options):
        if not 'directory' in options or not options['directory'] or len(options['directory']) == 0:
            self.print_help('manage.py', __name__)
            return
        directory = ' '.join(options['directory'])

        output = './'

        if 'output' in options and options['output']:
            output = ' '.join(options['output'])
        
        global verbosity
        if 'verbosity' in options and options['verbosity']:
            verbosity = options['verbosity']
        trace.set_verbosity(verbosity)

        files = self.generate_json_files(directory, output)

        if len(files["no_extension"]) > 0:
            self.process_files_no_extension(files["no_extension"], directory, output)
        if len(files["invalid"]) > 0:
            self.process_files_invalid(files["invalid"], directory, output)
        if len(files["orphans_subs"]) > 0:
            self.process_files_orphans_subs(files["orphans_subs"], directory, output)
        if len(files["orphans_audios"]) > 0:
            self.process_files_orphans_audios(files["orphans_audios"], directory, output)

        # TODO: mover a un metodo... por ahora lo hacemos aqui a pelo
        # self.process_files_clean(files["clean"], directory, output)

        processeds = []
        json_processeds_file = self.get_output_filename('processeds.json', directory, output)
        
        if os.path.exists(json_processeds_file):
            processeds = json.loads(open(json_processeds_file, 'r', newline=''))

        for f in files["clean"]:
            if self.match_in_processeds(f, processeds):
                continue
            
            cur_name = f['name']

            title = None
            year = None
            resolution = None
            
            # Buscamos el año
            possible_years = re.findall('\d+\d+\d+\d+', cur_name)
            for pos_year in reversed(possible_years):
                if int(pos_year) > 1930 and int(pos_year) <= datetime.now().year:
                    year = pos_year
            
            if year:
                cur_name = re.sub(year, "", cur_name)
                year = int(year)
            
            # Buscamos resoluciones
            possible_resolutions = re.findall('720p|1080p', cur_name)
            if len(possible_resolutions) == 1:
                resolution = possible_resolutions[0]
                cur_name = re.sub(resolution, "", cur_name)



            cur_name = re.sub(r"\[[a-zA-Z0-9\-\s\+\._]+\]", "", cur_name)

            cur_name = re.sub(r"(?![a-zA-ZÁÉÍÓÚáéíóú\s\.\,]).", "", cur_name)
            title = cur_name.strip()
            
            # print(f['name'])
            print(title)
            if year and title:
                facade_results = facade_search(title, year)
            elif not year:
                print("No tenemos año para la peli '%s'" % f['fullname'])
            else:
                print("No tenemos titulo para la peli '%s'" % f['fullname'])

            """
            print("cur_name: %s" % cur_name)
            print("title: %s" % title)
            print("year: %s" % year)
            print("resolution: %s" % resolution)
            
            print("")
            """

        """
        for cur_filename in full_list:
            print(cur_filename)
        """

        

"""
Buscador:

Para cada archivo...

1) Miramos si ya esta en el json, si es asi pasamos al siguiente
2) Si tiene 4 digitos numericos seguidos > 1950 y menor 2022 (current year + 1)
    - Tenemos un posible año
    - Quitamos todo el texto desde el año en adelante y hacemos strip de " " y "-" (Esto sera el titulo)
3) Si no tiene año, el titulo sera todo el texto del nombre quitando desde "[.*" y haciendo strip de " " y "-" (Esto sera el titulo)
4) Buscamos con el imdb el titulo
    4.a) Si tenemos un solo match de año y titulo lo damos por bueno creando una estrcutura tipo MiniMovie {imdb_id, title, year}
    4.b) Si tenemos varios matches:
        * Sacamos la info para que se pueda seleccionar cual es el bueno
        * Sacamos una opcion de no me convence ninguno, introducir imdb_id (manualmente buscamos en el imdb y pegamos el id)
            - Cogemos la peli por imdb_id y generamos un MiniMovie
5) Añadimos a una lista el nombre del archivo original y el nuevo generado del imdb

Una vez terminado todos los archivos generamos un json con los datos de la lista

Generador de script de renames (popper.sh):
1) Por cada item en el json generamos un mv con el archivo original y el nuevo nombre
"""