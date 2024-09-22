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


# Show Management Class
class ShowManager:
    @staticmethod
    def get_movie(title):
        title = decode(title)
        try:
            con = sqlite3.connect(show_db)
            cur = con.cursor()
            query = """
                SELECT title, year, episodes, GROUP_CONCAT(genre, ', ') AS genres, rating, votes
                FROM shows
                JOIN genres ON shows.id = genres.show_id
                JOIN ratings ON ratings.show_id = shows.id
                WHERE title LIKE ?
            """
            rows = cur.execute(query, [f"%{title}%"]).fetchall()
            if rows:
                return {'message': list(rows[0])}, 200
            else:
                return {'message': 'Movie Not Found'}, 404
        except Exception as error:
            return {'message': f'Something Went Wrong: {error}'}, 500

    @staticmethod
    def add_movie(data):
        try:
            con = sqlite3.connect(show_db)
            cur = con.cursor()
            InsertINtoSHOWS = 'INSERT INTO shows(title, year, episodes) VALUES(?, ?, ?);'
            cur.execute(InsertINtoSHOWS, (data['title'], data['year'], data['episodes']))
            con.commit()
            show_id = cur.execute('SELECT id FROM shows WHERE title = ?', [data['title']]).fetchone()[0]
            for genre in data['genres']:
                cur.execute('INSERT INTO genres(show_id, genre) VALUES(?, ?);', (show_id, genre))
            cur.execute('INSERT INTO ratings(show_id, rating, votes) VALUES(?, ?, ?);', (show_id, data['rating'], data['votes']))
            con.commit()
            return {'message': f'Movie {data["title"]} inserted successfully'}, 201
        except Exception as error:
            return {'message': f'Something Went Wrong: {error}'}, 500

    @staticmethod
    def update_rating(title, rating):
        title = decode(title)
        try:
            con = sqlite3.connect(show_db)
            cur = con.cursor()
            show_id = cur.execute('SELECT id FROM shows WHERE title = ?', [title]).fetchone()
            if show_id:
                cur.execute('UPDATE ratings SET rating = ? WHERE show_id = ?', (rating, show_id[0]))
                con.commit()
                return {'message': f'Movie {title} rating updated successfully'}, 200
            else:
                return {'message': 'Movie Not Found'}, 404
        except Exception as error:
            return {'message': f'Something Went Wrong: {error}'}, 500

    @staticmethod
    def delete_movie(title):
        title = decode(title)
        try:
            con = sqlite3.connect(show_db)
            cur = con.cursor()
            show_id = cur.execute('SELECT id FROM shows WHERE title = ?', [title]).fetchone()
            if show_id:
                cur.execute('DELETE FROM shows WHERE title = ?', [title])
                cur.execute('DELETE FROM genres WHERE show_id = ?', [show_id[0]])
                cur.execute('DELETE FROM ratings WHERE show_id = ?', [show_id[0]])
                con.commit()
                return {'message': f'Movie {title} deleted successfully'}, 200
            else:
                return {'message': 'Movie Not Found'}, 404
        except Exception as error:
            return {'message': f'Something Went Wrong: {error}'}, 500


# API Endpoints
class Movie(Resource):
    def get(self, title):
        return ShowManager.get_movie(title)

    def post(self, title):
        p = reqparse.RequestParser()
        p.add_argument('year', type=str, required=True)
        p.add_argument('episodes', type=int, default=1)
        p.add_argument('genre', type=str, action='append', required=True)
        p.add_argument('rating', type=float, required=True)
        p.add_argument('votes', type=int, required=True)
        args = p.parse_args()
        return ShowManager.add_movie({**args, 'title': title})

    def put(self, title):
        p = reqparse.RequestParser()
        p.add_argument('rating', type=float, required=True)
        args = p.parse_args()
        return ShowManager.update_rating(title, args['rating'])

    def delete(self, title):
        return ShowManager.delete_movie(title)



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