"""
Final project!
CIS 41B Adv Python
Mar 23, 2021

Ben Lublin
Maria Gorbunova

Enjoy organizing your movie choices!:)

Free avatars from Freepik user sentavio: https://www.freepik.com/sentavio

Backend - API and Database interaction
Written by Maria, Reviewed by Ben
"""
from io import BytesIO
from PIL import Image
import threading
import requests
import sqlite3
import time
import os

API_KEY = '0804ffb80d5c8e0a392dfef6ae19642a'


class APITalker:
    def __init__(self):
        print()

    def getGenres(self):
        """Returns the list of genres and respective ids"""
        url = f'https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}&language=en-US'
        r = requests.get(url)
        config = r.json()
        return config['genres']

    def processData(self, url):
        """requests data on list of movies, starts threads to get images, returns list of tuples"""
        r = requests.get(url)
        config = r.json()
        start = time.time()
        movieList = []
        threads = []  # create a list of threads, each thread will run function fetch_statedata
        for movie in config['results']:
            t = threading.Thread(target=self.getMovie,
                                 args=(movieList, movie))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        print("~*~*~*~*~*~*~*~ Total elapsed time: {:.2f}s ~*~*~*~*~*~*~*~".format(time.time() - start))

        return movieList
        #[(movie['id'], movie['title'], movie['overview'], 0, movie['genre_ids'],
                 #movie['vote_average'], movie['release_date'][0:4], self.getPoster(movie['id'])) for movie in config['results']]

    def getMovie(self, movieList, movie):
        """for threading; mostly responsible for assembling a tuple -> most importantly calling api for poster """
        movieList.append((movie['id'], movie['title'], movie['overview'], 0, movie['genre_ids'],
         movie['vote_average'], movie['release_date'][0:4], self.getPoster(movie['id'])))


    def popularList(self):
        """holds the url for popular movies"""
        # updates every day
        url = f'https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page=1'
        return self.processData(url)

    def releasedList(self):
        """holds the url for newly released movies"""
        url = f'https://api.themoviedb.org/3/movie/upcoming?api_key={API_KEY}&language=en-US&page=1'
        return self.processData(url)

    def searchName(self, name):
        """holds the url for search based on the name"""
        url = f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={name.replace(" ", "+")}'
        '''This will return a few fields, the one you want to look at is the results field. 
        This is an array and will contain our standard movie list objects. 
        With the item above in hand, you can see the id of the movie is 343611. 
        You can use that id to query the movie details method:
        https://api.themoviedb.org/3/movie/343611?api_key={api_key}'''

        return self.processData(url)

    def searchID(self, movie_id):
        """holds the url for certain movie id"""
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}'
        r = requests.get(url)
        movie = r.json()

        return (
            movie['id'], movie['title'], movie['overview'], 0, ' '.join(str(genre['id']) for genre in movie['genres']),
            movie['vote_average'], movie['release_date'][0:4], self.getPoster(movie['id']))

    def searchMovie(self, year='*', with_genres='*', vote_average='*'):  # popularity
        """search movie by several parameters: year, genre"""
        url = f'https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=en-US&sort_by=popularity.desc' 
        if year != '*':
            url += f'&primary_release_year={year}'
        if with_genres != '*':
            url += f'&with_genres={with_genres}'
        if vote_average != '*':
            url += f'&vote_average.gte={vote_average}'
            
        return self.processData(url)

    def size_str_to_int(self, x):
        """for sorting to get the largest image"""
        return float("inf") if x == 'original' else int(x[1:])

    def getPoster(self, movie_id):
        """ downloads image in a bytes fromat or replaces with a placeholder"""
        url = f'http://api.themoviedb.org/3/configuration?api_key={API_KEY}'
        r = requests.get(url)
        config = r.json()
        base_url = config['images']['base_url']
        sizes = config['images']['poster_sizes']
        max_size = max(sizes, key=self.size_str_to_int)

        IMG_PATTERN = f'http://api.themoviedb.org/3/movie/{movie_id}/images?api_key={API_KEY}'
        r = requests.get(IMG_PATTERN)
        api_response = r.json()

        photo = ''
        try:
            img_url = base_url + max_size + api_response['posters'][0]['file_path']
            r = requests.get(img_url)
            photo = r.content
        except IndexError:
            #print('No poster', movie_id)
            photo = Image.open('placeholder.jpeg')
            # Create a buffer to hold the bytes
            buf = BytesIO()
            # Save the image as jpeg to the buffer
            photo.save(buf, 'jpeg')
            # Rewind the buffer's file pointer
            buf.seek(0)
            # Read the bytes from the buffer
            photo = buf.read()
            # Close the buffer
            buf.close()

        """filetype = r.headers['content-type'].split('/')[-1]
        filename = 'poster_{0}.{1}'.format(movie_id, filetype)
        with open(filename, 'wb') as w:
            w.write(r.content)"""

        # return image as a blob
        return photo


