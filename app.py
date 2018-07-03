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
import datetime


app = Flask(__name__)

app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.db = Database()
app.face = Face(app)

# success function handling
def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)

# error function handling
def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)

# get karyawan id
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

# delete user
def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM karyawan WHERE karyawan.id = ?', [user_id])
    # also delete all faces with user id
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])


# class registrationForm(Form):
#     name = StringField('name', [validators.Length(min=1, max=50)])
#     email = StringField('email', [validators.Length(min=1, max=50)])
#     password = PasswordField('password', [validators.DataRequired(),validators.EqualTo('confirm', message='password do not match')])
#     confirm = PasswordField('confirm password')

# @app.route('/registration', methods=['GET', 'POST'])
# def register():
#     form = registrationForm(request.form)
#     if request.method == 'POST' and form.validate():
#         name = form.name.data
#         email = form.email.data
#         password = sha256_crypt.encrypt(form.password.data)

#         app.db.insert('INSERT INTO admin(username, email, password) VALUES(?,?,?)', (name, email, password))
#         flash('data baru dibuat')
#         return redirect(url_for('login'))
#     return render_template('register.html', form=form)

# login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        # cek user di database
        result = app.db.login("SELECT COUNT (username) FROM admin WHERE username=?", (username,))
        result = result[0]
        if result > 0: # jika ada 
            data = app.db.get_password("SELECT password FROM admin WHERE username=?", (username,))
            # password = data['password']
            data = data[0]
            print(data)
            if sha256_crypt.verify(password_candidate, data):
                # passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard')) # jika sukses, langsung redirect ke menu dashboard 
            else:
                error = 'Invalid user or password'
                return render_template('login.html', error=error) # jika gagal login
        else:
            error = 'No user'
            return render_template('login.html', error=error)
    return render_template('login.html')

# cek autentikasi sebelum masuk ke url lain
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login!', 'danger') # pesan jika tidak ada autentikasi masuk
            return redirect(url_for('login'))
    return wrap

# @app.route('/data_admin')
# def dataAdmin():
#     return render_template('data_admin.html') 

# class admin_edit_form(Form):
#     oldpassword = PasswordField('oldpassword', [validators.DataRequired()])    
#     newpassword = PasswordField('password', [validators.DataRequired(),validators.EqualTo('confirm', message='password do not match')])
#     confirm = PasswordField('confirm password')

# @app.route('/edit_admin', methods=['GET', 'POST', 'PUT'])
# def editAdmin():
#     if request.method == 'POST' and form.validate():
#         form = registrationForm(request.form)
#         old_pass = request.form['oldpassword']
#         app.db.lihat_karyawan('SELECT ')
#         if sha256_crypt.verify(old_pass)
#             newpassword = sha256_crypt.encrypt(form.password.data)

#             app.db.simpan_edit_karyawan("UPDATE admin SET password=? WHERE username=? and admin_id=?", (password, username, admin_id))
            
#             flash('update berhasil')
#             return redirect(url_for('dataAdmin'))
#     return render_template('edit_admin.html', form=form)

# logout admin
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# # route for user profile
# @app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
# def user_profile(user_id):
#     if request.method == 'GET':
#         user = get_user_by_id(user_id)
#         if user:
#             return success_handle(json.dumps(user), 200)
#         else:
#             return error_handle("User not found", 404)
#     if request.method == 'DELETE':
#         delete_user_by_id(user_id)
#         return success_handle(json.dumps({"deleted": True}))

