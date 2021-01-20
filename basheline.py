#!/usr/bin/env python3

import argparse
import csv
import sys
import re
import os

input_csv_header = ['Localizacion', 'Título Original', 'Titulo traducido', 'Director', 'Año', 'Resolución', 'Formato']
output_csv_header = ['storage_name', 'title', 'title_preferred', 'director', 'year', 'resolution', 'media_format', 'path', 'storage_type', 'version', 'tags']

def parse_arguments(args):
    parser = argparse.ArgumentParser(description='Bas[h]eline. Because even IMDB needs some lube ^_^')
    parser.add_argument("-i", "--input", nargs='+', required=True, help="Input TXT and CSV files. The files that are going to be processed")
    parser.add_argument("-o", "--outputcsv", nargs='+', required=True, help="Output CSV. Sanitised CSV File that is going to be generated")
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

class rawFilesParser:
    VALID_EXTENSIONS = ['avi', 'mkv', 'mp4', 'm4v', 'm2ts', 'mts', 'iso', 'm4a']
    GARBAGE_TITLES = ['Title', 'Título Original', 'Miss Congeniality 4']
    USEFUL_FIELDS = ['title', 'title_preferred', 'director', 'year', 'resolution', 'media_format', 'storage_type', 'storage_name', 'tags', 'version', 'path', 'subpath',
    'filename']

    def discardGarbageTitles(self, movie):
        title = movie['title']
        if any(bad_title.lower() == title.lower() for bad_title in rawFilesParser.GARBAGE_TITLES):
            movie['ignored'] = True

    def add_tag(self, movie, tag):
        if not 'tags' in movie or movie['tags'] == '':
            movie['tags'] = tag
        else:
            movie['tags'] = movie['tags'] + ',' + tag

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
        for row in self.raw_csv:
            rawText = str(row)
            self.translateHeaders(row)
            self.set_subpath_as_tag(row)
            self.process_altTitle(row)
            movie = {}
            movie['rawText'] = rawText
            movie['ignored'] = False
            for field in self.USEFUL_FIELDS:
                if field in row: movie[field] = row[field]
            self.discardGarbageTitles(movie)
            if not movie['ignored']:
                self.movies[rawText] = movie

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
            if not movie['ignored']: self.processMovie (movie)
            if not movie['ignored']: self.movies[txtline] = movie

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
        if extension and not any(validExtension.lower() == extension.lower() for validExtension in rawFilesParser.VALID_EXTENSIONS):
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

    def processMovie(self, movie):
        if not movie['ignored']: self.splitPath(movie)
        if not movie['ignored']: self.processPath(movie)
        if not movie['ignored']: self.splitFilename(movie)
        if not movie['ignored']: self.getDirectorAndYears(movie)
        if not movie['ignored']: self.getResolution(movie)
        if not movie['ignored']: self.getMediaFormat(movie)
        if not movie['ignored']: self.getTitles(movie)
        if not movie['ignored']: self.process_altTitle(movie)
        if not movie['ignored']: self.discardGarbageTitles(movie)

