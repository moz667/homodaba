#!/usr/bin/env python3

import argparse
import csv
import sys
import re
import os
import json

input_csv_header = ['Localizacion', 'Título Original', 'Titulo traducido', 'Director', 'Año', 'Resolución', 'Formato']
output_csv_header = ['storage_name', 'title', 'title_preferred', 'director', 'year', 'resolution', 'media_format', 'path', 'storage_type', 'version', 'imdb_id', 'tags' ]

def parse_arguments(args):
    parser = argparse.ArgumentParser(description='Bas[h]eline. Because even IMDB needs some lube ^_^')
    parser.add_argument("-i", "--input", nargs='+', required=True, help="Input TXT and CSV files. The files that are going to be processed")
    parser.add_argument("-o", "--outputcsv", nargs='+', required=True, help="Output CSV. Sanitised CSV File that is going to be generated")
    parser.add_argument("-p", "--patchedfilms", nargs='+', required=False, help="[OPT] Input JSON. File containing film fields to correct")
    parser.add_argument("-m", "--imdbjson", nargs='+', required=False, help="[OPT] Input JSON. File mapping unaligned CSV titles with IMDB")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    return parser.parse_args()

def validateFiles(filenames):
    csvFiles = []
    txtFiles = []
    for file in filenames:
        base, ext = os.path.splitext(file)
        if ext.lower() == '.csv':
            csvFiles.append(file)
        elif ext.lower() == '.txt':
            txtFiles.append(file)
        else:
            raise argparse.ArgumentTypeError('File must have a csv or txt extension', file)
    return csvFiles, txtFiles

class filesParser:
    VALID_EXTENSIONS = ['avi', 'mkv', 'mp4', 'm4v', 'm2ts', 'mts', 'iso', 'm4a']
    GARBAGE_TITLES = ['Title', 'Título Original', 'Miss Congeniality 4']

    def gatherMovies(self, txtMovies, csvMovies):
        self.movies = {**txtMovies.movies, **csvMovies.movies}
        self.normalizeCSVFields()

    def normalizeCSVFields(self):
        for row in self.movies:
            originMovie = self.movies[row]
            #Tricky: HomoDaba considers the field 'path' as the absolute name
            if originMovie['path'] == '':
                originMovie['path'] = originMovie['filename']
            else:
                originMovie['path'] = originMovie['path'] + '/' + originMovie['filename']
            movie = {}
            for field in output_csv_header:
                if field in originMovie: movie[field] = originMovie[field]
            self.movies[row] = movie

    def fixOriginErrors(self, file_json):
        base, ext = os.path.splitext(file_json)
        if ext.lower() != '.json':
            raise argparse.ArgumentTypeError('File must have a json extension', file_json)
        with open(file_json, 'r', newline='') as films_to_correct:
            moviespatch = json.load(films_to_correct)

        basheline_cleaner = csvCleaner(moviespatch, movieswithIMDB)
        for row in self.movies:
            movie = self.movies[row]
            basheline_cleaner.process(movie)
            self.movies[row] = movie

    def fixOriginErrors(self, *args):
        patchedTitles_json = args[0]
        if (len(args) == 2):
            titlesWithIMDBID_json = args[1]
        else:
            titlesWithIMDBID_json = None

        base, ext = os.path.splitext(patchedTitles_json)
        if ext.lower() != '.json':
            raise argparse.ArgumentTypeError('File must have a json extension', patchedTitles_json)
        with open(patchedTitles_json, 'r', newline='') as films_to_correct:
            moviespatch = json.load(films_to_correct)

        if titlesWithIMDBID_json is not None:
            base, ext = os.path.splitext(titlesWithIMDBID_json)
            if ext.lower() != '.json':
                raise argparse.ArgumentTypeError('File must have a json extension', titlesWithIMDBID_json)
            with open(titlesWithIMDBID_json, 'r', newline='') as films_w_imdb:
                movieswithIMDBID = json.load(films_w_imdb)
        else:
            movieswithIMDBID = {}

        basheline_cleaner = csvCleaner(moviespatch, movieswithIMDBID)
        for row in self.movies:
            movie = self.movies[row]
            basheline_cleaner.process(movie)
            self.movies[row] = movie


    def set_additionalyears_as_tag (self,movie):
        severalyears = self.set_additionalyears_as_tag.regex.match(movie['year'])
        if severalyears:
            firstyear = severalyears.group(1)
            secondyear = severalyears.group(2)
            self.add_tag(movie,secondyear)
            movie['year'] =firstyear 
    set_additionalyears_as_tag.regex = re.compile(r'(\d{4}).*(\d{4})')                      # year.*year

    def process_altTitle(self,movie):
        title_fields=['title','title_preferred']
        for title in title_fields:
            alttitle_exist = self.process_altTitle.alttitle_regex.match(movie[title])
            if alttitle_exist:
                trimmed_title = alttitle_exist.group(1)
                movie[title] = trimmed_title
                alttitle = alttitle_exist.group(2)
                alttitle_is_a_version = self.process_altTitle.version_regex.search(alttitle)
                if alttitle_is_a_version:
                    movie['version'] = alttitle
                else:
                    self.add_tag(movie, alttitle)
    process_altTitle.alttitle_regex = re.compile(r'(.*) \((.*)\)')                  # Tile (Alt. Title)
    process_altTitle.version_regex = re.compile(r'(edition|version|censor|cut)', re.IGNORECASE)

    def discardGarbageTitles(self, movie):
        title = movie['title']
        if any(bad_title.lower() == title.lower() for bad_title in filesParser.GARBAGE_TITLES):
            movie['ignored'] = True

    def add_tag(self, movie, tag):
        if not 'tags' in movie or movie['tags'] == '':
            movie['tags'] = tag
        else:
            movie['tags'] = movie['tags'] + ',' + tag

