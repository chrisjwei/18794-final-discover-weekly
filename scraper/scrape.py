import requests, pickle

class Genre(object):
    def __init__(self, name, genre_id, parent_genre_id):
        self.name = name
        self.genre_id = genre_id
        self.parent_genre_id = parent_genre_id
    def __repr__(self):
        return "Genre(%s, %s, %s)" % (self.name.encode('ascii', errors='backslashreplace'), self.genre_id, self.parent_genre_id)

class Track(object):
    def __init__(self, label, genre):
        self.label = label
        self.genre = genre


def fetch_genres(fetch_subgenres=False):
    r = requests.get("https://itunes.apple.com/WebObjects/MZStoreServices.woa/ws/genres")
    music_genres = r.json()["34"]["subgenres"]
    genres = {}
    for k,v in music_genres.items():
        if (fetch_subgenres and "subgenres" in v):
            for (k2,v2) in v["subgenres"].items():
                genres[k2] = Genre(v2["name"], k2, k)
        genres[k] = Genre(v["name"], k, None)
    return genres

def retrieve_song_details(song_id):
    r = requests.get("https://itunes.apple.com/lookup?id=%s" % song_id)
    results = r.json()
    if "results" in results:
        return results["results"][0]
    else:
        raise Exception("No such song exists for id=%s" % song_id)


def top_songs_genre(genre, limit=100):
    url = "https://itunes.apple.com/us/rss/topsongs/limit=%d/genre=%s/explicit=true/json" % (limit, genre.genre_id)
    r = requests.get(url)
    try:
        results = r.json()["feed"]["entry"]
    except:
        return []
    songs = []
    for result in results:
        print "parsing '%s'" % result["title"]["label"]
        '''
        song_id = result["id"]["attributes"]["im:id"]
        try:
            details = retrieve_song_details(song_id)
        except:
            print "could not find song in iTunes"
        '''
        songs.append(Track(result["title"]["label"], genre))

    return songs

def scrape_songs(limit_per_genre=100):
    genres = fetch_genres(True)
    print "Found %d genres" % len(genres)
    all_songs = []
    for genre_id,genre in genres.iteritems():
        print "Fetching genre '%s'" % genre.name
        songs = top_songs_genre(genre, limit_per_genre)
        print "...fetched %d songs" % len(songs)
        all_songs += songs
    print "Fetched %d songs in total" % len(all_songs)
    return all_songs

songs = scrape_songs()