class csvCleaner:
    def process(self, row):
        self.row = row
        self.process_007Films()
        self.process_AlienFilms()
        self.process_HarryPotterFilms()
        self.process_StarWarsFilms()
        self.set_additionalyears_as_tag()
        self.fix_years()
        self.fix_titles()
        return self.row

    def add_tag(self, tag):
        if self.row['tags'] == '':
            self.row['tags'] = tag
        else:
            tags = self.row['tags']
            self.row['tags'] = tags + ',' + tag

    def process_007Films(self):
        film007 = self.process_007Films.regex.match(self.row['title'])
        if film007:
            prefix = film007.group(1)
            trimmed_title = film007.group(2)
            self.add_tag(prefix)
            self.row['title'] = trimmed_title
    process_007Films.regex = re.compile(r'(007\. [0-9]{2}\.) (.*)')                         # 007. XX. Title

    def set_additionalyears_as_tag (self):
        severalyears = self.set_additionalyears_as_tag.regex.match(self.row['year'])
        if severalyears:
            firstyear = severalyears.group(1)
            secondyear = severalyears.group(2)
            self.add_tag(secondyear)
            self.row['year'] =firstyear 
    set_additionalyears_as_tag.regex = re.compile(r'(\d{4}).*(\d{4})')                      # year.*year

    def process_AlienFilms(self):
        filmalien = self.process_AlienFilms.regex.match(self.row['title'])
        if filmalien:
            prefix = filmalien.group(1)
            trimmed_title = filmalien.group(2)
            self.add_tag(prefix)
            self.row['title'] = trimmed_title
    process_AlienFilms.regex = re.compile(r'(Alien [0-9])\. (.*)')                          # Alien XX. Title

    def process_HarryPotterFilms(self):
        filmharrypotter = self.process_HarryPotterFilms.regex.match(self.row['title'])
        if filmharrypotter:
            order = 'Harry Potter ' + filmharrypotter.group(2)
            trimmed_title = filmharrypotter.group(1) + filmharrypotter.group(3)
            self.add_tag(order)
            self.row['title'] = trimmed_title
    process_HarryPotterFilms.regex = re.compile(r'(Harry Potter )([A-Z]{1,4})\. (.*)')      # Harry Potter XX. Title

    def process_StarWarsFilms(self):
        filmstarwars = self.process_StarWarsFilms.regex.match(self.row['title'])
        if filmstarwars:
            order = 'Star Wars. ' + filmstarwars.group(1)
            trimmed_title = filmstarwars.group(2)
            self.add_tag(order)
            self.row['title'] = trimmed_title
    process_StarWarsFilms.regex = re.compile(r'(Episode [A-Z]{1,4})\. (.*)')                # Episode XXXX. Title

    def fix_years(self):
        affected_films = [['Bajarse al Moro', 1989],
                ['Cidade de Deus', 2002],
                ['Crime Wave', 1953],
                ['Ex Machina', 2014],
                ['Once', 2007],
                ['The Deadly Affair', 1967],
                ['Two Cars, One Night', 2003],
                ['Toy Story 3', 2010],
                ['Grounded', 2012],
                ['The Offence', 1973]]
        for affected_film in affected_films:
            if affected_film[0].lower() == self.row['title'].lower():
                self.row['year'] = affected_film[1]

    def fix_titles(self):
        # Wrong Titles
        films_with_wrong_titles= [["Startime 1x27 Incident at a Corner", "Startime Incident at a Corner"],
                ['The Snapper', 'Screen Two - The Snapper'],
                ['Kung fu', 'Kung Fu Hustle'],
                ['Birdman', 'Birdman or (The Unexpected Virtue of Ignorance)'],
                ['Huozhe', 'Huo Zhe'],
                ['Ak-Nyeo', 'Aknyeo'],
                ['Alien³', 'Alien 3'],
                ['Dracula', "Bram Stoker's Dracula"],
                ["Dark City. Director's cut", 'Dark City', "Director's cut"],
                ["Dark City. Theatrical's cut", 'Dark City', "Theatrical's cut"],
                # We need to change them because of the use of forbidden characters: ":" o "/"
                ['Silent Hill. Revelation 3D', 'Silent Hill: Revelation'],
                ['Face Off', 'Face/Off'],
                ['Dont Look Back', 'Bob Dylan: Dont Look Back'],
                ['V.H.S.', 'V/H/S'],
                ['50-50', '50/50'],
                ['Sin City. A Dame to Kill For', "Frank Miller's Sin City: A Dame to Kill For"],
                ['The Empire Strikes Back', 'Star Wars: Episode V - The Empire Strikes Back'],
                ['Return of the Jedi', 'Star Wars: Episode VI - Return of the Jedi'],
                ['The Last Jedi', 'Star Wars: Episode VIII - The Last Jedi'],
                ['The Phantom Menace', 'Star Wars: Episode I - The Phantom Menace'],
                ['Rogue One', 'Rogue One: A Star Wars Story'],
                ['Dark Phoenix', 'X-Men: Dark Phoenix'],
                # We need to use the "World-wide (English title)" instead of the "original title".
                ['Extraterrestre', 'Extraterrestrial'],
                ['Un cuento chino', 'Chinese Take-Out'],
                ['El bar', 'The Bar'],
                ['Dolor y gloria', 'Pain and Glory'],
                ['Amama', 'When a Tree Falls'],
                ['Smultronstället', 'Wild Strawberries'],
                ['Hwal', 'The Bow'],
                ['Oro', 'Gold'],
                ['Ils', 'Them'],
                ['Das Experiment', 'The Experiment'],
                ['Il traditore', 'The Traitor'],
                ["J'accuse", 'An Officer and a Spy'],
                ['Noruwei no mori', 'Norwegian Wood'],
                ['Ohayô', 'Good Morning'],
                ['Yao a yao yao dao waipo qiao', 'Shanghai Triad'],
                ['Ying', 'Shadow'],
                ['Ray', 'Paradise'],
                ['Zimna wojna', 'Cold War'],
                ['Kokuhaku', 'Confessions']]
        for affected_film in films_with_wrong_titles:
            if affected_film[0].lower() == self.row['title'].lower():
                self.row['title'] = affected_film[1]
                # If the title includes the version
                if len(affected_film) >= 3:
                    self.row['version'] = affected_film[2]

        # Wrong Directors
        affected_directors=[['Juan Antonio Bayona', 'J.A. Bayona'],
                ['Andrey Tarkovskiy', 'Andrei Tarkovsky'],
                ['Wong Kar Wai', 'Wong Kar-Wai'],
                ['Shion Sono', 'Sion Sono'],
                ['Jennifer Yuh', 'Jennifer Yuh Nelson'],
                ['Andrés Muschietti', 'Andy Muschietti'],
                ['Jaihong Juhn', 'Jai-hong Juhn'],
                ['Víctor González', 'Fernando Meirelles, Kátia Lund']]
        for affected_director in affected_directors:
            if affected_director[0].lower() == self.row['director'].lower():
                self.row['director'] = affected_director[1]

        # Wrong title and wrong director
        affected_movies=[['Lik Wong', 'Riki-Oh: The Story of Ricky', 'Ngai Choi Lam'],
                ['Wu xia', 'Dragon', 'Peter Ho-Sun Chan']]
        for affected_movie in affected_movies:
            if affected_movie[0].lower() == self.row['title'].lower():
                self.row['title'] = affected_movie[1]
                self.row['director'] = affected_movie[2]

        # Superman II (Richard Donner, 2006) -> Superman II (Richard Donner edition) (Richard Lester, 1980 y 2006)
        affected_film=['Superman II', '2006'] 
        if (affected_film[0].lower() == self.row['title'].lower()) and (self.row['year'] == affected_film[1]):
            self.row['title'] = 'Superman II'
            self.row['version'] = 'Richard Donner edition'
            self.row['year'] = '1980'
            self.add_tag('2006')
            self.row['director'] = 'Richard Lester'

