from flask import Flask, json, Response, request, render_template, url_for, session, logging, flash, redirect
import sqlite3
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename
from os import path, getcwd
import time
from ta import Database
from face import Face
from functools import wraps
import base64
import re
from datetime import datetime


app = Flask(__name__)

app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.db = Database()
app.face = Face(app)


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def get_user_by_id(user_id):
    user = {}
    results = app.db.select(
        'SELECT karyawan.id, karyawan.name, karyawan.telpon, karyawan.alamat, karyawan.created, faces.id, faces.user_id, faces.filename,faces.created FROM karyawan LEFT JOIN faces ON faces.user_id = karyawan.id WHERE karyawan.id = ?', 
        [user_id])

    index = 0
    for row in results:
        # print(row)
        face = {
            "id": row[5],
            "user_id": row[6],
            "filename": row[7],
            "created": row[8],
        }
        if index == 0:
            user = {
                "id": row[0],
                "name": row[1],
                "telpon": row[2],
                "alamat": row[3],
                "created": row[4],
                "faces": [],
            }
        if row[5]:
            user["faces"].append(face)
        index = index + 1

    if 'id' in user:
        return user
    return None


def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM karyawan WHERE karyawan.id = ?', [user_id])
    # also delete all faces with user id
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])

def delete_karyawan_foto(user_id):
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password_candidate = request.form['password']

#         result = app.db.login("SELECT COUNT (username) FROM admin WHERE username=?", (username,))
#         print (result)
#         result = result[0]
#         if result > 0:
#             data = app.db.get_password("SELECT password FROM admin WHERE username=?", (username,))
#             # password = data['password']
#             data = data[0]
#             if sha256_crypt.verify(password_candidate, data):
#                 # passed
#                 session['logged_in'] = True
#                 session['username'] = username

#                 flash('You are now logged in', 'success')
#                 return redirect(url_for('dashboard'))
#             else:
#                 print('PASSWORD NOT MATCH')
#         else:
#             print('NO USER')
#     return render_template('login.html')

#   Route for Homepage
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        result = app.db.login("SELECT COUNT (username) FROM admin WHERE username=?", (username,))
        print (result)
        result = result[0]
        if result > 0:
            data = app.db.get_password("SELECT password FROM admin WHERE username=?", (username,))
            # password = data['password']
            data = data[0]
            if sha256_crypt.verify(password_candidate, data):
                # passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                print('PASSWORD NOT MATCH')
        else:
            print('NO USER')
    return render_template('login.html')

# check jika user sudah login atau belum
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login!', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# @app.route('/api', methods=['GET'])
# def homepage():
#     output = json.dumps({"api": '1.0'})
#     return success_handle(output)

# route for user profile
@app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
def user_profile(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User not found", 404)
    if request.method == 'DELETE':
        delete_user_by_id(user_id)
        return success_handle(json.dumps({"deleted": True}))

# delete user karyawan
@app.route('/delete_user_karyawan/<int:user_id>', methods=['GET', 'DELETE', 'POST'])
def delete_user_karyawan(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User not found", 404)
    if request.method == 'POST':
        delete_user_by_id(user_id)
        # return success_handle(json.dumps({"deleted": True}))
        return redirect(url_for('dataKaryawan'))


# router for recognize a unknown face
# @app.route('/api/recognize', methods=['POST'])
# def recognize():
#     if 'file' not in request.files:
#         return error_handle("Image is required")
#     else:
#         file = request.files['file']
#         # file extension valiate
#         if file.mimetype not in app.config['file_allowed']:
#             return error_handle("File extension is not allowed")
#         else:

#             filename = secure_filename(file.filename)
#             unknown_storage = path.join(app.config["storage"], 'unknown')
#             file_path = path.join(unknown_storage, filename)
#             file.save(file_path)

#             user_id = app.face.recognize(filename)
#             if user_id:
#                 user = get_user_by_id(user_id)
#                 message = {"message": "Hey we found {0} matched with your face image".format(user["name"]),
#                            "user": user}
#                 return success_handle(json.dumps(message))
#             else:

#                 return error_handle("Sorry we can not found any people matched with your face image, try another image")

@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

# detail karyawan
@app.route('/dataKaryawan')
@is_logged_in
def dataKaryawan():
    views = app.db.query('SELECT * FROM karyawan')

    if views != None:
        return render_template('dataKaryawan.html', views=views)
    else:
        msg = "Tidak ada data Karyawan"        
        return render_template('dataKaryawan.html', msg=msg)
    return render_template('dataKaryawan.html', views=views)

@app.route('/tambah_karyawan', methods=['GET', 'POST'])
@is_logged_in
def tambahKaryawan():
    if 'file' not in request.files:
        return render_template('tambah_karyawan.html')
    else:
        print("File request", request.files)
        file = request.files['file']

        if file.mimetype not in app.config['file_allowed']:

            print("File extension is not allowed")

            return error_handle("We are only allow upload file with *.png , *.jpg")
        else:
            name = request.form['name']
            telpon = request.form['telpon']
            alamat = request.form['alamat']

            print("File is allowed and will be saved in ", app.config['storage'])
            filename = secure_filename(file.filename)
            trained_storage = path.join(app.config['storage'], 'trained')
            file.save(path.join(trained_storage, filename))
            # let start save file to our storage
            # save to our sqlite database.db
            created = int(time.time())
            user_id = app.db.insert('INSERT INTO karyawan(name, telpon, alamat, created) values(?,?,?,?)', [name, telpon, alamat, created])
                        
            if user_id:

                print("User saved in data", name, user_id)
                    # user has been save with user_id and now we need save faces table as well

                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) values(?,?,?)',
                                            [user_id, filename, created])

                if face_id:

                    print("cool face has been saved")
                    face_data = {"id": face_id, "filename": filename, "created": created}
                    return_output = json.dumps({"id": user_id, "name": name, "face": [face_data]})
                    return success_handle(return_output)
                else:

                    print("An error saving face image.")

                    return error_handle("n error saving face image.")
                return render_template('dataKaryawan.html')

            else:
                print("Something happend")
                return error_handle("An error inserting new user")
            

