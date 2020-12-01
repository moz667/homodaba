#!/usr/bin/env python3

import argparse
import csv
import sys
import re

csv_header = ['storage_name', 'title', 'title_preferred', 'director', 'year', 'resolution', 'media_format', 'path', 'storage_type', 'version', 'tags']


def parse_arguments(args):
    parser = argparse.ArgumentParser(description='Bas[h]eline. Because even IMDB needs some lube ^_^')
    parser.add_argument("-i", "--inputcsv", nargs='+', required=True, help="Input CSV. The CSV File that is going to be processed")
    parser.add_argument("-o", "--outputcsv", nargs='+', required=True, help="Output CSV. Sanitised CSV File that is going to be generated")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    return parser.parse_args()

def print_first_lines(csvfile, csv_quotechar, csv_delimiter):
    print ('\ncsvfile: ',csvfile)
    csv_reader = csv.DictReader(csvfile, fieldnames = csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    fieldnames = csv_reader.fieldnames
    print ('fields: ', fieldnames)
    i=0
    for row in csv_reader:
        i+=1
        if i>=10:
            break
        print ('Line %d: %s' % (i,row)  )

class BashelineCleaner:
    GARBAGE_TITLES = ['Título Original', 'Miss Congeniality 4']

    def process(self, row):
        self.row = row

        self.add_storage_type()
        self.set_subpath_as_tag()
        self.process_altTitle()
        self.process_007Films()
        self.process_AlienFilms()
        self.process_HarryPotterFilms()
        self.process_StarWarsFilms()
        self.set_additionalyears_as_tag()

        return self.row

    def add_tag(self, tag):
        tags = self.row['tags']
        if tags:
            self.row['tags'] = tags + ',' + tag
        else:
            self.row['tags'] = tag

    def is_procesable(self, row):
        if any(bad_title.lower() == row['title'].lower() for bad_title in BashelineCleaner.GARBAGE_TITLES):
            return False
        return True

    def add_storage_type(self):
        if self.row['storage_name']  == 'Original':
            self.row['storage_type'] = self.row['media_format'].lower()
        elif self.add_storage_type.regex.match( self.row['storage_name'] ):
            self.row['storage_type'] =  'hard-drive'
    add_storage_type.regex = re.compile(r'HDD-Pelis-[0-9]{3}')

    def set_subpath_as_tag(self):
        titlewithpath = self.set_subpath_as_tag.regex.match(self.row['title'])
        if titlewithpath:
            subpath = titlewithpath.group(1)
            trimmed_title = titlewithpath.group(2)
            self.add_tag(subpath)
            self.row['title'] = trimmed_title
    set_subpath_as_tag.regex = re.compile(r'([^/]+)/(.*)')                                  # subpath/Title

    def process_altTitle(self):
        title_fields=['title','title_preferred']
        for title in title_fields:
            alttitle_exist = process_altTitle.alttitle_regex.match(self.row[title])
            if alttitle_exist:
                trimmed_title = alttitle_exist.group(1)
                self.row[title] = trimmed_title
                alttitle = alttitle_exist.group(2)
                alttitle_is_a_version = process_altTitle.version_regex.search(alttitle)
                if alttitle_is_a_version:
                    self.row['version'] = alttitle
                else:
                    self.add_tag(alttitle)
    process_altTitle.alttitle_regex = re.compile(r'([^\(]+) \(([^\)]+)\)')                  # Tile (Alt. Title)
    process_altTitle.version_regex = re.compile(r'(edition|version|censor|cut)', re.IGNORECASE)

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

    """
    TODO: Borrar, no se usa
    def add_fake_path(self):
        if (not self.row['path']) and (self.row['storage_type'] ==  'hard-drive'):
            self.row['path'] = '/FakePath/' + self.row['title'] + ' - ' + self.row['title_preferred'] + ' (' + self.row['director'] + ', ' + self.row['year'] + ').' + self.row['media_format']
    """

def generate_file(fin, fout, csv_quotechar, csv_delimiter):
    writer = csv.DictWriter(fout, fieldnames = csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    reader = csv.DictReader(fin, fieldnames = csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    writer.writeheader()

    basheline_cleaner = BashelineCleaner()

    for row in reader:
        if basheline_cleaner.is_procesable(row):
            writer.writerow(
                basheline_cleaner.process(row)
            )

def main(args):
    input_csvfile=args.inputcsv[0]
    output_csvfile=args.outputcsv[0]

    csv_quotechar = '|'
    csv_delimiter = ';'

    with open(input_csvfile, 'r', newline='') as input_csv, open(output_csvfile, 'w+', newline='') as output_csv:
        generate_file(input_csv, output_csv, csv_quotechar, csv_delimiter)

    #with open(output_csvfile, 'r', newline='') as output_csv:
    #    print_first_lines(output_csv, csv_quotechar, csv_delimiter)


if __name__ == '__main__':
    arguments = parse_arguments(sys.argv[1:])
    main(arguments)

