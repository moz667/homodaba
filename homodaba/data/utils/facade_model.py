from datetime import datetime

from data.models import Movie

SPANISH_LANGUAGE_COUNTRIES = [
    'Mexico', 'Colombia', 'Spain', 'Argentina',
    'Peru', 'Venezuela', 'Chile', 'Guatemala',
    'Ecuador', 'Bolivia', 'Cuba',
    'Dominican Republic', 'Honduras', 'Paraguay',
    'El Salvador', 'Nicaragua', 'Costa Rica',
    'Panama', 'Uruguay', 'Equatorial Guinea',
]

SPANISH_LANGUAGE_COUNTRIES_ISO_3166_1 = {
    'MX': 'Mexico', 'CO': 'Colombia', 'ES': 'Spain', 'AR': 'Argentina',
    'PE': 'Peru', 'VE': 'Venezuela', 'CL': 'Chile', 'GT': 'Guatemala',
    'EC': 'Ecuador', 'BO': 'Bolivia', 'CU': 'Cuba', 'DO': 'Dominican Republic',
    'HN': 'Honduras', 'PY': 'Paraguay', 'SV': 'El Salvador', 'NI': 'Nicaragua',
    'CR': 'Costa Rica', 'PA': 'Panama', 'UY': 'Uruguay', 'GQ': 'Equatorial Guinea'
}

class FacadeCredit:
    id = None
    name = None
    canonical_name = None
    avatar_url = None
    avatar_thumbnail_url = None

class FacadeMovie:
    title = None
    title_original = None
    title_preferred = None
    imdb_id = None
    tmdb_id = None
    kind = Movie.MK_MOVIE
    summary = None
    poster_url = None
    poster_thumbnail_url = None
    year = None
    rating = None
    title_akas = {}
    tags = []
    genres = []
    content_rating_systems = []
    directors = []
    writers = []
    actors = []
    countries = []

    # tmdb_fields
    release_date = None

    def __init__(self):
        self.title = None
        self.title_original = None
        self.title_preferred = None
        self.imdb_id = None
        self.tmdb_id = None
        self.kind = Movie.MK_MOVIE
        self.summary = None
        self.poster_url = None
        self.poster_thumbnail_url = None
        self.year = None
        self.rating = None
        self.title_akas = {}
        self.tags = []
        self.genres = []
        self.content_rating_systems = []
        self.directors = []
        self.writers = []
        self.actors = []
        self.countries = []

        # tmdb_fields
        self.release_date = None

    def populate_from_tmdb_movie(self, m):
        self.tmdb_id = m.id

        m_info = m.info()
        self.title = m_info['title']
        self.title_original = m.original_title
        
        alternative_titles = m.alternative_titles()

        if 'titles' in alternative_titles:
            # {'iso_3166_1': 'TH', 'title': 'X', 'type': ''}
            # type npi de para que se usa
            for at in alternative_titles['titles']:
                if at['iso_3166_1'] in SPANISH_LANGUAGE_COUNTRIES_ISO_3166_1 and at['iso_3166_1'] == 'ES' and (at['type'] == 'Castilian title' or at['type'] == ''):
                    self.title_preferred = at['title']

            if self.title_preferred is None and len(m.origin_country) == 1 \
                and m.origin_country[0] in SPANISH_LANGUAGE_COUNTRIES_ISO_3166_1:
                self.title_preferred = self.title_original

            if self.title_preferred is None:
                for at in alternative_titles['titles']:
                    if at['iso_3166_1'] in SPANISH_LANGUAGE_COUNTRIES_ISO_3166_1:
                        self.title_preferred = at['title']
            
            for at in alternative_titles['titles']:
                if not at['iso_3166_1'] in self.title_akas.keys():
                    self.title_akas[at['iso_3166_1']] = at['title']

        if self.title_preferred is None:
            self.title_preferred = self.title

        self.imdb_id = m_info['imdb_id'] if 'imdb_id' in m_info and m_info['imdb_id'] else None

        if self.imdb_id is None:
            self.kind = Movie.MK_NOT_AN_IMDB_MOVIE
        
        self.summary = m_info['overview'] if 'overview' in m_info else None

        # image sizes on tmdb: https://www.themoviedb.org/talk/53c11d4ec3a3684cf4006400
        self.poster_thumbnail_url = 'https://image.tmdb.org/t/p/w780%s' % m_info['poster_path'] if 'poster_path' in m_info else None
        self.poster_url = 'https://image.tmdb.org/t/p/original%s' % m_info['poster_path'] if 'poster_path' in m_info else None

        self.year = datetime.fromisoformat(m_info['release_date']).year
            
        self.rating = m_info['vote_average'] if 'vote_average' in m_info else None

        if 'belongs_to_collection' in m_info and m_info['belongs_to_collection']:
            self.tags.append(m_info['belongs_to_collection']['name'])
        
        if 'genres' in m_info and m_info['genres']:
            # {'id': 28, 'name': 'Action'}
            for g in m_info['genres']:
                self.genres.append(g['name'])

        # FIXME: tmdb no tiene crs para peliculas (curiosamente si lo tiene para series)
        # self.content_rating_systems

        m_credits = m.credits()

        if m_credits and 'crew' in m_credits:
            for p in m_credits['crew']:
                if p['job'] == 'Director':
                    self.directors.append(dictionary_to_facade_credit(p))
                elif p['job'] == 'Writer' or p['job'] == 'Novel' or p['job'] == 'Screenplay':
                    self.writers.append(dictionary_to_facade_credit(p))
        
        if m_credits and 'cast' in m_credits:
            for p in m_credits['cast']:
                self.actors.append(dictionary_to_facade_credit(p))
                if len(self.actors) > 11:
                    break

        self.countries = m.origin_country
    
def dictionary_to_facade_credit(p):
    # {'adult': False, 'gender': 2, 'id': 4671, 'known_for_department': 'Editing', 'name': 'Zach Staenberg', 'original_name': 'Zach Staenberg', 'popularity': 0.2352, 'profile_path': '/fTE4gvedUe9xJRAdKUnCM09TkwZ.jpg', 'credit_id': '52fe425bc3a36847f8018141', 'department': 'Editing', 'job': 'Editor'}
    # {'adult': False, 'gender': 2, 'id': 6384, 'known_for_department': 'Acting', 'name': 'Keanu Reeves', 'original_name': 'Keanu Reeves', 'popularity': 11.1443, 'profile_path': '/kEoUZKEG7dzbCESDjd0CKAN1r0n.jpg', 'cast_id': 34, 'character': 'Neo', 'credit_id': '52fe425bc3a36847f80181c1', 'order': 0}
    fc = FacadeCredit()
    fc.id = 'tmdb:%s' % p['id']
    fc.name = p['name']
    fc.canonical_name = p['original_name']
    fc.avatar_thumbnail_url = 'https://image.tmdb.org/t/p/w780%s' % p['profile_path'] if 'profile_path' in p and p['profile_path'] else None
    fc.avatar_url = 'https://image.tmdb.org/t/p/original%s' % p['profile_path'] if 'profile_path' in p and p['profile_path'] else None

    return fc

def is_valid_tmdb_movie(m):
    if not m.id:
        return False
    
    m_info = m.info()

    if not m_info or not 'title' in m_info or not m_info['title'] \
        or not m.original_title or not 'release_date' in m_info \
        or not m_info['release_date']:
        return False
    
    return True