class edit_karyawan(Form):
    name = StringField('name', [validators.Length(min=1, max=50)])
    telpon = StringField('telpon', [validators.Length(min=2, max=25)])
    alamat = StringField('alamat', [validators.Length(min=1, max=50)])

# edit user karyawan
@app.route('/edit_karyawan/<int:user_id>', methods=['GET', 'POST', 'PUT'])
@is_logged_in
def edit_user_karyawan(user_id):
    row_karyawan = app.db.lihat_karyawan('SELECT * FROM karyawan WHERE karyawan.id = ?', [user_id])

    form = edit_karyawan(request.form)

    form.name.data = row_karyawan[1]
    form.telpon.data = row_karyawan[2]
    form.alamat.data = row_karyawan[3]

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        telpon = request.form['telpon']
        alamat = request.form['alamat']

        app.db.simpan_edit_karyawan("UPDATE karyawan SET name=?, telpon=?, alamat=? WHERE id=?", (name, telpon, alamat, user_id))
        flash('Data karyawan berhasil diubah')

        return redirect(url_for('dataKaryawan'))
    return render_template('edit_karyawan.html', form=form)


class RegisterForm(Form):
    username = StringField('Username', [validators.length(min=1, max=50)])
    email = StringField('Email', [validators.length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm(request.form)
#     if request.method =='POST' and form.validate():
#         username = form.username.data
#         email = form.email.data
#         password = sha256_crypt.encrypt(str(form.password.data))

#         # sql
#         qr = app.db.insert("INSERT INTO admin(username, email, password) VALUES(?,?,?)", (username, email, password))

#         flash('You are now registered and can log in', 'success')

#         return redirect(url_for('login'))
#     return render_template('register.html', form=form)

@app.route('/dashboard_absensi')
def dashboard_absensi():
    return render_template('dashboard_absensi.html')

# Bagian karyawan
@app.route('/absenMasuk', methods=['GET', 'POST'])
def recognize():
    if request.method == 'GET':
        return render_template('absensi_masuk.html')    
    else:
        image_b64 = request.values[('imageBase64')]
        imgstr = re.search(r'data:image/png;base64,(.*)',image_b64).group(1)
        convert = open('storage/unknown/output.png', 'wb')
        decoded = base64.b64decode(imgstr)
        convert.write(decoded)
        convert.close()

        user_id = app.face.recognize("output.png")
        if user_id:
            time = datetime.now().strftime("%B %d, %Y %I:%M%p")
            user = get_user_by_id(user_id)
            print(user)
            print(time)
            simpan = app.db.insert('INSERT INTO absensi(name,jam_masuk) values(?,?)', (user["name"], time,))
            print(simpan)
            message = {"message": "Hey we found {0} matched with your face image".format(user["name"]),
                        "user": user}
            return success_handle(json.dumps(message))
        else:
            return error_handle("Sorry we can not found any people matched with your face image, try another image")
        return ('tidak ada data wajah')

@app.route('/absenPulang', methhods=['GET', 'POST'])
def absensiPulang():
    print("on going")

# Run the app
if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'Thisissupossedtobesecret!'
    app.run()