def generate_file(rawMovies, fout, csv_quotechar, csv_delimiter):
    writer = csv.DictWriter(fout, fieldnames = output_csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    writer.writeheader()
    bashelineCleaner = csvCleaner()

    for film in rawMovies.movies:
        rawMovie = rawMovies.movies[film]
        movie = {}
        if 'title' in rawMovie:             movie['title'] = rawMovie['title']
        if 'storage_name' in rawMovie:      movie['storage_name'] = rawMovie['storage_name']
        if 'director' in rawMovie:          movie['director'] = rawMovie['director']
        if 'year' in rawMovie:              movie['year'] = rawMovie['year']
        if 'resolution' in rawMovie:        movie['resolution'] = rawMovie['resolution']
        if 'media_format' in rawMovie:      movie['media_format'] = rawMovie['media_format']
        if 'title_preferred' in rawMovie:   movie['title_preferred'] = rawMovie['title_preferred']
        if 'storage_type' in rawMovie:      movie['storage_type'] = rawMovie['storage_type']
        if 'version' in rawMovie:           movie['version'] = rawMovie['version']
        if 'tags' in rawMovie:              movie['tags'] = rawMovie['tags']
        #Tricky: OutputCSV considers 'path' as the absolute name
        if rawMovie['path'] == '':
            movie['path'] = rawMovie['filename']
        else:
            movie['path'] = rawMovie['path'] + '/' + rawMovie['filename']

        writer.writerow(
            bashelineCleaner.process(movie)
        )

def main(args):
    '''
    Input files:
         TXT Files contain bulk data in HDDs. Similar to: 'find /path > bulkFile.txt'
         CSV Files contain a custom list (physical media)
    '''
    input_files=args.input
    output_csvfile=args.outputcsv[0]
    input_csvfiles, input_txtfiles = validateFiles(input_files)

    csv_quotechar = '|'
    csv_delimiter = ';'

    rawMovies = rawFilesParser()
    rawMovies.readTXTFiles(input_txtfiles)
    rawMovies.processTXTFiles()

    rawMovies.readCSVFiles(input_csvfiles, csv_quotechar, csv_delimiter)
    rawMovies.processCSVFiles()

    with open(output_csvfile, 'w+', newline='') as output_csv:
        generate_file(rawMovies, output_csv, csv_quotechar, csv_delimiter)

if __name__ == '__main__':
    arguments = parse_arguments(sys.argv[1:])
    main(arguments)

