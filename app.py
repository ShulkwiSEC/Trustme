from flask import Flask, render_template, request, redirect, session
from urllib.parse import unquote as decode
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from flask_restful import Api, reqparse, Resource
from flask_session import Session
import os

# Database configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
show_db = os.path.join(BASE_DIR, 'Datebases', 'shows.db')
userdb = os.path.join(BASE_DIR, 'Datebases', 'users.db')

# CONFIG
app = Flask(__name__, static_folder='templates/static/')
api = Api(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_HTTPONLY'] = False
Session(app)

# User Management Class
class UserManager:
    @staticmethod
    def init_userdb():
        # if os.path.exists(userdb):
        #     os.remove(userdb)
        try:
            query = """
                DROP TABLE IF EXISTS users;
                DROP TABLE IF EXISTS notes;

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    user_pass TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notes (
                    user_id INTEGER,
                    note TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """
            with sqlite3.connect(userdb) as con:
                cur = con.cursor()
                cur.executescript(query)
                con.commit()
            return True
        except Exception as e:
            print(f"Error initializing user database: {e}")
            return False

    @staticmethod
    def register(username, password):
        try:
            con = sqlite3.connect(userdb)
            cur = con.cursor()
            pass_hash = generate_password_hash(password)
            query = 'INSERT INTO users(username, user_pass) VALUES(?, ?)'
            cur.execute(query, [username, pass_hash])
            con.commit()
            return True
        except sqlite3.IntegrityError:
            print('Username already exists')
            return False
        except Exception as error:
            print(error)
            # DEBUGING
            print(con.execute("SELECT * FROM sqlite_master").fetchall())
            return False
        finally:
            con.close()

    @staticmethod
    def login(username, user_pass):
        try:
            con = sqlite3.connect(userdb)
            cur = con.cursor()
            query = 'SELECT user_pass FROM users WHERE username = ?'
            pass_hash = cur.execute(query, [username]).fetchone()
            if pass_hash is None:
                return False  # Username Not Found
            return check_password_hash(pass_hash[0], user_pass)
        except Exception as error:
            print(error)
            return False
        finally:
            con.close()

# APIs Endpoints
class Moive(Resource):
    def get(self,title):
        title = decode(title)
        p = reqparse.RequestParser()
        try:
            con = sqlite3.connect(db)
            cur = con.cursor()
            qeruy = "SELECT title,year,episodes,genre,rating,votes FROM (SELECT * FROM shows AS s INNER JOIN genres AS g ON s.id = g.show_id INNER JOIN ratings AS r ON r.show_id = s.id) WHERE title LIKE ?"
            rows = cur.execute(qeruy,[f"%{title}%",]).fetchall()
            if rows != []:
                data = list(rows[0])
                data[3] = ''
                for row in rows:
                    data[3] += row[3]+','
                data[3] = data[3][:-1]
                con.commit()
                return {'massage': data},200
            else:
                return {'massage': 'Moive Not Found'},404
        except Exception as error:
            return {'massage': f'Something Went Wrong {error}'},500
    def post(self,title):
        title = decode(title)
        p = reqparse.RequestParser()
        p.add_argument('year', type=str, help='year is required',required=True)
        p.add_argument('episodes',type=int, help='episodes ',required=False,default=1)
        p.add_argument('genre',type=str, help='genre is required',action='append',required=True)
        p.add_argument('rating',type=float, help='rating is required',required=True)
        p.add_argument('votes',type=int, help='votes is required',required=True)
        args = p.parse_args()
        year = args['year']
        episodes = args['episodes']
        genres = args['genre']
        rating = args['rating']
        votes = args['votes']
        InsertINtoSHOWS = 'INSERT INTO shows(title,year,episodes) VALUES(?,?,?);'
        InsertINtoGenre = 'INSERT INTO genres(show_id,genre) VALUES(?,?);'
        InsertINtoRatings = 'INSERT INTO ratings(show_id,rating,votes) VALUES(?,?,?);'
        try:
            con = sqlite3.connect(db)
            cur = con.cursor()
            cur.execute(InsertINtoSHOWS,[title,year,episodes])
            con.commit()
            show_id = cur.execute('SELECT id FROM shows WHERE title = ?',[title,]).fetchone()[0]
            for genre in genres:
                cur.execute(InsertINtoGenre,[show_id,genre])
            cur.execute(InsertINtoRatings,[show_id,rating,votes])
            con.commit()
            return {'massage':f'Movie {title}: {args} Inserted Susccfly'},201
        except Exception as error:
            return {'massage': f'Something Went Wrong {error}'},500

    def put(self,title):
        title = decode(title)
        try:
            p = reqparse.RequestParser()
            print('PUTTTT')
            p.add_argument('rating',type=float, help='rating is required',required=True)
            args = p.parse_args()
            rating = args['rating']
            con = sqlite3.connect(db)
            cur = con.cursor()
            show_id = cur.execute('SELECT id FROM shows WHERE title = ?',[title,]).fetchone()
            if show_id != None:
                qeruy = 'UPDATE ratings SET rating = ? WHERE show_id = ?'
                cur.execute(qeruy,[rating,show_id[0]])
                con.commit()
                return {'massage':f'Movie {title} rating {rating} Updated Susccfly'},201
            else:
                return {'massage': 'Moive Not Found'},404

        except Exception as error:
            return {'massage': f'DEBUGING: Something Went Wrong {error}'},500

    def delete(slef,title):
        title = decode(title)
        p = reqparse.RequestParser()
        try:
            con = sqlite3.connect(db)
            cur = con.cursor()
            testingIftitleFound = cur.execute('SELECT id FROM shows WHERE title = ?',[title,]).fetchone()
            print(testingIftitleFound)
            if (testingIftitleFound != None):
                show_id = cur.execute('SELECT id FROM shows WHERE title = ?',[title,]).fetchone()[0]
                DelFROMShows = 'DELETE FROM shows WHERE title = ?'
                DelFROMGenres = 'DELETE FROM genres WHERE show_id = ?'
                DelFROMRatings = 'DELETE FROM ratings WHERE show_id = ?'
                cur.execute(DelFROMShows,[title,])
                cur.execute(DelFROMRatings,[show_id,])
                cur.execute(DelFROMGenres,[show_id,])
                con.commit()
                return {'massage':f'Movie {title} DELETE Susccfly'},202
            else:
                return {'massage':f'Movie {title} DELETE Not Found'},404
        except Exception as error:
            return {'massage': f'Something Went Wrong {error}'},500

class Notes(Resource):
    def get(self):
        if logedin():
            try:
                username = session['username']
                query = 'SELECT note FROM notes WHERE user_id IN (SELECT id FROM users WHERE username = ?)'
                con = sqlite3.connect(userdb)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                print(username)
                
                user_id_row = cur.execute('SELECT id FROM users WHERE username = ?', [username]).fetchone()
                if not user_id_row:
                    return {'message': 'Username Not Found'}, 404
                
                notes = cur.execute(query, [username]).fetchall()
                notes = [row['note'] for row in notes]
                
                return {'message': notes if notes else 'No notes added yet'}, 200
            except Exception as error:
                return {'message': f'Something Went Wrong: {error}'}, 500
            finally:
                con.close()
        else:
            return {'message': 'Please sign up and log in first.'}, 403

    def post(self):
        p = reqparse.RequestParser()
        if logedin():
            p.add_argument('note', type=str, help='Note is required', required=True)
            args = p.parse_args()
            try:
                note = args['note']
                username = session['username']
                con = sqlite3.connect(userdb)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                
                user_id_row = cur.execute('SELECT id FROM users WHERE username = ?', [username]).fetchone()
                if not user_id_row:
                    return {'message': 'Username Not Found'}, 404
                
                cur.execute('INSERT INTO notes(user_id, note) VALUES(?, ?)', [user_id_row['id'], note])
                con.commit()
                return {'message': 'Note added successfully'}, 201
            except Exception as error:
                return {'message': f'Something Went Wrong: {error}'}, 500
            finally:
                con.close()
        else:
            return {'message': 'Please sign up and log in first.'}, 403

    def put(self):
        p = reqparse.RequestParser()
        if logedin():
            p.add_argument('new_note',type=str, help='New note is required',required=True)
            p.add_argument('old_note',type=str, help='Old note is required',required=True)
            args = p.parse_args()
            try:
                username = session['username']
                new_note = args['new_note']
                old_note = args['old_note']
                con = sqlite3.connect(userdb)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                
                user_id_row = cur.execute('SELECT id FROM users WHERE username = ?', [username]).fetchone()
                if not user_id_row:
                    return {'message': 'Username Not Found'}, 404
                
                old_note_found = cur.execute('SELECT note FROM notes WHERE user_id = ? AND note = ?', [user_id_row['id'], old_note]).fetchone()
                if not old_note_found:
                    return {'message': 'Old Note Not Found'}, 404
                
                cur.execute('UPDATE notes SET note = ? WHERE user_id = ? AND note = ?', [new_note, user_id_row['id'], old_note])
                con.commit()
                return {'message': 'Note updated successfully!'}, 200
            except Exception as error:
                return {'message': f'Something Went Wrong: {error}'}, 500
            finally:
                con.close()
        else:
            return {'message': 'Please sign up and log in first.'}, 403

    def delete(self):
        p = reqparse.RequestParser()
        if logedin():
            p.add_argument('note', type=str, required=True,help='Note is required')
            args = p.parse_args()
            try:
                note = args['note']
                username = session['username']
                con = sqlite3.connect(userdb)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                
                user_id_row = cur.execute('SELECT id FROM users WHERE username = ?', [username]).fetchone()
                if not user_id_row:
                    return {'message': 'Username Not Found'}, 404
                
                note_found = cur.execute('SELECT note FROM notes WHERE user_id = ? AND note = ?', [user_id_row['id'], note]).fetchone()
                if not note_found:
                    return {'message': 'Note Not Found'}, 404
                
                cur.execute('DELETE FROM notes WHERE note = ? AND user_id = ?', [note, user_id_row['id']])
                con.commit()
                return {'message': 'Note deleted successfully!'}, 200
            except Exception as error:
                return {'message': f'Something Went Wrong: {error}'}, 500
            finally:
                con.close()
        else:
            return {'message': 'Please sign up and log in first.'}, 403


# Usefull Functions
def comming_soon():
    return render_template('comming_soon.html')

def logedin():
    return 'username' in session

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    else:
        return render_template('singup.html', msg='You need to sign up and log in to use our services')

@app.route('/add_a_movie')
def addmovie():
    if 'username' in session:
        return render_template('NewMovie.html')
    else:
        return render_template('singup.html', msg='You need to sign up and log in to use our services')

@app.route('/delete_movie')
def remove_movie():
    if 'username' in session:
        return render_template('delete_movie.html')
    else:
        return render_template('singup.html', msg='You need to sign up and log in to use our services')

@app.route('/edit_movie')
def edit_movie():
    if 'username' in session:
        return render_template('edit_movie.html')
    else:
        return render_template('singup.html', msg='You need to sign up and log in to use our services')

@app.route('/singup', methods=['GET', 'POST'])
def singup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            if UserManager.register(username, password):
                return redirect('/singin')
            else:
                return render_template('singup.html', msg='Username already exists')
        else:
            return render_template('singup.html', msg='Username & password required')
    else:
        return render_template('singup.html')

@app.route('/singin', methods=['GET', 'POST'])
def singin():
    if request.method == 'POST':
        if 'username' in session:
            session.clear()
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            if UserManager.login(username, password):
                session['username'] = username
                return redirect('/')
            else:
                return render_template('login.html', msg='Invalid username or password')
        else:
            return render_template('login.html', msg='Username & password required')
    else:
        return render_template('login.html')

@app.route('/movie_information')
def movies_info():
    catgory = request.args.get('catgory', None)
    con = sqlite3.connect(show_db)
    con.row_factory = sqlite3.Row # Output Format
    cur = con.cursor()
    if not catgory:
        query = "SELECT s.id, s.title, s.year, s.episodes, GROUP_CONCAT(g.genre, ', ') AS genres, r.rating, r.votes, GROUP_CONCAT(pw.name, ', ') AS writers FROM shows AS s JOIN genres AS g ON s.id = g.show_id  JOIN ratings AS r ON s.id = r.show_id  JOIN writers AS w ON s.id = w.show_id  JOIN people AS pw ON w.person_id = pw.id GROUP BY s.id, s.title, s.year, s.episodes, r.rating, r.votes LIMIT 50;"
        movies = cur.execute(query).fetchall()
    else:
        catgory = decode(catgory)
        query = "SELECT s.id, s.title, s.year, s.episodes, r.rating, r.votes, GROUP_CONCAT(g.genre, ', ') AS genres FROM shows AS s JOIN genres AS g ON s.id = g.show_id JOIN ratings AS r ON s.id = r.show_id WHERE g.genre = ? GROUP BY s.id, s.title, s.year, s.episodes, r.rating, r.votes LIMIT 50;"
        movies = cur.execute(query,[catgory,]).fetchall()
        con.commit()
        con.close()
    return render_template('movie_information.html',movies=movies)


@app.route('/notes')
def note():
    return render_template('Notebook.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        session.clear()
        return redirect('/')
    else:
        return '<h1>Please sign up and log in first.</h1>'


api.add_resource(Movie, '/api/movie/<string:title>')
api.add_resource(Notes, '/api/v1/notes/')


def main():
    if __name__ == '__main__':
        if not UserManager.init_userdb():
            exit(1)
        app.run(host='0.0.0.0',port=80)


main()