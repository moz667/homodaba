from django.core.management.base import BaseCommand, CommandError

from data.models import MovieStorageType
from data.utils import Trace as trace

from datetime import datetime
import csv, os, sys, re, json

from .utils import save_json, split_filename_parts

from .filesystem import clean_filename_for_samba_share, escape_single_quoute
from .filesystem.JSONDirectory import JSONDirectoryScan, get_output_filename
from .filesystem.FileProcessor import FileProcessor
from .filesystem.JSONDirectory import split_filename_parts, VIDEO_EXT, SUB_EXT, AUDIO_EXT

from data.models import Movie, Tag

HELP_TEXT = """
Ejemplo de fichero de configuracion (JSON):
[
    {
        "real_path": "/mnt/nfs/servidor/compartido",
        "smb_path": "smb://servidor/compartido",
        "type": "movie",
        "tag": "tag1"
    },
    {
        "real_path": "/mnt/nfs/servidor/compartido2",
        "smb_path": "smb://servidor/compartido2",
        "type": "movie"
    },
]
"""

class Command(BaseCommand):
    help = HELP_TEXT

    """
    Argumentos del comando:

    """
    def add_arguments(self, parser):
        parser.add_argument('--config', nargs='+', type=str, help="Fichero con la configuracion de scaneo (JSON).")
        parser.add_argument('--output', nargs='+', type=str, help="Fichero csv de salida (por defecto: ./scan-output.csv).")

        """
        parser.add_argument('--directory', nargs='+', type=str, help="Directorio a chequear")
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
        """

    def handle(self, *args, **options):
        if not 'config' in options or not options['config'] or len(options['config']) == 0:
            self.print_help('manage.py', __name__)
            return
        config_json_file = ' '.join(options['config'])

        config_directories = json.load(open(config_json_file, 'r', newline=''))

        output_csv_file = './scan-output.csv'

        if 'output' in options and options['output']:
            output_csv_file = ' '.join(options['output'])
        
        verbosity = options['verbosity']
        trace.set_verbosity(verbosity)

        output_csv_header = ['title', 'year', 'imdb_id', 'not_an_imdb_movie', 'path', 'storage_name', 'storage_type', 'media_format', 'tags']

        with open(output_csv_file, 'w+', newline='') as output_csv:
            writer = csv.DictWriter(output_csv, fieldnames = output_csv_header, delimiter=";", quotechar='"')
            writer.writeheader()

            for config_dir in config_directories:
                video_list = scan_all_videos(config_dir["real_path"])

                for video in video_list:
                    tags = ','.join(
                        [config_dir['tags'] if 'tags' in config_dir else '', 
                        video['tag'] if 'tag' in video else '']
                    )

                    tags = tags.strip(',')
                    
                    writer.writerow({
                        'title': video['title'],
                        'year': video['year'],
                        'imdb_id': video['imdb_id'],
                        'not_an_imdb_movie': 'False' if video['imdb_id'] else 'True',
                        'storage_name': config_dir['smb_path'],
                        'storage_type': MovieStorageType.ST_NET_SHARE,
                        'media_format': calculate_media_format(video),
                        'path': config_dir['smb_path'] + video['fullname'].replace(config_dir["real_path"], ""),
                        'tags': tags
                    })

        all_data_rows = []
        with open(output_csv_file, newline='') as output_csv:
            reader = csv.DictReader(output_csv, fieldnames = output_csv_header, delimiter=";", quotechar='"')
            for row in reader:
                if row['title'] != 'title':
                    all_data_rows.append(row)

        sorted_rows = sorted(all_data_rows, key=lambda row:(row['title']), reverse=False)
        sorted_rows = sorted(sorted_rows, key=lambda row:(row['year']), reverse=False)

        with open(output_csv_file, 'w', newline='') as output_csv:
            writer = csv.DictWriter(output_csv, fieldnames = output_csv_header, delimiter=";", quotechar='"')
            writer.writeheader()

            for row in sorted_rows:
                writer.writerow(row)

        
# TODO: Calcular el media_format
# 'mp4', 'avi', 'mkv', 'wmv', 'iso', 'mpg', 'mpeg'
def calculate_media_format(video_file):
    if video_file['ext'] == "mp4":
        return MovieStorageType.MF_MP4
    elif video_file['ext'] == "avi":
        return MovieStorageType.MF_AVI
    elif video_file['ext'] == "iso":
        return MovieStorageType.MF_ISO
    elif video_file['ext'] == "mkv":
        return MovieStorageType.MF_MKV
    else:
        return MovieStorageType.MF_UNKNOWN
    
def scan_all_videos(path, is_root=True, tag=None):
    all_video_files = []
    full_list = os.listdir(path)

    for file_item in full_list:
        if os.path.isdir(os.path.join(path, file_item)):
            all_video_files = all_video_files + scan_all_videos(
                os.path.join(path, file_item), 
                is_root=False, 
                tag=file_item if is_root else tag
            )
            continue
        
        cur_item = split_filename_parts(file_item)

        # Si empieza por . lo ignoramos:
        if cur_item['fullname'].startswith('.'):
            trace.warning("Ignoramos el archivo '%s/%s'." % (path, cur_item['fullname']))
            continue
        
        # Comprobamos que tiene extension...
        if not 'ext' in cur_item:
            trace.warning("El archivo '%s/%s' no tiene extension." % (path, cur_item['fullname']))
            continue
        
        # ...y que tenga una extension valida
        if not 'ext' in cur_item or not cur_item['ext'].lower() in VIDEO_EXT:
            if not 'ext' in cur_item or (not cur_item['ext'].lower() in SUB_EXT and not cur_item['ext'].lower() in AUDIO_EXT):
                trace.warning("El archivo '%s/%s' no una extension valida." % (path, cur_item['fullname']))
            continue
        
        # corregimos el fullname con el path:
        cur_item['fullname'] = '%s/%s' % (path, cur_item['fullname'])

        # OJO: Solo funciona con el formato sencillo siguiente:
        #  - "TITULO (AÑO) [ttIMDB_ID]", para los scrapeados del imdb
        #  - "TITULO (AÑO)", para los que no sean scrapeables en el imdb
        #  - "TITULO", para los que no sean scrapeables en el imdb y no sepamos año
        s = cur_item["name"]
        
        pattern = re.compile("(.*) \(([0-9]+)\) \[tt([0-9]+)\]")
        reg_search = pattern.search(s)

        if reg_search:
            cur_item["imdb_id"] = reg_search.group(3)
            cur_item["year"] = reg_search.group(2)
            cur_item["title"] = reg_search.group(1)
        else:
            pattern = re.compile("(.*) \(([0-9]+)\)")
            reg_search = pattern.search(s)

            if reg_search:
                cur_item["imdb_id"] = ""
                cur_item["year"] = reg_search.group(2)
                cur_item["title"] = reg_search.group(1)
            else:
                cur_item["imdb_id"] = ""
                cur_item["year"] = Movie.DEFAULT_NO_YEAR
                cur_item["title"] = s

                cur_item["tag"] = ','.join([tag, Tag.NO_YEAR]) if tag else Tag.NO_YEAR

        if 'title' in cur_item and 'year' in cur_item:
            if tag and not 'tag' in cur_item:
                cur_item["tag"] = tag
            
            all_video_files.append(cur_item)
        else:
            trace.warning("El archivo '%s/%s' no coincide con ningun patron de identificacion valido." % (path, cur_item['fullname']))
        # OJO: Solo funciona con el formato sencillo

    return all_video_files
