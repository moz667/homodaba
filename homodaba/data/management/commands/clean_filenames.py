from django.core.management.base import BaseCommand, CommandError

from data.utils import Trace as trace
from data.utils.imdbpy_facade import search_movie_imdb, get_imdb_movie, match_imdb_movie, search_imdb_movies, is_valid_imdb_movie

import getch

from datetime import datetime
import os, sys, re, json

from .utils import save_json, split_filename_parts

from .filesystem import clean_filename_for_samba_share, escape_single_quoute
from .filesystem.JSONDirectory import JSONDirectoryScan, get_output_filename
from .filesystem.FileProcessor import FileProcessor

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

class Command(BaseCommand):
    help = HELP_TEXT

    not_interactive = False
    processeds = []
    processeds_filename = ""
    ignoreds = []
    ignoreds_filename = ""

    """
    Argumentos del comando:

    """
    def add_arguments(self, parser):
        parser.add_argument('--directory', nargs='+', type=str, help="""Directorio a chequear""")
        parser.add_argument('--output', nargs='+', type=str, help="""Directorio donde guardaremos los json generados""")
        parser.add_argument(
            '--not-scan-directory',
            action='store_true',
            help='No scanea directorios y carga los json que tengamos en el --output.',
        )
        parser.add_argument(
            '--not-interactive',
            action='store_true',
            help='No hace ninguna pregunta (input) si encuentra errores, solo va pasando e intenta localizarlas solo.',
        )

    def generate_move_safe(self, filename, target_dir='orphans', target_filename=None):
        esc_filename = escape_single_quoute(filename)
        esc_target_filename = escape_single_quoute(target_filename) if not target_filename is None else esc_filename

        return ("if [ -e '%s/%s' ]; then\n" % (target_dir, esc_target_filename)) + \
            ("\techo 'ERROR: Ya existe %s en %s'\n" % (esc_target_filename, target_dir)) + \
            "else\n" + \
            ("\tmv -i -- '%s' '%s/%s'\n" % (esc_filename, target_dir, esc_target_filename)) + \
            "fi\n\n"

    def process_files_no_extension(self, files, directory, output='.'):
        # Con los que no tienen extension por ahora no hacemos nada mas que 
        # sacarlos por pantalla
        trace.info("Se han encontrado %s archivos/directorios sin extension en el directorio '%s'." % (len(files), directory))
        debug_message = ""
        for f in files:
            debug_message = debug_message + ("\t'%s'\n" % f["fullname"])
        trace.info("Estos archivos son:", debug_message)

    def process_files_invalid(self, files, directory, output='.'):
        # Con los que no son invalidos por ahora no hacemos nada mas que 
        # sacarlos por pantalla
        trace.info("Se han encontrado %s archivos invalidos en el directorio '%s'." % (len(files), directory))
        debug_message = ""
        for f in files:
            debug_message = debug_message + ("\t'%s'\n" % f["fullname"])
        trace.info("Estos archivos son:", debug_message)
    
    def process_files_orphans_subs(self, files, directory, output='.'):
        sh_filename = get_output_filename('files_orphans_subs.sh', directory, output)
        sh_file = open(sh_filename, 'w', newline='')
        sh_file.write("#!/bin/sh\n")

        for f in files:
            sh_file.write(self.generate_move_safe(f['fullname']))

    def process_files_orphans_audios(self, files, directory, output='.'):
        sh_filename = get_output_filename('files_orphans_audios.sh', directory, output)
        sh_file = open(sh_filename, 'w', newline='')
        sh_file.write("#!/bin/sh\n")

        for f in files:
            sh_file.write(self.generate_move_safe(f['fullname']))

    def process_files_clean(self, files, directory, output='.'):
        file_processor = FileProcessor(
            files=files,
            directory=directory,
            output=output,
            not_interactive=self.not_interactive
        )

        file_processor.process()

        if not file_processor.validate():
            print("")
            print("")
            if not file_processor.is_all_files_valid():
                print(" * No podemos continuar mientras que te queden pelis sin validar ")
            elif file_processor.contains_repeated_imdb_ids():
                print(" * No podemos continuar mientras que queden pelis con ids duplicados")
            else:
                print(" * No podemos continuar, corrija los archivos manualmente.")
            print("")
            exit()

        sh_filename = get_output_filename('move_processeds.sh', directory, output)
        sh_file = open(sh_filename, 'w', newline='')
        sh_file.write("#!/bin/sh\n")

        for f in file_processor.processeds:
            sh_file.write(self.generate_move_safe(f['fullname'], 'clean-name', f['new_fullname']))

            for extra_files in ['audios', 'subs']:
                if extra_files in f:
                    for extra_file in f[extra_files]:
                        sh_file.write(self.generate_move_safe(extra_file['fullname'], 'clean-name', extra_file['new_fullname']))

    def handle(self, *args, **options):
        if not 'directory' in options or not options['directory'] or len(options['directory']) == 0:
            self.print_help('manage.py', __name__)
            return
        directory = ' '.join(options['directory'])

        output = './'

        if 'output' in options and options['output']:
            output = ' '.join(options['output'])
        
        not_scan_directory = options['not_scan_directory']
        self.not_interactive = options['not_interactive']

        verbosity = options['verbosity']
        trace.set_verbosity(verbosity)

        files = {}

        if not_scan_directory:
            files = JSONDirectoryScan.load_json_files(directory, output)
        else:
            files = JSONDirectoryScan.generate_json_files(directory, output)

        if len(files["no_extension"]) > 0:
            self.process_files_no_extension(files["no_extension"], directory, output)
        if len(files["invalid"]) > 0:
            self.process_files_invalid(files["invalid"], directory, output)
        if len(files["orphans_subs"]) > 0:
            self.process_files_orphans_subs(files["orphans_subs"], directory, output)
        if len(files["orphans_audios"]) > 0:
            self.process_files_orphans_audios(files["orphans_audios"], directory, output)
        if len(files["clean"]) > 0:
            self.process_files_clean(files["clean"], directory, output)

        # TODO: Pintar estadisticas al final?




"""
search_results = search_imdb_movies('The Hobbit: An Unexpected Journey (2012)')

if not search_results is None and len(search_results) > 0:
    for sr in search_results:
        if 'year' in sr and 'title' in sr and 'kind' in sr and sr['kind'] == 'movie':
            imdb_movie = get_imdb_movie(sr.movieID)
            print(" - %s (%s) [%s] https://www.imdb.com/title/tt%s" % (sr['title'], sr['year'], sr.movieID, sr.movieID))
            # for k in imdb_movie.keys():
            #    print("    + '%s': '%s'" % (k, imdb_movie[k]))
"""