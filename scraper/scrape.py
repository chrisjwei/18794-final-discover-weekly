import requests, json, urllib, sqlite3, random, re, sys

'''
    TODO:
        1) replace request.get() to sleep if internet connection broken
'''


class Genre(object):
    def __init__(self, name, genre_id, parent_genre_id):
        self.name = name
        self.genre_id = genre_id
        self.parent_genre_id = parent_genre_id
    def __repr__(self):
        return "Genre(%s, %s, %s)" % (self.name.encode('ascii', errors='backslashreplace'), self.genre_id, self.parent_genre_id)

class Track(object):
    def __init__(self, label, song_id, genre):
        self.label = label
        self.genre = genre
        self.song_id = song_id
        self.yt_id = None

    def __hash__(self):
        return hash(self.yt_id)

    def youtube_id_lookup(self, key):
        query = self.label.replace('-', ' ')
        q = urllib.urlencode({'part':'snippet', 'order':'relevance', 'q':query.encode('utf-8'), 'type':'video', 'key':key})
        search_url = "https://www.googleapis.com/youtube/v3/search?%s" % q
        results = requests.get(search_url).json()["items"]
        if len(results) > 0:
            # arbitrarily select the first one
            self.yt_id = results[0]["id"]["videoId"]

    def retrieve_song_details(self):
        r = requests.get("https://itunes.apple.com/lookup?id=%s" % self.song_id)
        results = r.json()
        if "results" in results:
            return results["results"][0]
        else:
            raise Exception("No such song exists for id=%s" % self.song_id)

    def to_csv(self):
        return (self.label, self.genre.name, self.song_id, self.yt_id)

def find_related_videos(yt_id, key, n=5, process="random"):
    if yt_id == None:
        raise Exception("No youtube link has been found for this video, cannot find related videos")
    print "Finding related video for '%s'..." % yt_id
    if process=="random":
        maxResults = min(n*5, 50)
    elif process=="top":
        maxResults = max(1,min(n,50))
    else:
        raise Exception("Unsupported process %s" % process)
    q = urllib.urlencode({'part':'snippet', 'relatedToVideoId':yt_id, 'type':'video', 'maxResults':maxResults,'key':key})
    search_url = "https://www.googleapis.com/youtube/v3/search?%s" % q
    results = requests.get(search_url).json()["items"]
    print "Found %d related videos" % len(results)
    results = [(result["id"]["videoId"], result["snippet"]["title"]) for result in results]
    if len(results) <= n:
        return results
    if process == "top":
        return results[:n]
    elif process == "random":
        return random.sample(results, n)
    else:
        raise Exception("Unsupported process %s" % process)

def fetch_genres():
    r = requests.get("https://itunes.apple.com/WebObjects/MZStoreServices.woa/ws/genres")
    music_genres = r.json()["34"]["subgenres"]
    genres = []
    for k,v in music_genres.items():
        if ("subgenres" in v):
            for (k2,v2) in v["subgenres"].items():
                genres.append(Genre(v2["name"], k2, k))
        genres.append(Genre(v["name"], k, None))
    return genres

def top_songs_genre(genre, limit=5):
    url = "https://itunes.apple.com/us/rss/topsongs/limit=%d/genre=%s/explicit=true/json" % (limit, genre.genre_id)
    r = requests.get(url)
    try:
        results = r.json()["feed"]["entry"]
    except:
        print "oops!"
        return []
    songs = []
    if (limit == 1):
        return [Track(results["title"]["label"], results["id"]["attributes"]["im:id"], genre)]
    else:
        for result in results:
            print "parsing '%s'" % result["title"]["label"]
            song_id = result["id"]["attributes"]["im:id"]
            songs.append(Track(result["title"]["label"], song_id, genre))
    return songs

def scrape_songs(key, seed_genres=None, include_subgenres=False, limit_per_genre=5):
    if limit_per_genre > 200:
        print "Max number of songs per genre is 200. Defaulting to 200"
        limit_per_genre = 200
    elif limit_per_genre < 1:
        print "Min number of songs per genre is 1. Defaulting to 1"
        limit_per_genre = 1
    genres = fetch_genres()
    print "Found %d genres" % len(genres)
    all_songs = []
    if seed_genres != None:
        genres = [genre for genre in genres if genre.name.lower() in seed_genres]
    for genre in genres:
        print "Fetching genre '%s'" % genre.name
        songs = top_songs_genre(genre, limit_per_genre)
        print "...fetched %d songs" % len(songs)
        for song in songs:
            song.youtube_id_lookup(key)
        songs_with_links = [song for song in songs if song.yt_id != None]
        print "...found %d youtube links" % len(songs_with_links)
        all_songs += songs_with_links
    print "Fetched %d songs in total" % len(all_songs)
    return all_songs