class DBTalker:
    def __init__(self, myapi):
        if not os.path.exists('moviesDB.db'):
            #if db didnt exist
            self.conn = sqlite3.connect('moviesDB.db')
            with self.conn:
                self.cur = self.conn.cursor()
                #just in case dropping old values:
                self.cur.execute("""DROP TABLE IF EXISTS GenresDB""")
                self.cur.execute("""CREATE TABLE GenresDB( genre_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                                   genre TEXT UNIQUE ON CONFLICT IGNORE )""")
                genre_list = [(genre['id'], genre['name']) for genre in myapi.getGenres()]
                self.cur.executemany(""" INSERT INTO GenresDB VALUES (?,?) """, genre_list)

                # just in case dropping old values:
                self.cur.execute("""DROP TABLE IF EXISTS MoviesDB""")
                self.cur.execute("""CREATE TABLE MoviesDB( movie_id INTEGER NOT NULL PRIMARY KEY UNIQUE ON CONFLICT IGNORE,
                                                   title TEXT UNIQUE ON CONFLICT IGNORE, 
                                                   overview TEXT,
                                                   watched INTEGER,
                                                   genre_ids TEXT,
                                                   vote_average INTEGER,
                                                   year INTEGER,
                                                   poster BLOB NOT NULL
                                                   )""")

                # populate with default movies for starters
                listToWatch = [527774,791373, 512200, 508442, 508415, 316, 672, 674, 762, 31011]
                for i in listToWatch:
                    self.cur.execute(""" INSERT INTO MoviesDB VALUES (?,?,?,?,?,?,?,?) """, (myapi.searchID(i)))

        else:
            self.conn = sqlite3.connect('moviesDB.db')
            with self.conn:
                self.cur = self.conn.cursor()

    def randomChoice(self):
        """pick 5 random movies from unwatched"""
        self.cur.execute('''SELECT * FROM MoviesDB 
                        WHERE movie_id IN (SELECT movie_id FROM MoviesDB 
                                                ORDER BY RANDOM() LIMIT 5) 
                        AND watched=0''')
        result = self.cur.fetchall()
        return result

    def watchedList(self):
        """return movies that were already watched"""
        self.cur.execute('''SELECT * FROM MoviesDB 
                        WHERE watched=1''')
        result = self.cur.fetchall()
        return result

    def wantToWatch(self):
        """return movies from the to watch list"""
        self.cur.execute('''SELECT * FROM MoviesDB 
                        WHERE watched==0''')
        result = self.cur.fetchall()
        return result

    def change_watched(self, movie_id):
        """ edit the movie so it changes to watched movie"""
        self.cur.execute("""UPDATE MoviesDB
                            SET watched = 1
                            WHERE movie_id = (?)""", (movie_id,))
        result = self.cur.fetchone()
        self.conn.commit()
        return result

    def selectOne(self, movie_id):
        """selects one movie from db by movie_id"""
        self.cur.execute('''SELECT * FROM MoviesDB 
                        WHERE movie_id==(?)''', (movie_id,))
        result = self.cur.fetchone()
        return result

    def insert(self, movie):
        """insert one movie in the db"""
        self.cur.execute(""" INSERT INTO MoviesDB VALUES (?,?,?,?,?,?,?,?) """, movie)
        result = self.cur.fetchone()
        self.conn.commit()
        return result


    def remove(self, movie_id):
        """remove the movie from database"""
        self.cur.execute('''Delete FROM MoviesDB 
                        WHERE movie_id==(?)''', (movie_id,))
        result = self.cur.fetchone()
        self.conn.commit()
        return result

    def getGenres(self):
        """get the list of tuples for genre name and id"""
        self.cur.execute('''SELECT * FROM GenresDB ''')
        result = self.cur.fetchall()
        return result


"""  TESTING  """

# create api
# myapi = APITalker()
# x = myapi.getGenres()

# print(type(x[0][1]))
# print(type(x[0][0]))
      

#print("before loop")
#for movie in myapi.searchMovie(year="2009", with_genres="14", vote_average=7):
    #print(movie[0], movie[1], movie[2])

#print("after loop")

'''
#search by id
movie = myapi.searchID(762)
print(movie[0], movie[1], movie[2], movie[3], "\n", type(movie[4]), type(movie[5]))


#searching by name
for movie in myapi.searchName("Harry Potter"):
    print(movie[0], movie[1], movie[2])

# return list of popular
print("Popular List: ")
for i in myapi.popularList():
    print(i[1])


#return list of released
print("Released List: ")
for i in myapi.releasedList():
    print(i[1])

# search the matrix
for movie in myapi.searchName("The Matrix"):
    print(movie[0], movie[1], movie[2])


# print(myapi.searchName("Avatar"))
'''
#search year
# for movie in myapi.searchMovie(year="2004"):
    # print(f"Name: {movie[1]} ::: Year: {movie[6]}\nPlot: {movie[2]}")
'''
#search genre
for movie in myapi.searchMovie(with_genres="14"):
    print(movie[1], movie[2])
'''
# # search genre and year
# for movie in myapi.searchMovie(year="2009", with_genres="14"):
    # print(f"Name: {movie[1]} ::: Year: {movie[6]}\nPlot: {movie[2]}")
'''
# search genre, year, vote
for movie in myapi.searchMovie(year="2009", with_genres="14", vote_average=7):
    print(movie[1], movie[2])

'''


#mydb = DBTalker(myapi)


'''
# random choice
for movie in mydb.randomChoice():
    print(movie[1], movie[2])

#change to watched
print(mydb.change_watched(527774))

print("Watched:")
for movie in mydb.watchedList():
    print(movie[1], movie[2])

print("Want to watch:")
for movie in mydb.wantToWatch():
    print(movie[1], movie[2])

movie = myapi.searchName("Fantastic Beasts and where to find them")

print(movie[0])
print(mydb.insert(movie[0]))
print(mydb.watchedList())
print(mydb.wantToWatch())

myapi.getPoster(672)

print(mydb.getGenres())'''
