from django.core.management.base import BaseCommand, CommandError

from data.utils import Trace as trace
from data.utils.imdbpy_facade import search_movie_imdb, get_imdb_movie, match_imdb_movie, search_imdb_movies, is_valid_imdb_movie

import getch

from datetime import datetime
import os, sys, re, json

from .utils import save_json, split_filename_parts

from .filesystem import clean_filename_for_samba_share, escape_single_quoute
from .filesystem.JSONDirectory import JSONDirectoryScan, get_output_filename

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

    def match_in_processeds(self, file):
        for p in self.processeds:
            if file['fullname'] == p['fullname']:
                return True

        for p in self.ignoreds:
            if file['fullname'] == p['fullname']:
                return True
        
        return False
    
    def save_processeds(self):
        save_json(self.processeds, self.processeds_filename)
        save_json(self.ignoreds, self.ignoreds_filename)

    # TODO: Esto lo tendriamos que mover a utils de imdb
    def match_posible_movies(self, search_results, year=None, trace_message=True):
        posible_movies = []

        if year:
            for sr in search_results:
                if 'year' in sr and 'title' in sr and 'kind' in sr and sr['kind'] == 'movie' and int(year) == int(sr['year']):
                    posible_movies.append(sr)


        for sr in search_results:
            if 'year' in sr and 'title' in sr and 'kind' in sr and sr['kind'] == 'movie' and not sr in posible_movies:
                posible_movies.append(sr)
        
        if trace_message:
            if len(posible_movies) > 0:
                print(" * Aunque hemos encontrado las siguientes: *")
                for sr in posible_movies:
                    print(" - %s (%s) [%s] https://www.imdb.com/title/tt%s" % (sr['title'], sr['year'], sr.movieID, sr.movieID))
        
        return posible_movies

    def match_file_as_imdb_movie(self, file):
        imdb_movie = None
        posible_movies = []

        if file['year'] and file['title']:
            search_results = search_movie_imdb(file['title'], file['year'])

            if search_results == None or len(search_results) == 0:
                print(" * No encontramos coincidencias para la peli '%s' *" % file['fullname'])
            else:
                # TODO: Revisar... esta haciendo mal el match
                imdb_movie = match_imdb_movie(search_results, file['title'], file['year'])

                if imdb_movie and is_valid_imdb_movie(imdb_movie):
                    file['title'] = imdb_movie['title']
                    file['year'] = imdb_movie['year']
                    file['imdb_id'] = imdb_movie.getID()
                else:
                    imdb_movie = None
                    posible_movies = self.match_posible_movies(search_results, year=file['year'], trace_message=False)

        if imdb_movie is None:
            if not file['year']:
                print(" * No tenemos año para la peli '%s' *" % file['fullname'])
            
            if not file['title']:
                print(" * No tenemos titulo para la peli '%s' *" % file['fullname'])
            else:
                search_results = search_imdb_movies(file['title'])

                if not search_results is None and len(search_results) > 0:
                    print("")
                    print(" * No encontramos coincidencia clara para la peli '%s' *" % file['fullname'])
                    posible_movies = self.match_posible_movies(search_results, year=file['year'])

        return imdb_movie, posible_movies

    def process_file(self, file, query_file=True):
        imdb_movie = None
        posible_movies = []

        if query_file:
            imdb_movie, posible_movies = self.match_file_as_imdb_movie(file)

            if not imdb_movie is None:
                self.processeds.append(file)
                return True

        if self.not_interactive:
            return False

        print("")
        if len(posible_movies) == 1:
            sr = posible_movies[0]
            print(" 0. Selecciona '%s (%s) [%s]'" % (sr['title'], sr['year'], sr.movieID))
        elif len(posible_movies) > 0:
            print(" 0. Selecciona una de las pelis encontradas")
        print(" 1. Introducir imdb_id")
        print(" 2. Introducir/Cambiar titulo (año)")
        print(" 3. Introducir/Cambiar año")
        print(" 4. Introducir/Cambiar titulo")
        print(" 5. Mostrar informacion de la peli actual")
        print(" 6. Ignorar")
        print(" ?. Volver a procesar")
        print("")
        print(" X. Guardar y Salir")
        print("")
        print("")
        print('Introduce una opcion:')

        # getch coge solo un caracter, esta guay para evitarnos un intro
        selected_option = getch.getch()
        print("")

        if selected_option == "0":
            movie_index = 0

            if len(posible_movies) > 1:
                i = 0
                for sr in posible_movies:
                    print(" %s.- %s (%s) [%s] https://www.imdb.com/title/tt%s" % (i, sr['title'], sr['year'], sr.movieID, sr.movieID))
                    i = i + 1
                movie_index = input('Introduce el indice:')
                

            imdb_id = posible_movies[int(movie_index)].movieID
            imdb_movie = get_imdb_movie(imdb_id)

            if not imdb_movie is None:
                file['title'] = imdb_movie['title']
                file['year'] = imdb_movie['year']
                file['imdb_id'] = imdb_id

                self.processeds.append(file)
                return True

            trace.error("No hemos encontrado la peli por el imdb_id='%s'" % imdb_id)
            return False
        elif selected_option == "1":
            imdb_id = input('Introduce el imdb_id: ')

            imdb_id = re.sub(r'^tt', '', imdb_id)
            
            if imdb_id.isdigit():
                imdb_movie = get_imdb_movie(imdb_id)

                if not imdb_movie is None:
                    file['title'] = imdb_movie['title']
                    file['year'] = imdb_movie['year']
                    file['imdb_id'] = imdb_id

                    self.processeds.append(file)
                    return True
            
            trace.error("No hemos encontrado la peli por el imdb_id='%s'" % imdb_id)
            return False
        elif selected_option == "2":
            text = input('Introduce el titulo (año): ')

            year = text[text.find("(")+1:text.find(")")].strip()
            if year.isdigit():
                year = int(year)

            title = text[:text.find("(")].strip()

            file['title'] = title
            file['year'] = year

            return False
        elif selected_option == "3":
            year = input('Introduce el año:')

            file['year'] = int(year)
            return False
        elif selected_option == "4":
            title = input('Introduce el titulo:')

            file['title'] = title
            return False
        elif selected_option == "5":
            # print(file)
            print(" - fullname: '%s'" % file['fullname'])
            print(" - title: '%s'" % file['title'])
            print(" - year: '%s'" % file['year'])

            if 'imdb_id' in file:
                print(" - imdb_id: '%s'" % file['imdb_id'])
            return False
        elif selected_option == "6":
            print(" - Añadiendo '%s' a ignorados." % file['fullname'])
            self.ignoreds.append(file)
            return True
        elif str(selected_option).lower() == "x":
            self.save_processeds()
            exit(0)
        else:
            return False
    
    def populate_title_and_year(self, file):
        cur_name = file['name']

        title = None
        year = None
        resolution = None
        
        # Buscamos el año
        possible_years = re.findall('\d+\d+\d+\d+', cur_name)
        for pos_year in reversed(possible_years):
            if int(pos_year) > 1930 and int(pos_year) <= datetime.now().year:
                year = pos_year
                break
        
        if year:
            cur_name = re.sub("%s.*" % year, "", cur_name)
            year = int(year)
        
        # Buscamos resoluciones
        possible_resolutions = re.findall('720p|1080p', cur_name)
        if len(possible_resolutions) == 1:
            resolution = possible_resolutions[0]
            cur_name = re.sub(resolution, "", cur_name)

        cur_name = cur_name.strip()

        cur_name = cur_name.lower()

        for s in "BluRay 720p Hi10 x264 Dual Subs triaudio HDTeam".lower().split():
            cur_name = cur_name.replace(" %s" % s, " ")

        cur_name = re.sub(r"\[[a-zA-Z0-9\-\s\+\._]+\]", "", cur_name)
        cur_name = re.sub(r"-|_|\.", " ", cur_name)
        cur_name = re.sub(r"(?![0-9a-zA-ZÁÉÍÓÚáéíóúñ\s\.\,]).", "", cur_name)
        
        title = cur_name.split()
        title = ' '.join(title)

        # " BluRay 720p Hi10  x264 Dual Subs [HDTeam]"

        file['year'] = year
        file['title'] = title

        return title, year

    def populate_new_filenames(self, file):
        # El caso de ':' se usa un monton, por lo que lo reemplazamos por ';'
        # que parece que no se usa demasiado :P
        clean_imdb_title = re.sub(r'[:]', ';', file['imdb_title'])
        clean_imdb_title = clean_filename_for_samba_share(clean_imdb_title)

        new_name = "%s (%s) [tt%s].%s" % (
            clean_imdb_title, 
            file['imdb_year'],
            file['imdb_id'],
            file['ext']
        )

        file['new_fullname'] = new_name

        for extra_files in ['audios', 'subs']:
            if extra_files in file:
                for extra_file in file[extra_files]:
                    new_name = "%s (%s) [tt%s].%s" % (
                        clean_imdb_title, 
                        file['imdb_year'],
                        file['imdb_id'],
                        extra_file['ext']
                    )

                    extra_file['new_fullname'] = new_name

    def process_files_clean(self, files, directory, output='.'):
        self.processeds = []
        self.processeds_filename = get_output_filename('processeds.json', directory, output)

        if os.path.exists(self.processeds_filename):
            self.processeds = json.load(open(self.processeds_filename, 'r', newline=''))

        self.ignoreds = []
        self.ignoreds_filename = get_output_filename('ignoreds.json', directory, output)

        if os.path.exists(self.ignoreds_filename):
            self.ignoreds = json.load(open(self.ignoreds_filename, 'r', newline=''))

        total_files = len(files)
        cur_file_index = 0

        for f in files:
            cur_file_index = cur_file_index + 1
            if self.match_in_processeds(f):
                continue
            
            self.populate_title_and_year(f)
            
            # print(f['name'])
            print("")
            print("## %s/%s : %s (%s) '%s' ##" % (
                cur_file_index, total_files, 
                f['title'], f['year'] if not f['year'] is None else '', 
                f['fullname']))

            try:
                while not self.process_file(f):
                    if self.not_interactive:
                        break
            except:
                print("Error no esperado:", sys.exc_info()[0])
                self.save_processeds()
                raise
        
        self.save_processeds()

        delete_processeds = []

        trace.debug(" * Validando procesados (Datos basicos)")
        for f in self.processeds:
            trace.debug(" - %s" % f['fullname'])
            imdb_movie = get_imdb_movie(f['imdb_id'])

            if (not 'manual_valid' in f or not f['manual_valid']) and not is_valid_imdb_movie(imdb_movie):
                print("")
                print("## Encontramos errores en '%s'" % f['fullname'])
                print("")
                if not 'kind' in imdb_movie.keys():
                    print(" - No sabemos el tipo de peli para imdb_id='%s' fullname='%s'" % (f['imdb_id'], f['fullname']))
                elif imdb_movie['kind'] != 'movie':
                    print(" - El tipo de peli es '%s' para imdb_id='%s' fullname='%s'" % (imdb_movie['kind'], f['imdb_id'], f['fullname']))
                
                if not 'full-size cover url' in imdb_movie.keys() or not imdb_movie['full-size cover url']:
                    print(" - La peli no tiene portada. imdb_id='%s' fullname='%s'" % (f['imdb_id'], f['fullname']))
            
                print(" - Revise la url https://www.imdb.com/title/tt%s y si no coincide puede borrarla a continuacion." % f['imdb_id'])
                print("")

                if not self.not_interactive:
                    print(" * Desea BORRAR la peli '%s' de la lista de procesados? [Y/n]: " % f['fullname'])
                    selected_option = getch.getch()

                    if selected_option.lower() != 'n':
                        delete_processeds.append(f)
                        continue
                    else:
                        print("")
                        print(" * Desea VALIDAR la peli '%s' en la lista de procesados? (de esta forma no le volvera a preguntar) [Y/n]: " % f['fullname'])
                        selected_option = getch.getch()

                        if selected_option.lower() != 'n':
                            f['manual_valid'] = True

            if not 'imdb_title' in f:
                if imdb_movie:
                    f['imdb_title'] = imdb_movie['title']
                    f['imdb_year'] = imdb_movie['year']
                else:
                    trace.error("No encontramos peli en el imdb_id='%s' fullname='%s'" % (f['imdb_id'], f['fullname']))
                
            if 'imdb_title' in f:
                self.populate_new_filenames(f)
        
        if not self.not_interactive and len(delete_processeds) > 0:
            print("")
            print(" * Esta seguro que desea borrar %s items de la lista de procesados? [y/N]: " % len(delete_processeds))
            selected_option = getch.getch()

            if selected_option.lower() == 'y':
                for item in delete_processeds:
                    self.processeds.remove(item)
        
        self.save_processeds()

        # Comprobamos que ya todos estan validados manualmente o son una peli valida de imdb
        for f in self.processeds:
            if (not 'manual_valid' in f or not f['manual_valid']) and not is_valid_imdb_movie(imdb_movie):
                print(" * No podemos continuar mientras que te queden pelis sin validar ")
                exit()

        # Buscamos imdb_ids repetidos
        imdb_ids = []
        imdb_repeated_ids = {}
        new_fullnames = []
        for f in self.processeds:
            if f['imdb_id'] in imdb_ids:
                # print(" * El imdb_id '%s' esta repetido en otra peli" % f['imdb_id'])
                if not f['imdb_id'] in imdb_repeated_ids:
                    imdb_repeated_ids[f['imdb_id']] = 1    
                imdb_repeated_ids[f['imdb_id']] = imdb_repeated_ids[f['imdb_id']] + 1
            else:
                imdb_ids.append(str(f['imdb_id']))

                # Buscamos nombres repetidos (como tiene imdb_id deberian ser los 
                # mismos que los anteriores, al estar dentro del else: no deberia
                # salir ni uno)
                if f['new_fullname'] in new_fullnames:
                    print(" * El nuevo nombre '%s' esta repetido en otra peli" % f['new_fullname'])
                else:
                    new_fullnames.append(f['new_fullname'])
                
                for key in ['audios', 'subs']:
                    for item in f[key]:
                        if item['new_fullname'] in new_fullnames:
                            print(" * El nuevo nombre '%s' esta repetido en '%s' otra peli" % (item['new_fullname'], key))
                        else:
                            new_fullnames.append(f['new_fullname'])
        
        for imdb_id in imdb_repeated_ids.keys():
            repeated_files = []
            
            for f in self.processeds:
                if f['imdb_id'] == imdb_id:
                    repeated_files.append(f)
            
            print(" * Los siguientes archivos tienen el mismo imdb_id='%s':" % imdb_id)
            for rf in repeated_files:
                print("    - %s" % rf['fullname'])
            
            imdb_movie = get_imdb_movie(imdb_id)
            print(" * Los datos en imdb de la peli son %s (%s) [https://www.imdb.com/title/tt%s]:" % (imdb_movie['title'], imdb_movie['year'], imdb_id))

            if not self.not_interactive:
                print(" * Quieres borrar todos estos archivos de procesados? [y/N]")
                selected_option = getch.getch()

                if selected_option.lower() == 'y':
                    for item in repeated_files:
                        self.processeds.remove(item)
                    
                    self.save_processeds()

        if len(imdb_repeated_ids) > 0:
            print(" * No podemos continuar mientras que queden pelis con ids duplicados")
            exit()

        # No hace falta comprobar que ni fullname ni new_fullname estan repetidos, 
        # ya que al meterle el imdb_id al final no va a ocurrir.

        # Ultima comprobacion, uno a uno mostrar el viejo y el nuevo nombre asi 
        # como algo de info de imdb
        for f in self.processeds:
            if not 'last_validation' in f or not f['last_validation']:
                print("")
                print(" > '%s'" % f['fullname'])
                print(" > '%s'" % f['new_fullname'])
                print("   https://www.imdb.com/title/tt%s" % f['imdb_id'])

                if not self.not_interactive:
                    print(" * Es correcto? [Y/n]")
                    
                    selected_option = getch.getch()

                    if selected_option.lower() == 'n':
                        print(" * No podemos continuar, corrija el error manualmente.")
                        exit()
                    
                    # TODO: Usar esta ultima validacion para generar el sh final
                    f['last_validation'] = True
                    self.save_processeds()

        sh_filename = get_output_filename('move_processeds.sh', directory, output)
        sh_file = open(sh_filename, 'w', newline='')
        sh_file.write("#!/bin/sh\n")

        for f in self.processeds:
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