class csvFilesParser(filesParser):
    def __init__(self):
        super().__init__()

    def set_subpath_as_tag(self, row):
        titlewithpath = self.set_subpath_as_tag.regex.match(row['title'])
        if titlewithpath:
            subpath = titlewithpath.group(1)
            trimmed_title = titlewithpath.group(2)
            self.add_tag(row,subpath)
            row['title'] = trimmed_title
    set_subpath_as_tag.regex = re.compile(r'(.*)/(.*)')                                  # subpath/Title

    def readCSVFiles(self, input_csvfiles, csv_quotechar, csv_delimiter):
        raw_csv = []
        for csvfile in input_csvfiles:
            with open(csvfile, 'r', newline='') as input_csv:
                reader = csv.DictReader(input_csv, fieldnames = input_csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
                for row in reader:
                    raw_csv.append(row)
        self.raw_csv = raw_csv
        print ('CSV list length',len(self.raw_csv))

    def translateHeaders(self, row):
        row['title'] = row['Título Original']
        row['title_preferred'] = row['Titulo traducido']
        row['director'] = row['Director']
        row['year'] = row['Año']
        row['resolution'] = row['Resolución']
        row['media_format'] = row['Formato']
        row['storage_type'] = row['Formato'].lower()
        row['storage_name'] = row['Localizacion']
        row['path'] = ''
        row['filename'] = ''

    def processCSVFiles(self):
        self.movies = {}
        for row in self.raw_csv:
            rawText = str(row)
            self.translateHeaders(row)
            self.set_subpath_as_tag(row)
            self.process_altTitle(row)
            movie = {}
            movie['rawText'] = rawText
            movie['ignored'] = False
            movie['filename'] = row['filename']
            for field in output_csv_header:
                if field in row: movie[field] = row[field]
            self.discardGarbageTitles(movie)
            self.set_additionalyears_as_tag(movie)
            if not movie['ignored']:
                self.movies[rawText] = movie

class txtFilesParser(filesParser):
    def __init__(self):
        super().__init__()

    def readTXTFiles(self, input_txtfiles):
        raw_txt = []
        for txtfile in input_txtfiles:
            with open(txtfile, 'r', newline='') as input_txt:
                raw_txt += input_txt.readlines()
        self.raw_txt = raw_txt
        print ('TXT list length',len(self.raw_txt))

    def processTXTFiles(self):
        self.movies = {}
        for txtline in self.raw_txt:
            movie = {}
            movie['rawText'] = txtline
            movie['ignored'] = False
            if not movie['ignored']: self.processTXTMovie (movie)
            if not movie['ignored']: self.movies[txtline] = movie

    def processTXTMovie(self, movie):
        if not movie['ignored']: self.splitPath(movie)
        if not movie['ignored']: self.processPath(movie)
        if not movie['ignored']: self.splitFilename(movie)
        if not movie['ignored']: self.getDirectorAndYears(movie)
        if not movie['ignored']: self.getResolution(movie)
        if not movie['ignored']: self.getMediaFormat(movie)
        if not movie['ignored']: self.getTitles(movie)
        if not movie['ignored']: self.process_altTitle(movie)
        if not movie['ignored']: self.set_additionalyears_as_tag(movie)
        if not movie['ignored']: self.discardGarbageTitles(movie)

    def splitPath(self, movie):
        path,name = os.path.split(os.path.abspath(movie['rawText']))
        movie['filename'] = name.rstrip("\n")
        movie['path'] = path

    def processPath(self, movie):
        pathSplit = self.processPath.regex.match(movie['path'])
        if pathSplit:
            storage_name = pathSplit.group(1)
            definition = pathSplit.group(2)
            subpath = pathSplit.group(3)
            if definition == 'SD':
                isHD = False
            elif definition == 'HD':
                isHD = True
            else:
                raise TypeError("Couldn't identify if isHD/isSD for", movie['path'])
            if not subpath:
                subpath = ""
            movie['storage_name'] = storage_name
            movie['isHD'] = isHD
            self.add_tag(movie, subpath)
            movie['storage_type'] = 'hard-drive'
        else:
            movie['ignored'] = True
    processPath.regex = re.compile(r'/media/bpk/(HDD-Pelis-[0-9]{3})/([HS]D)(?:/(.*))?')

    def checkExtension(self,movie):
        extension = movie['extension']
        if extension and not any(validExtension.lower() == extension.lower() for validExtension in filesParser.VALID_EXTENSIONS):
            movie['ignored'] = True
        elif extension:
            movie['extension'] = extension.upper()
        else:
            movie['extension'] = ''

    def splitFilename(self, movie):
        nameSplit = self.splitFilename.splitTitle.match(movie['filename'])
        if nameSplit:
            movie['titles'] = nameSplit.group(1)
            movie['directorsAndYears'] = nameSplit.group(2)
            movie['resolution'] = nameSplit.group(3)
            movie['extension'] = nameSplit.group(4)
            typeAlt = nameSplit.group(5) # Some Files are named "XXXXX DVD" when a DVD is located in HD (WTF!)
            if typeAlt:
                movie['media_format'] = typeAlt
                movie['extension'] = ''
                movie['isHD'] = False
            else:
                movie['media_format'] = ''
                self.checkExtension(movie)
        else:
            movie['ignored'] = True
    splitFilename.splitTitle = re.compile(r'(.*) (\(.*, (?:[0-9]{4}(?: y [0-9]{4})?)\)) ?(720p|1080p|2160p|1080i|1080|2160)?(?:(?:\.([a-zA-Z0-9]*))| (DVD))?$', re.MULTILINE )

    def getDirectorAndYears(self, movie):
        directorYearsSplit = self.getDirectorAndYears.regex.match(movie['directorsAndYears'])
        if directorYearsSplit:
            movie['director'] = directorYearsSplit.group(1)
            movie['year'] = directorYearsSplit.group(2)
        else:
            raise TypeError("Unable to find Director, year within:", movie['directorsAndYears'])
    getDirectorAndYears.regex = re.compile(r'\((.*), ([0-9]{4}( y [0-9]{4})?)\)')

    def getResolution(self, movie):
        if not movie['resolution'] and movie['isHD'] and (movie['extension'] == '' or movie['extension'] == 'ISO')  :
            movie['resolution'] = "1080p"
        elif not movie['resolution']:
            movie['resolution'] = ''

    def getMediaFormat(self, movie):
        extension = movie['extension']
        if not movie['extension'] and movie['resolution'] == "1080p":
            movie['media_format'] = 'BLURAY'
        elif extension == 'ISO' and movie['resolution'] == "1080p":
            movie['media_format'] = 'BLURAY-ISO'
        elif not movie['extension'] and not movie['isHD']:
            movie['media_format'] = 'DVD'
        elif extension == 'ISO'  and not movie['isHD']:
            movie['media_format'] = 'DVD-ISO'
        elif not movie['extension'] and movie['resolution'] == "2160p":
            movie['media_format'] = 'ULTRA-BLURAY'
        elif extension == 'ISO'  and movie['resolution'] == "2160p":
            movie['media_format'] = 'ULTRA-BLURAY-ISO'
        else:
            movie['media_format'] = extension

    def getTitles(self, movie):
        if ' - ' in movie['titles']: # It has two titles: "Title - title_preferred"
            titles = self.getTitles.regex.match(movie['titles'])
            movie['title'] = titles.group(1)
            movie['title_preferred'] = titles.group(2)
        else: # It has one title
            movie['title'] = movie['titles']
            movie['title_preferred'] = ''
    getTitles.regex = re.compile(r'(.*)(?: - (.*))')

class csvCleaner(filesParser):
    def __init__(self, moviespatch, movieswithunmatchedtitles):
        self.patch = moviespatch
        self.unmatchedtitles = movieswithunmatchedtitles
        super().__init__()

    def process(self, row):
        self.row = row
        self.process_007Films()
        self.process_AlienFilms()
        self.process_HarryPotterFilms()
        self.process_StarWarsFilms()
        self.fix_movies()
        return self.row

    def process_007Films(self):
        film007 = self.process_007Films.regex.match(self.row['title'])
        if film007:
            trimmed_title = film007.group(1)
            self.row['title'] = trimmed_title
    process_007Films.regex = re.compile(r'007\. [0-9]{2}\. (.*)')                         # 007. XX. Title

    def process_AlienFilms(self):
        filmalien = self.process_AlienFilms.regex.match(self.row['title'])
        if filmalien:
            trimmed_title = filmalien.group(1)
            self.row['title'] = trimmed_title
    process_AlienFilms.regex = re.compile(r'Alien [0-9]\. (.*)')                          # Alien XX. Title

    def process_HarryPotterFilms(self):
        filmharrypotter = self.process_HarryPotterFilms.regex.match(self.row['title'])
        if filmharrypotter:
            trimmed_title = filmharrypotter.group(1) + filmharrypotter.group(2)
            self.row['title'] = trimmed_title
    process_HarryPotterFilms.regex = re.compile(r'(Harry Potter )[A-Z]{1,4}\. (.*)')      # Harry Potter XX. Title

    def process_StarWarsFilms(self):
        filmstarwars = self.process_StarWarsFilms.regex.match(self.row['title'])
        if filmstarwars:
            trimmed_title = filmstarwars.group(1)
            self.row['title'] = trimmed_title
    process_StarWarsFilms.regex = re.compile(r'Episode [A-Z]{1,4}\. (.*)')                # Episode XXXX. Title

    def fix_movies(self):
        # Movies patched manually
        for affected_film in self.patch:
            search = affected_film['search']
            replace = affected_film['replace']
            match = True
            for field in search:
                search_content = search[field]
                if not search_content.lower() == self.row[field].lower():
                    match = False
            if match:
                for field in replace:
                    replace_content = replace[field]
                    if field == 'tag':
                        self.add_tag(self.row,replace_content)
                    else:
                        self.row[field] = replace_content

        # Adding IMDB_ID to CSV -> Detected using csv_to_imdb
        imdb_id = ''
        matchAll = 0
        matchTitle = 0
        matchTitleAndYear = 0

        for affected_film in self.unmatchedtitles:
            searchCSV = affected_film['search']
            replace = affected_film['replace']


            search['director'] = searchCSV['director_csv']
            search['title'] = searchCSV['title_csv']
            if searchCSV['title_preferred_csv'] is not None:
                search['title_preferred'] = searchCSV['title_preferred_csv']
            search['year'] = searchCSV['year_csv']

            match = True
            for field in search:
                search_content = search[field]
                if not search_content.lower() == self.row[field].lower():
                    match = False
            if match and imdb_id == '':
                print ('IMDB:', replace['imdb_id'])
                self.row['imdb_id'] = replace['imdb_id']


def generate_file(movies, fout, csv_quotechar, csv_delimiter):
    writer = csv.DictWriter(fout, fieldnames = output_csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    writer.writeheader()

    for row in movies.movies:
        movie = movies.movies[row]
        writer.writerow(movie)

def main(args):
    '''
    Input files:
         TXT Files contain bulk data in HDDs. Similar to: 'find /path > bulkFile.txt'
         CSV Files contain a custom list (physical media)
    '''
    input_files=args.input
    output_csvfile=args.outputcsv[0]
    if args.patchedfilms is not None:
        films_to_correct=args.patchedfilms[0]
    else:
        films_to_correct = None

    if args.imdbjson is not None:
        films_to_add_imdbid=args.imdbjson[0]
    else:
        films_to_add_imdbid = None

    input_csvfiles, input_txtfiles = validateFiles(input_files)

    csv_quotechar = '|'
    csv_delimiter = ';'

    txtMovies = txtFilesParser()
    txtMovies.readTXTFiles(input_txtfiles)
    txtMovies.processTXTFiles()

    csvMovies = csvFilesParser()
    csvMovies.readCSVFiles(input_csvfiles, csv_quotechar, csv_delimiter)
    csvMovies.processCSVFiles()

    movies = filesParser()
    movies.gatherMovies(txtMovies, csvMovies)
    if films_to_correct and not films_to_add_imdbid:
        movies.fixOriginErrors(films_to_correct)
    if (films_to_correct and films_to_add_imdbid ):
        movies.fixOriginErrors(films_to_correct, films_to_add_imdbid)

    with open(output_csvfile, 'w+', newline='') as output_csv:
        generate_file(movies, output_csv, csv_quotechar, csv_delimiter)

if __name__ == '__main__':
    arguments = parse_arguments(sys.argv[1:])
    main(arguments)