def init_database(conn):
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS song;''')
    c.execute('''DROP TABLE IF EXISTS frontier;''')
    c.execute('''DROP TABLE IF EXISTS genre;''')
    c.execute('''CREATE TABLE song (youtube_id TEXT PRIMARY KEY, label TEXT, song_id TEXT, genre_id TEXT, is_downloaded INTEGER);''')
    c.execute('''CREATE TABLE frontier (youtube_id TEXT PRIMARY KEY, label TEXT);''')
    c.execute('''CREATE TABLE genre (genre_id TEXT PRIMARY KEY, parent_genre_id TEXT, genre_name TEXT);''')
    conn.commit()


def populate_seed(conn, yt_key, seed_genres=None, limit_per_genre=5, limit_frontier_per_song=5):
    c = conn.cursor()
    genres = fetch_genres()
    c.executemany('''INSERT INTO genre VALUES (?,?,?)''', [(genre.genre_id, genre.parent_genre_id, genre.name.lower()) for genre in genres])
    songs = scrape_songs(yt_key, seed_genres, True, limit_per_genre)
    c.executemany('''INSERT OR IGNORE INTO song VALUES (?,?,?,?)''', [(song.yt_id, song.label, song.song_id, song.genre.genre_id) for song in songs])
    frontier = reduce(lambda x,y: x+y, [find_related_videos(song.yt_id, yt_key, limit_frontier_per_song) for song in songs])
    c.executemany('''INSERT OR IGNORE INTO frontier VALUES (?,?)''', frontier)
    conn.commit()

def initialize_scraper(conn, key, seed_genres):
    init_database(conn)
    populate_seed(conn, key, seed_genres, 1)
    # dump status of initialization
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM genre")
    print "Found %d genres" % (c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM song")
    print "Initialized scraper domain with %d songs" % c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM frontier")
    print "Initialized frontier with %d potential songs" % c.fetchone()[0]

def youtube_label_to_itunes_label(yt_label):
    yt_label = re.sub(" ft\. ", " ", yt_label, flags=re.IGNORECASE)
    match = re.match("[\w\s&\+]+ *- *[\w\s,]+", yt_label)
    if match == None:
        return None
    else:
        label = match.group(0)
    return label

def itunes_search(term):
    term = term.replace('-', ' ').encode("utf-8")
    q = urllib.urlencode({'term':term, 'media':'music', 'entity':'song', 'limit':'1'})
    r = requests.get("https://itunes.apple.com/search?%s" % q)
    results = r.json()
    if "results" in results and len(results["results"]) > 0:
        return results["results"][0]
    else:
        return None

def scrape(conn, key):
    c = conn.cursor()
    # take a song from the frontier
    c.execute("SELECT * FROM frontier ORDER BY RANDOM() LIMIT 1");
    (yt_id, label) = c.fetchone()
    c.execute("DELETE FROM frontier WHERE youtube_id=?",[yt_id])
    conn.commit()
    # if already seen discard and continue
    c.execute("SELECT EXISTS(SELECT 1 FROM song WHERE song.youtube_id = ?)", [yt_id])
    exists = c.fetchone()[0]
    if (exists):
        print "Already seen '%s', skipping to next item" % label
        return
    # preprocess youtube label - drop [OFFICIAL MUSIC VIDEO] tags and what not
    search = youtube_label_to_itunes_label(label)
    if search == None:
        print "Invalid label: %s" % label
        return
    print "Looking up processed label: %s" % search
    # try to find the song in iTunes
    itunes_song = itunes_search(search)
    if (itunes_song == None):
        print "Could not find matching iTunes song..."
        return
    actual_label = itunes_song["artistName"] + " - " + itunes_song["trackName"]
    # see if the genre of the found song matches any of our genres
    c.execute("SELECT genre_id FROM genre WHERE genre_name = ?", [itunes_song["primaryGenreName"].lower()])
    genre = c.fetchone()
    if genre == None:
        print "Song not found in genre set, ignoring..."
        return
    genre_id = genre[0]
    # insert new song into our database
    c.execute("INSERT OR IGNORE INTO song VALUES (?,?,?,?)", (yt_id, actual_label, itunes_song["trackId"], genre_id))
    conn.commit()
    # update frontier with related videos
    frontier = find_related_videos(yt_id, key)
    c.executemany('''INSERT OR IGNORE INTO frontier VALUES (?,?)''', frontier)
    conn.commit()

with open('secrets.json') as f:
    key_ring = json.load(f)
conn = sqlite3.connect("foo.db")
seed_genres = ["r&b/soul","soul","rock","alternative","dance","hip-hop/rap", "blues", "classical", "country","jazz","reggae","easy listening"]
#initialize_scraper(conn, key_ring["youtube_key"], seed_genres)
for i in xrange(10000):
    try:
        scrape(conn,key_ring["youtube_key"])
    except:
        print "Caught an error"