# hapus karyawan
@app.route('/delete_user_karyawan/<int:user_id>', methods=['GET', 'DELETE', 'POST'])
@is_logged_in
def delete_user_karyawan(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User not found", 404)
    if request.method == 'POST':
        delete_user_by_id(user_id)
        return redirect(url_for('dataKaryawan'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


@app.route('/dataAbsensi')
@is_logged_in
def dataAbsensi():
    views = app.db.query('SELECT * FROM absensi')

    if views:
        return render_template('dataAbsensi.html', views=views)
    else:
        flash('Tidak ada data absen hari ini', 'success')
        return render_template('dataAbsensi.html')
    return render_template('dataAbsensi.html', views=views)

# MENU DATA KARYAWAN
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

# TAMBAH KARYAWAN BARU
@app.route('/tambah_karyawan', methods=['GET', 'POST'])
@is_logged_in
def tambahKaryawan():
    if 'file' not in request.files:
        return render_template('tambah_karyawan.html')
    else:
        print("File request", request.files)
        file = request.files['file']

        if file.mimetype not in app.config['file_allowed']:

            flash('File extension is not allowed', 'danger')

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
                    app.face.load_all()
                    flash('data baru telah dimasukkan', 'success')
                    return render_template('dataKaryawan.html')
                else:

                    print("An error saving face image.")

                    return error_handle("n error saving face image.")

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
        flash('Data karyawan berhasil diubah', 'success')

        return redirect(url_for('dataKaryawan'))
    return render_template('edit_karyawan.html', form=form)

# kelola absensi
@app.route('/dashboard_absensi')
def dashboard_absensi():
    return render_template('dashboard_absensi.html')



# Bagian karyawan
@app.route('/absen')
def absen():
    return render_template('absensi_pulang.html')

@app.route('/absenMasuk', methods=['GET', 'POST'])
def absensiMasuk():
    if request.method == 'GET':
        cek_tanggal = datetime.datetime.now().strftime("%B %d, %Y")        
        views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
        viewInJSON = json.dumps(views)
        if views:
            return success_handle(viewInJSON)
        else:
            return error_handle(['terjadi kesalahan'])
    else:
        image_b64 = request.values[('imageBase64')]
        imgstr = re.search(r'data:image/png;base64,(.*)',image_b64).group(1)
        convert = open('storage/unknown/output.jpg', 'wb')
        decoded = base64.b64decode(imgstr)
        convert.write(decoded)
        convert.close()

        user_ids = app.face.recognize("output.jpg")
        print(user_ids)

        # user_id = app.face.recognize("output.jpg")
        # if user_id:
        #     tanggal = datetime.datetime.now().strftime("%B %d, %Y")
        #     jam_masuk = datetime.datetime.now().strftime("%I:%M%p")
        #     # waktu_jadwal = datetime.time(8, 0, 0)
        #     # print (waktu_jadwal.strftime("%T"))
        #     user = get_user_by_id(user_id)
        #     # print(type(user))
            
        #     id_user1 = user["id"]

        #     getStatus = app.db.lihat_absensi("SELECT * FROM absensi WHERE tanggal_absen=? AND kar_id=?", [tanggal,id_user1])

        #     if getStatus is None:
        #         stat_masuk = "Yes"
        #         j_pulang = "No"
        #         ket = "Belum absen Pulang"
        #         s_pulang = "No"
        #         simpanBaru = app.db.insert('INSERT INTO absensi(tanggal_absen, name, jam_masuk, jam_pulang, keterangan, s_masuk, s_pulang, kar_id) VALUES(?,?,?,?,?,?,?,?)', [tanggal, user["name"], jam_masuk, j_pulang, ket, stat_masuk, s_pulang, id_user1])
                
        #         # menampilkan preview absensi hanya pada hari ini
        #         cek_tanggal = datetime.datetime.now().strftime("%B %d, %Y")        
        #         views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
        #         viewInJSON = json.dumps(views)
        #         return success_handle(viewInJSON)
        #     else:
        #         return error_handle(['data wajah tidak ditemukan'])
        # else:
            # return error_handle(['terjadi kesalahan'])

@app.route('/absenPulang', methods=['GET', 'POST'])
def absensiPulang():
    if request.method == 'GET':
        cek_tanggal = datetime.datetime.now().strftime("%B %d, %Y")        
        views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
        viewInJSON = json.dumps(views)
        if views:
            return success_handle(viewInJSON)
        else:
            flash('Tidak ada data absen hari ini', 'success')
            return render_template('absensi_pulang.html')
        return render_template('absensi_pulang.html', views=views)
    else:
        image_b64 = request.values[('imageBase64')]
        imgstr = re.search(r'data:image/png;base64,(.*)',image_b64).group(1)
        convert = open('storage/unknown/pulang.jpg', 'wb')
        decoded = base64.b64decode(imgstr)
        convert.write(decoded)
        convert.close()

        user_id = app.face.recognize("pulang.jpg")
        if user_id:
            tanggal = datetime.datetime.now().strftime("%B %d, %Y")
            jam_pulang = datetime.datetime.now().strftime("%I:%M%p")
            waktu_jadwal = datetime.time(8, 0, 0)
            print (waktu_jadwal.strftime("%T"))
            user = get_user_by_id(user_id)
            print(type(user))
            
            id_user1 = user["id"]

            getStatus = app.db.lihat_absensi("SELECT * FROM absensi WHERE tanggal_absen=? AND kar_id=?", [tanggal,id_user1])

            if getStatus is None:
                return error_handle('anda belum absen masuk')
            elif getStatus[7] == "yes":
                return error_handle('sudah absen pulang')
            else:
                stat_pulang = "yes"
                ket = "Done"
                updateAbsen = app.db.update_absensi('UPDATE absensi SET s_pulang=?, jam_pulang=?, keterangan=? WHERE kar_id=? AND tanggal_absen=?', [stat_pulang, jam_pulang, ket, id_user1, tanggal])

                # menampilkan preview absensi hanya pada hari ini                
                cek_tanggal = datetime.datetime.now().strftime("%B %d, %Y")        
                views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
                viewInJSON = json.dumps(views)
                return success_handle(viewInJSON)
        else:
            return error_handle("terjadi kesalahan")

# Run the app
if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'Thisissupossedtobesecret!'
    app.run()
