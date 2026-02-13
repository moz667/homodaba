
from data.management.commands.utils import save_json
from data.utils import Trace as trace
from data.utils.imdbpy_facade import get_facade_movie, match_facade_movie
from data.models import maybe_format_imdb_id

import getch

from datetime import datetime
import os, sys, re, json

from . import clean_filename_for_samba_share
from .JSONDirectory import get_output_filename

# kitty console:
# from data.utils.imdbpy_facade import show_imdb_movie_image

class FileProcessor(object):
    files = []

    not_interactive = False
    processeds = []
    processeds_filename = get_output_filename('processeds.json', '.', 'output/')

    ignoreds = []
    ignoreds_filename = get_output_filename('ignoreds.json', '.', 'output/')

    def __init__(self, files, directory='.', output='output/', not_interactive=False):
        super().__init__()

        self.files = files

        self.processeds = []
        self.processeds_filename = get_output_filename('processeds.json', directory, output)

        if os.path.exists(self.processeds_filename):
            self.processeds = json.load(open(self.processeds_filename, 'r', newline=''))

        self.ignoreds = []
        self.ignoreds_filename = get_output_filename('ignoreds.json', directory, output)

        if os.path.exists(self.ignoreds_filename):
            self.ignoreds = json.load(open(self.ignoreds_filename, 'r', newline=''))
        
        self.not_interactive = not_interactive

    def process(self):
        cur_file_index = 0

        for f in self.files:
            cur_file_index = cur_file_index + 1
            if self.match_in_processeds(f):
                continue
            
            self.populate_title_and_year(f)
            
            # print(f['name'])
            print("")
            print("## %s/%s : %s (%s) '%s' ##" % (
                cur_file_index, self.get_total_files(), 
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

    def validate(self):
        delete_processeds = []

        trace.debug(" * Validando procesados (Datos basicos)")
        for f in self.processeds:
            trace.debug(" - %s" % f['fullname'])
            if not 'imdb_id' in f and not 'tmdb_id' in f:
                trace.error("La pelicula '%s' no tiene imdb_id ni tmdb_id." % f['fullname'])
                return False

            facade_movie_params = {}

            if 'imdb_id' in f:
                facade_movie_params['imdb_id'] = f['imdb_id']
            
            if 'tmdb_id' in f:
                facade_movie_params['tmdb_id'] = f['tmdb_id']

            facade_movie = get_facade_movie(**facade_movie_params)

            if (not 'manual_valid' in f or not f['manual_valid']) and not facade_movie:
                print("")
                print("## Encontramos errores en '%s'" % f['fullname'])
                print("")
                if 'imdb_id' in f and f['imdb_id']:
                    print(" - Revise la url https://www.imdb.com/title/%s y si no coincide puede borrarla a continuacion." % maybe_format_imdb_id(f['imdb_id']))
                    print("")
                if 'tmdb_id' in f and f['tmdb_id']:
                    print(" - Revise la url https://www.themoviedb.org/movie/%s y si no coincide puede borrarla a continuacion." % f['tmdb_id'])
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
                if facade_movie:
                    f['imdb_title'] = facade_movie.title
                    f['imdb_year'] = facade_movie.year
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

        # Buscamos imdb_ids repetidos
        if self.search_repeated_imdb_ids():
            return False

        # No hace falta comprobar que ni fullname ni new_fullname estan repetidos, 
        # ya que al meterle el imdb_id al final no va a ocurrir.

        # Ultima comprobacion, uno a uno mostrar el viejo y el nuevo nombre asi 
        # como algo de info de imdb
        for f in self.processeds:
            if not 'last_validation' in f or not f['last_validation']:
                print("")
                print(" > '%s'" % f['fullname'])
                print(" > '%s'" % f['new_fullname'])
                print("   https://www.imdb.com/title/%s" % maybe_format_imdb_id(f['imdb_id']))

                if not self.not_interactive:
                    print(" * Es correcto? [Y/n]")
                    
                    selected_option = getch.getch()

                    if selected_option.lower() == 'n':
                        return False
                    
                    # TODO: Usar esta ultima validacion para generar el sh final
                    f['last_validation'] = True
                    self.save_processeds()
        
        return True

    def is_all_files_valid(self):
        # Comprobamos que ya todos estan validados manualmente o son una peli valida de imdb
        for f in self.processeds:
            if (not 'manual_valid' in f or not f['manual_valid']):
                if get_facade_movie(f['imdb_id']) is None:
                    return False
        
        return True

    def contains_repeated_imdb_ids(self):
        imdb_ids = []
        for f in self.processeds:
            if f['imdb_id'] in imdb_ids:
                return True
            
            imdb_ids.append(f['imdb_id'])

    def search_repeated_imdb_ids(self):
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
            
            print("")
            print("## Los siguientes archivos tienen el mismo imdb_id='%s':" % imdb_id)
            for rf in repeated_files:
                print("    - %s" % rf['fullname'])
            
            facade_movie = get_facade_movie(imdb_id=imdb_id)
            print(" * Los datos en imdb de la peli son %s (%s) [https://www.imdb.com/title/%s]:" % (
                facade_movie.title, facade_movie.year, maybe_format_imdb_id(imdb_id)
            ))

            if not self.not_interactive:
                print(" * Quieres borrar todos estos archivos de procesados? [y/N]")
                selected_option = getch.getch()

                if selected_option.lower() == 'y':
                    for item in repeated_files:
                        self.processeds.remove(item)
                    
                    self.save_processeds()
        
        return len(imdb_repeated_ids) > 0

    def save_processeds(self):
        save_json(self.processeds, self.processeds_filename)
        save_json(self.ignoreds, self.ignoreds_filename)

    def match_in_processeds(self, file):
        for p in self.processeds:
            if file['fullname'] == p['fullname']:
                return True

        for p in self.ignoreds:
            if file['fullname'] == p['fullname']:
                return True
        
        return False

    def populate_new_filenames(self, file):
        # El caso de ':' se usa un monton, por lo que lo reemplazamos por ';'
        # que parece que no se usa demasiado :P
        clean_imdb_title = re.sub(r'[:]', ';', file['imdb_title'])
        clean_imdb_title = clean_filename_for_samba_share(clean_imdb_title)

        new_name = "%s (%s) [%s].%s" % (
            clean_imdb_title, 
            file['imdb_year'],
            maybe_format_imdb_id(file['imdb_id']),
            file['ext']
        )

        file['new_fullname'] = new_name

        for extra_files in ['audios', 'subs']:
            if extra_files in file:
                for extra_file in file[extra_files]:
                    new_name = "%s (%s) [%s].%s" % (
                        clean_imdb_title, 
                        file['imdb_year'],
                        maybe_format_imdb_id(file['imdb_id']),
                        extra_file['ext']
                    )

                    extra_file['new_fullname'] = new_name

    def populate_title_and_year(self, file):
        cur_name = file['name']
        
        title = None
        year = None
        resolution = None
        
        # TODO: Deberiamos mejorar la busqueda de año pensando en la forma
        # que tiene bpk de definir los nombres de archivos:
        # Titulo (Director/es, año)

        # Buscamos el año
        possible_years = re.findall('\d+\d+\d+\d+', cur_name)
        for pos_year in reversed(possible_years):
            if int(pos_year) > 1930 and int(pos_year) <= datetime.now().year:
                year = pos_year
                break
        
        if year:
            # Muchas veces los nombres de las pelis vienen de la forma:
            #   Titulo (año) Varias tags y cosas que no nos interesan
            #   Titulo año Varias tags y cosas que no nos interesan
            # Es tan comun esta definicion, que resulta interesante
            # hacer estos replaces:
            #   s/(año).*//
            #   s/año.*//
            pattern = re.compile("\(%s\)" % year)

            if pattern.search(cur_name):
                new_cur_name = re.sub("\(%s\).*" % year, "", cur_name).strip()
                if len(new_cur_name) > 0:
                    cur_name = new_cur_name
            else:
                new_cur_name = re.sub("%s.*" % year, "", cur_name).strip()
                if len(new_cur_name) > 0:
                    cur_name = new_cur_name
                else:
                    cur_name = re.sub("%s" % year, "", cur_name)

            year = int(year)
        
        # Buscamos resoluciones
        possible_resolutions = re.findall('720p|1080p|480p|1080i', cur_name)
        if len(possible_resolutions) == 1:
            resolution = possible_resolutions[0]
            cur_name = re.sub(resolution, "", cur_name)

        cur_name = cur_name.strip()

        cur_name = cur_name.lower()

        # Quitamos terminos cacosos que contienen un punto
        for s in "elitetorrent.net EspaTaquilla.com www.zonatorrent.com www.lokotorrents.com".lower().split():
            cur_name = cur_name.replace(s, " ")

        # Limpiamos todo lo que no sean letras, numeros o . y ,
        cur_name = re.sub(r"(?![0-9a-zA-ZÁÉÍÓÚáéíóúñ\s\,]).", " ", cur_name)

        # Quitamos terminos cacosos de descripciones que meten a los archivos
        # [DVDRip][Xvid][Castellano][EspaTaquilla.com]
        for s in "BluRay 720p Hi10 x264 Dual Subs triaudio hdtv español HDTeam hdrip xvid ac3 hdrip gnio DVDRip castellano spanish divx".lower().split():
            cur_name = cur_name.replace(s, " ")

        cur_name = re.sub(r"\[[a-zA-Z0-9\-\s\+\._]+\]", "", cur_name)
        cur_name = re.sub(r"-|_|\.", " ", cur_name)
        cur_name = re.sub(r"(?![0-9a-zA-ZÁÉÍÓÚáéíóúñ\s\.\,]).", "", cur_name)

        title = cur_name.split()
        title = ' '.join(title)

        file['year'] = year
        file['title'] = title

        return title, year

    def get_total_files(self):
        return len(self.files)

    def match_file_as_facade_match(self, file):
        facade_match = None

        if file['title']:
            facade_match = match_facade_movie(
                file['title'], year=file['year'] if file['year'] else None
            )
        
        if facade_match:
            if facade_match.facade_movie:
                file['title'] = facade_match.facade_movie.title
                file['year'] = facade_match.facade_movie.year
                file['imdb_id'] = facade_match.facade_movie.imdb_id
            else:
                if not file['year']:
                    print(" * No tenemos año para la peli '%s' *" % file['fullname'])
                
                if not file['title']:
                    print(" * No tenemos titulo para la peli '%s' *" % file['fullname'])
                else:
                    print(" * No encontramos coincidencia clara para la peli '%s' *" % file['fullname'])

                    if len(facade_match.promissing_facade_movies) > 0:
                        print(" * Aunque hemos encontrado las siguientes: *")
                        for facade_movie in facade_match.promissing_facade_movies:
                            print(" - %s (%s) [%s] https://www.imdb.com/title/%s" % (
                                facade_movie.title, facade_movie.year, facade_movie.imdb_id, facade_movie.imdb_id
                            ))

        return facade_match

    def process_file(self, file):
        facade_match = self.match_file_as_facade_match(file)

        if facade_match.facade_movie:
            self.processeds.append(file)
            return True

        if self.not_interactive:
            return False

        print("")
        if facade_match and len(facade_match.promissing_facade_movies) > 0:
            if len(facade_match.promissing_facade_movies) == 1:
                sr = facade_match.promissing_facade_movies[0]
                print(" 0. Selecciona '%s (%s) [%s]'  https://www.imdb.com/title/%s" % (sr.title, sr.year, sr.imdb_id, sr.imdb_id))
            else:
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

        if selected_option == "0" and facade_match and len(facade_match.promissing_facade_movies) > 0:
            movie_index = 0

            if len(facade_match.promissing_facade_movies) > 1:
                i = 0
                for sr in facade_match.promissing_facade_movies:
                    print(" %s.- %s (%s) [%s] https://www.imdb.com/title/%s" % (i, sr.title, sr.year, sr.imdb_id, sr.imdb_id))
                    i = i + 1
                movie_index = input('Introduce el indice:')
                

            imdb_id = facade_match.promissing_facade_movies[int(movie_index)].imdb_id
            tmdb_id = facade_match.promissing_facade_movies[int(movie_index)].tmdb_id

            facade_movie = facade_match.promissing_facade_movies[int(movie_index)]

            file['title'] = facade_movie.title
            file['year'] = facade_movie.year
            file['imdb_id'] = facade_movie.imdb_id
            file['tmdb_id'] = facade_movie.tmdb_id

            self.processeds.append(file)
            return True
        elif selected_option == "1":
            kargs = {}
            imdb_id = input('Introduce el imdb_id: ')
            tmdb_id = None

            if imdb_id:
                kargs['imdb_id'] = maybe_format_imdb_id(imdb_id)
            else:
                tmdb_id = input('Introduce el tmdb_id: ')
                if tmdb_id:
                    kargs['tmdb_id'] = tmdb_id

            if len(kargs) > 0:
                facade_movie = get_facade_movie(**kargs)

                if not facade_movie is None:
                    file['title'] = facade_movie.title
                    file['year'] = facade_movie.year
                    file['imdb_id'] = imdb_id
                    file['tmdb_id'] = tmdb_id

                    self.processeds.append(file)
                    return True
        
            trace.error("No hemos encontrado la peli por imdb_id='%s' ni por tmdb_id='%s" % (imdb_id, tmdb_id))
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
