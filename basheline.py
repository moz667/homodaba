#!/usr/bin/env python3

import argparse
import csv
import sys
import re

csv_header = ['storage_name', 'title', 'title_preferred', 'director', 'year', 'resolution', 'media_format', 'path', 'storage_type', 'version', 'tags']
garbage_titles = ['Título Original', 'Miss Congeniality 4']


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

def add_tag(row,tag):
    tags = row['tags']
    if tags:
        row['tags'] = tags + ',' + tag
    else:
        row['tags'] = tag

def title_is_garbage(row):
    if any(bad_title.lower() == row['title'].lower() for bad_title in garbage_titles):
        return True
    return False


def add_storage_type(row):
    if row['storage_name']  == 'Original':
        row['storage_type'] = row['media_format'].lower()
    elif add_storage_type.regex.match( row['storage_name'] ):
        row['storage_type'] =  'hard-drive'
    return row
add_storage_type.regex = re.compile(r'HDD-Pelis-[0-9]{3}')

def set_subpath_as_tag(row):
    titlewithpath = set_subpath_as_tag.regex.match(row['title'])
    if titlewithpath:
        subpath = titlewithpath.group(1)
        trimmed_title = titlewithpath.group(2)
        add_tag(row,subpath)
        row['title'] = trimmed_title
    return row
set_subpath_as_tag.regex = re.compile(r'([^/]+)/(.*)')                                  # subpath/Title

def process_altTitle(row):
	title_fields=['title','title_preferred']
	for title in title_fields:
		alttitle_exist = process_altTitle.alttitle_regex.match(row[title])
		if alttitle_exist:
			trimmed_title = alttitle_exist.group(1)
			row[title] = trimmed_title
			alttitle = alttitle_exist.group(2)
			alttitle_is_a_version = process_altTitle.version_regex.search(alttitle)
			if alttitle_is_a_version:
				row['version'] = alttitle
			else:
				add_tag(row,alttitle)
	return row
process_altTitle.alttitle_regex = re.compile(r'([^\(]+) \(([^\)]+)\)')                  # Tile (Alt. Title)
process_altTitle.version_regex = re.compile(r'(edition|version|censor|cut)', re.IGNORECASE)

def process_007Films(row):
    film007 = process_007Films.regex.match(row['title'])
    if film007:
        prefix = film007.group(1)
        trimmed_title = film007.group(2)
        add_tag(row,prefix)
        row['title'] = trimmed_title
    return row
process_007Films.regex = re.compile(r'(007\. [0-9]{2}\.) (.*)')                         # 007. XX. Title

def set_additionalyears_as_tag (row):
    severalyears = set_additionalyears_as_tag.regex.match(row['year'])
    if severalyears:
        firstyear = severalyears.group(1)
        secondyear = severalyears.group(2)
        add_tag(row, secondyear)
        row['year'] =firstyear 
    return row
set_additionalyears_as_tag.regex = re.compile(r'(\d{4}).*(\d{4})')                      # year.*year

def process_AlienFilms(row):
    filmalien = process_AlienFilms.regex.match(row['title'])
    if filmalien:
        prefix = filmalien.group(1)
        trimmed_title = filmalien.group(2)
        add_tag(row,prefix)
        row['title'] = trimmed_title
    return row
process_AlienFilms.regex = re.compile(r'(Alien [0-9])\. (.*)')                          # Alien XX. Title

def process_HarryPotterFilms(row):
    filmharrypotter = process_HarryPotterFilms.regex.match(row['title'])
    if filmharrypotter:
        order = 'Harry Potter ' + filmharrypotter.group(2)
        trimmed_title = filmharrypotter.group(1) + filmharrypotter.group(3)
        add_tag(row, order)
        row['title'] = trimmed_title
    return row
process_HarryPotterFilms.regex = re.compile(r'(Harry Potter )([A-Z]{1,4})\. (.*)')      # Harry Potter XX. Title

def process_StarWarsFilms(row):
    filmstarwars = process_StarWarsFilms.regex.match(row['title'])
    if filmstarwars:
        order = 'Star Wars. ' + filmstarwars.group(1)
        trimmed_title = filmstarwars.group(2)
        add_tag(row, order)
        row['title'] = trimmed_title
    return row
process_StarWarsFilms.regex = re.compile(r'(Episode [A-Z]{1,4})\. (.*)')                # Episode XXXX. Title

def add_fake_path(row):
    if (not row['path']) and (row['storage_type'] ==  'hard-drive'):
        row['path'] = '/FakePath/' + row['title'] + ' - ' + row['title_preferred'] + ' (' + row['director'] + ', ' + row['year'] + ').' + row['media_format']
    return row

def generate_file(fin, fout, csv_quotechar, csv_delimiter):
    writer = csv.DictWriter(fout, fieldnames = csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    reader = csv.DictReader(fin, fieldnames = csv_header, delimiter=csv_delimiter, quotechar=csv_quotechar)
    writer.writeheader()

    for row in reader:
        if title_is_garbage(row):
            continue

        row = add_storage_type(row)

        row = set_subpath_as_tag(row)

        row = process_altTitle(row)

        row = process_007Films(row)

        row = process_AlienFilms(row)

        row = process_HarryPotterFilms(row)

        row = process_StarWarsFilms(row)

        row = set_additionalyears_as_tag (row)

        # Added it for testing but we don't really need it. 
        #row = add_fake_path(row)

        writer.writerow(row)

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

