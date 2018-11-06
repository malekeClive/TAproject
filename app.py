# --MODULE-- #
from flask import Flask, json, Response, request, render_template, url_for, session, logging, flash, redirect, jsonify, make_response, send_from_directory
import sqlite3
from wtforms import Form, StringField, TextField, TextAreaField, PasswordField, validators, IntegerField, FileField
from wtforms.fields.html5 import DateField, TelField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename
from werkzeug.datastructures import CombinedMultiDict
import calendar
import os
from os import path, getcwd
import time
from ta import Database
from face import Face
from functools import wraps
import base64
import re
import datetime
import pdfkit


app = Flask(__name__)

app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.db = Database()
app.face = Face(app)

# --SUCCESS FUNCTION HANDLING
def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)

# --ERROR FUNCTION HANDLING-- #
def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)

# --FUNCTION GET ABSENSI ID-- #
def get_absen_id(absen_id):
    absen = {}
    results = app.db.select(
        'SELECT * FROM absensi WHERE id = ?', [absen_id])
        
    for row in results:
        absen = {
            "id": row[0],
            "tanggal_absen": row[1],
            "name": row[2],
            "jam_masuk": row[3],
            "jam_pulang": row[4],
            "keterangan": row[5],
            "s_masuk": row[6],
            "s_pulang": row[7],
            "kar_id": row[8],
            "bulan_tahun": row[9],
            "created": row[10]
        }
    if 'id' in absen:
        return absen
    return None

# --FUNCTION GET KARYAWAN-- #
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

# --FUNCTION DELETE USER-- #
def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM karyawan WHERE karyawan.id = ?', [user_id])
    # also delete all faces with user id
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])
    # and also delete attendance data from absensi table
    app.db.delete('DELETE FROM absensi WHERE absensi.kar_id = ?', [user_id])

# --FUNCTION PREVIEW ABSENSI HARI INI-- #
def preview_absen_now():
    cek_tanggal = datetime.datetime.now().strftime("%d-%m-%Y")
    views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
    return views

# --FUNCTION PREVIEW KARYAWAN-- #
def preview_karyawan():
    views = app.db.query('SELECT * FROM karyawan')
    return views


class RegisterForm(Form):
    adminId = StringField('admin Id', [validators.Length(min=1, max=50)])
    username = StringField('nama', [validators.Length(min=1, max=50)])
    email = StringField('email', [validators.Length(min=1, max=50)])
    password = PasswordField('password', [validators.DataRequired(), validators.EqualTo('confirm', message='Password do not match')])
    confirm = PasswordField('confirm password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        admin_id = form.adminId.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        app.db.insert("INSERT INTO admin(admin_id, username, email, password) VALUES (?,?,?,?)", (admin_id, username, email, password))

        return success_handle('berhasil')
    else:
        return render_template('register.html', form=form)
    

# --MENU LOGIN ADMIN-- #
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

# --CEK AUTENTIKASI SEBELUM MASUK URL LAIN-- #
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login!', 'danger') # pesan jika tidak ada autentikasi masuk
            return redirect(url_for('login'))
    return wrap

# --MENU DATA ADMIN-- #
@app.route('/data_admin')
@is_logged_in
def dataAdmin():
    cek_admin = app.db.lihat_absensi('SELECT * FROM admin')
    return render_template('data_admin.html', cek_admin=cek_admin) 

# --MENU EDIT ADMIN-- #
class admin_edit_form(Form):
    adminId = StringField('Admin Id', [validators.DataRequired()])
    name = StringField('Nama', [validators.DataRequired()])
    email = StringField('Email', [validators.DataRequired()])

    oldpassword = PasswordField('Password Lama', [validators.DataRequired()], filters = [lambda x: x or None])    
    newpassword = PasswordField('Password Baru', [validators.EqualTo('confirm', message='Password tidak sama')])
    confirm = PasswordField('Konfirmasi Password Baru')

@app.route('/edit_admin', methods=['GET', 'POST', 'PUT'])
@is_logged_in
def editAdmin():
    form = admin_edit_form(request.form)
    # pass_form = password_form(request.form)
    if request.method == 'POST':
        new_data = app.db.lihat_karyawan('SELECT * FROM admin')
        
        admin_id = form.adminId.data
        name = form.name.data
        email = form.email.data
        oldpass = form.oldpassword.data

        app.db.update_absensi('UPDATE admin SET admin_id = ?, username = ?, email = ?', [admin_id, name, email])

        if oldpass != None:
            if sha256_crypt.verify(oldpass, new_data[4]):
                newpass = sha256_crypt.encrypt(form.newpassword.data)

                app.db.update_absensi('UPDATE admin SET password = ?', [newpass])
                return redirect(url_for('dataAdmin'))
            else:
                flash('invalid old password')
                return render_template('edit_admin.html', form=form)
        else:
            return redirect(url_for('dataAdmin'))
    else:
        get_data_admin = app.db.lihat_karyawan('SELECT * FROM admin')

        form.adminId.data = get_data_admin[1]
        form.name.data = get_data_admin[2]
        form.email.data = get_data_admin[3]
        return render_template('edit_admin.html', form=form)

# --LOGOUT ADMIN-- #
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# route for user profile
# @app.route('/api/users/<int:absen_id>', methods=['GET', 'DELETE'])
# def user_profile(absen_id):
#     if request.method == 'GET':
#         user = get_absen_id(absen_id)
#         if user:
#             return success_handle(json.dumps(user), 200)
#         else:
#             return error_handle("User not found", 404)
    # if request.method == 'DELETE':
    #     delete_user_by_id(user_id)
    #     return success_handle(json.dumps({"deleted": True}))

# --MENU CETAK LAPORAN-- #
@app.route('/cetakLaporan', methods=['GET','POST'])
@is_logged_in
def date():
    getDate = request.form['bulan']
    print(getDate)
    yr = int(getDate[0:4])
    mn = int(getDate[5:])
    views = app.db.query('SELECT * FROM absensi WHERE strftime("%Y-%m", created)=?', [getDate,])
    if views:
        
        weekday_count = 0
        cal = calendar.Calendar()

        for week in cal.monthdayscalendar(yr, mn):
            for i, day in enumerate(week):
                # not this month's day or a weekend
                if day == 0 or i == 6:
                    continue
                # or some other control if desired...
                weekday_count += 1
        # print (weekday_count)

        jumlah = app.db.query('SELECT absensi.kar_id, absensi.name, count(kar_id) FROM absensi where strftime("%Y-%m", absensi.created)=? GROUP BY kar_id', [getDate,])

        rekap = []
        for row in jumlah:
            hasil = weekday_count - row[2]
            conv = str(hasil)
            rekap.append({'id':row[0], 'nama':row[1], 'jumlah absen':row[2], 'hasil':conv})
            
        rendered = render_template('rekapLaporan.html', views=views, jumlah=jumlah, hasil=rekap)
        css = ['static/stylesheets/style.css']
        pdf = pdfkit.from_string(rendered, False, css=css)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=output.pdf'

        return response
    else:
        flash('tidak ada data', 'danger')
        return redirect(url_for('dataAbsensi'))

# --MENU EDIT ABSENSI-- #
class edit_absensi(Form):
    name = StringField('Nama Karyawan', [validators.Length(min=1, max=50)])
    tanggalAbsen = StringField('Tanggal Absen', [validators.Length(min=1, max=25)])
    keterangan = StringField('Keterangan', [validators.Length(min=0, max=50)])

@app.route('/edit_keterangan/<int:absen_id>', methods=['GET', 'POST'])
@is_logged_in
def edit_ket_absensi(absen_id):
    row_absensi = app.db.lihat_karyawan('SELECT * FROM absensi WHERE id = ?', [absen_id])
    
    form = edit_absensi(request.form)

    form.name.data = row_absensi[2]
    form.tanggalAbsen.data = row_absensi[1]
    form.keterangan.data = row_absensi[5]

    if request.method == 'POST' and form.validate():

        set_ket = request.form.get('comp_select')

        app.db.update_absensi("UPDATE absensi SET keterangan=? WHERE id=?", (set_ket, absen_id))
        
        flash('berhasil ubah keterangan', 'success')

        return redirect(url_for('dataAbsensi'))
    return render_template('edit_absensi.html', form=form, data=[{'name':'Done'}, {'name':'izin'}, {'name':'sakit'}])

# --HAPUS KARYAWAN-- #
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
        # app.face.del_user(user_id)
        delete_user_by_id(user_id)
        return redirect(url_for('karyawanData'))

# --DASHBOARD MENU-- #
@app.route('/dashboard')
@is_logged_in
def dashboard():
    views_absensi = preview_absen_now()
    views_karyawan = preview_karyawan()

    jmlh_kar = len(views_karyawan)
    jmlh_abs = len(views_absensi)
    sisa_kar = jmlh_kar - jmlh_abs
    return render_template('dashboard.html', views_abs=jmlh_abs, views_kar=jmlh_kar, views_sisa=sisa_kar)

# --MENU DATA ABSENSI-- #
@app.route('/dataAbsensi')
@is_logged_in
def dataAbsensi():
    views = app.db.query('SELECT * FROM absensi')
    views.reverse()

    if views:
        return render_template('dataAbsensi.html', views=views)
    else:
        flash('Tidak ada data absen hari ini', 'success')
        return render_template('dataAbsensi.html')
    return render_template('dataAbsensi.html', views=views)

# --MENU DATA KARYAWAN-- #
@app.route('/dataKaryawan')
@is_logged_in
def dataKaryawan():
    return render_template('dataKaryawan.html')

@app.route('/karyawanData')
@is_logged_in
def karyawanData():
    views = app.db.query('SELECT * FROM karyawan')
    return render_template('dataKaryawan.html', views=views)

class TambahKaryawanForm(Form):
    name = StringField('Nama', [validators.Length(min=1, max=50)])
    telpon = IntegerField('Telpon', [validators.required('Number Only')])
    alamat = StringField('Alamat', [validators.Length(min=1, max=50)])
    image = FileField('File Gambar', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images Only!')
    ])

# --TAMBAH KARYAWAN BARU-- #
@app.route('/tambah_karyawan', methods=['GET', 'POST'])
@is_logged_in
def tambahKaryawan():
    form = TambahKaryawanForm(CombinedMultiDict((request.files, request.form)))

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        telpon = request.form['telpon']
        alamat = request.form['alamat']
        foto = request.files['image']

        filename = secure_filename(foto.filename)
        trained_storage = path.join(app.config['storage'], 'trained')
        foto.save(path.join(trained_storage, filename))

        created = int(time.time())
        user_id = app.db.insert('INSERT INTO karyawan(name, telpon, alamat, created) values(?,?,?,?)', [name, telpon, alamat, created])

        if user_id:
            print("User saved in data", name, user_id)
            # simpan data wajah
            face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) values(?,?,?)', [user_id, filename, created])

            if face_id:
                app.face.load_one()
                flash('data baru telah dimasukkan', 'success')
                return redirect(url_for('karyawanData'))
            else:
                return render_template('tambah_karyawan.html', form=form)
    else:
        return render_template('tambah_karyawan.html', form=form)


    # if 'file' not in request.files:
    #     return render_template('tambah_karyawan.html')
    # else:
    #     # views = app.db.query('SELECT * FROM faces')
    #     # for rows in views:
    #     #     nama_file = rows[2]
    #     #     print(nama_file)
    #     #     print(type(nama_file))
        
    #     file = request.files['file']

    #     if file.mimetype not in app.config['file_allowed']:
    #         return error_handle("We are only allow upload file with *.png , *.jpg")
    #     # elif nama_file == file:
    #     #     return error_handle(['nama file sudah ada'])
    #     else:
    #         # request field
    #         name = request.form['name']
    #         telpon = request.form['telpon']
    #         alamat = request.form['alamat']

    #         # simpan ke storage
    #         print("File is allowed and will be saved in ", app.config['storage'])
    #         filename = secure_filename(file.filename)
    #         trained_storage = path.join(app.config['storage'], 'trained')
    #         file.save(path.join(trained_storage, filename))

    #         # simpan ke database
    #         created = int(time.time())
    #         user_id = app.db.insert('INSERT INTO karyawan(name, telpon, alamat, created) values(?,?,?,?)', [name, telpon, alamat, created])
                        
    #         if user_id:

    #             print("User saved in data", name, user_id)
    #             # simpan data wajah
    #             face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) values(?,?,?)',
    #                                         [user_id, filename, created])

    #             if face_id:
    #                 app.face.load_one()
    #                 # flash('data baru telah dimasukkan', 'success')
    #                 # return render_template('dataKaryawan.html')
    #                 return success_handle('Data Karyawan Baru berhasil dimasukkan')
    #             else:
    #                 return error_handle("Gagal menyimpan data wajah")

    #         else:
    #             return error_handle("Terjadi kesalahan")

# --EDIT USER KARYAWAN-- #
class edit_karyawan(Form):
    name = StringField('Nama Karyawan', [validators.DataRequired()])
    telpon = IntegerField('Telpon', [validators.required('Number Only')])
    alamat = TextAreaField('Alamat', [validators.DataRequired()])
    image = FileField('File Gambar', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images Only!')])

@app.route('/getPhoto/<filename>')
def send_image(filename):
    return send_from_directory(path.join(app.config['storage'], 'trained'), filename)    

@app.route('/edit_karyawan/<int:user_id>', methods=['GET', 'POST', 'PUT'])
@is_logged_in
def edit_user_karyawan(user_id):
    row_karyawan = app.db.lihat_karyawan('SELECT * FROM karyawan WHERE karyawan.id = ?', [user_id])
    row_faces = app.db.lihat_karyawan('SELECT * FROM faces WHERE faces.user_id = ?', [user_id])
    image_names = os.listdir('./storage/trained')

    form = edit_karyawan(CombinedMultiDict((request.files, request.form)))

    form.name.data = row_karyawan[1]
    form.telpon.data = row_karyawan[2]
    form.alamat.data = row_karyawan[3]
    get_photo = image_names.index(row_faces[2])
    gets = image_names[get_photo]

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        telpon = request.form['telpon']
        alamat = request.form['alamat']
        foto = request.files['image']

        created = int(time.time())

        uid = app.db.simpan_edit_karyawan("UPDATE karyawan SET name=?, telpon=?, alamat=? WHERE id=?", (name, telpon, alamat, user_id))
        app.db.simpan_edit_karyawan("UPDATE absensi SET name= (SELECT karyawan.name FROM karyawan WHERE karyawan.id=?) where kar_id=? ", (user_id, user_id,))

        if foto != None and uid:
            filename = secure_filename(foto.filename)
            trained_storage = path.join(app.config['storage'], 'trained')
            foto.save(path.join(trained_storage, filename))

            app.db.simpan_edit_karyawan("UPDATE faces SET user_id=?, filename=?, created=? WHERE user_id=?", [user_id, filename, created, user_id])
            print("update foto")
        
            app.face.load_custom(user_id)

            flash('Data karyawan berhasil diubah', 'success')

            return redirect(url_for('karyawanData'))
        else:
            print("tidak update foto")
            flash('Data karyawan berhasil diubah', 'success')
            return redirect(url_for('karyawanData'))

    return render_template('edit_karyawan.html', form=form, image_names=gets)


# ---BAGIAN KARYAWAN---#
@app.route('/absen')
def absen():
    return render_template('absensi.html')

@app.route('/absenMasuk', methods=['GET', 'POST'])
def absensiMasuk():
    if request.method == 'GET':
        cek_tanggal = datetime.datetime.now().strftime("%d-%m-%Y")
        views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
        viewInJSON = json.dumps(views)
        if views:
            return success_handle(viewInJSON)
        else:
            return error_handle(['terjadi kesalahan'])
    else:
        # convert gambar yang didapatkan dari base64 menjadi .jpg
        image_b64 = request.values[('imageBase64')]
        imgstr = re.search(r'data:image/png;base64,(.*)',image_b64).group(1)
        convert = open('storage/unknown/output.jpg', 'wb')
        decoded = base64.b64decode(imgstr)
        convert.write(decoded)
        convert.close()

        user_ids = app.face.recognize("output.jpg")  # mendapatkan data wajah
        user_filtered = list(filter(lambda x: x != 'unknown', user_ids))  # filter jika data wajah yang masuk tidak ada di database
        isSuccess = False

        #cek kalau wajah2 ketemu
        if len(user_filtered) != 0:
        # loop setiap wajah yang didapatkan
            for i in user_filtered:
                get_user = get_user_by_id(i)
                tanggal = datetime.datetime.now().strftime("%d-%m-%Y")
                jam_masuk = datetime.datetime.now().strftime("%I:%M%p")
                bln_thn = datetime.datetime.now().strftime("%B/%Y")
                
                getStatus = app.db.lihat_absensi("SELECT * FROM absensi WHERE tanggal_absen=? AND kar_id=?", [tanggal,i])

                # jika belum absen masuk
                if getStatus is None:
                    stat_masuk = "Yes"
                    j_pulang = "No"
                    s_pulang = "No"
                    ket = "Belum absen pulang"

                    # simpan data absensi
                    simpan_absen = app.db.insert('INSERT INTO absensi(tanggal_absen, name, jam_masuk, jam_pulang, keterangan, s_masuk, s_pulang, kar_id, bulan_tahun) VALUES(?,?,?,?,?,?,?,?,?)', [tanggal, get_user["name"], jam_masuk, j_pulang, ket, stat_masuk, s_pulang, i, bln_thn])
                    isSuccess = True
                else:
                    isSuccess = False
            if isSuccess:
                # menampilkan preview absensi hanya hari ini       
                cek_tanggal = datetime.datetime.now().strftime("%d-%m-%Y")
                views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
                viewInJSON = json.dumps(views)
                return success_handle(viewInJSON)
            else:
                return error_handle('sudah ambil absen')
        return error_handle("tidak ada wajah")

# cek_tanggal = datetime.datetime.now().strftime("%B %d, %Y")
#                 views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
#                 viewInJSON = json.dumps(views)

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
        cek_tanggal = datetime.datetime.now().strftime("%d-%m-%Y")        
        views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
        viewInJSON = json.dumps(views)
        if views:
            return success_handle(viewInJSON)
        else:
            return error_handle('terjadi kesalahan')
    else:
        image_b64 = request.values[('imageBase64')]
        imgstr = re.search(r'data:image/png;base64,(.*)',image_b64).group(1)
        convert = open('storage/unknown/output.jpg', 'wb')
        decoded = base64.b64decode(imgstr)
        convert.write(decoded)
        convert.close()

        user_ids = app.face.recognize("output.jpg")  # mendapatkan data wajah
        user_filtered = list(filter(lambda x: x != 'unknown', user_ids))  # filter jika data wajah yang masuk tidak ada di database
        isSuccess = False        
        
        if len(user_filtered) != 0:
            # loop setiap wajah yang didapatkan
            for i in user_filtered:
                get_user = get_user_by_id(i)
                tanggal = datetime.datetime.now().strftime("%d-%m-%Y")
                jam_pulang = datetime.datetime.now().strftime("%I:%M%p")

                getStatus = app.db.lihat_absensi("SELECT * FROM absensi WHERE tanggal_absen=? AND kar_id=?", [tanggal,i])

                stat_pulang = "yes"
                ket = "Done"
                # update data absen
                updateAbsen = app.db.update_absensi('UPDATE absensi SET s_pulang=?, jam_pulang=?, keterangan=? WHERE kar_id=? AND tanggal_absen=?', [stat_pulang, jam_pulang, ket, i, tanggal])
                isSuccess = True

            if isSuccess:
                # menampilkan preview absensi hanya hari ini
                cek_tanggal = datetime.datetime.now().strftime("%d-%m-%Y")
                views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
                viewInJSON = json.dumps(views)
                return success_handle(viewInJSON)
            else:
                return error_handle('tidak ada data wajah')
        return error_handle("belum absen masuk")

        # user_id = app.face.recognize("pulang.jpg")
        # if user_id:
        #     tanggal = datetime.datetime.now().strftime("%B %d, %Y")
        #     jam_pulang = datetime.datetime.now().strftime("%I:%M%p")
        #     waktu_jadwal = datetime.time(8, 0, 0)
        #     print (waktu_jadwal.strftime("%T"))
        #     user = get_user_by_id(user_id)
        #     print(type(user))
            
        #     id_user1 = user["id"]

        #     getStatus = app.db.lihat_absensi("SELECT * FROM absensi WHERE tanggal_absen=? AND kar_id=?", [tanggal,id_user1])

        #     if getStatus is None:
        #         return error_handle('anda belum absen masuk')
        #     elif getStatus[7] == "yes":
        #         return error_handle('sudah absen pulang')
        #     else:
        #         stat_pulang = "yes"
        #         ket = "Done"
        #         updateAbsen = app.db.update_absensi('UPDATE absensi SET s_pulang=?, jam_pulang=?, keterangan=? WHERE kar_id=? AND tanggal_absen=?', [stat_pulang, jam_pulang, ket, id_user1, tanggal])

        #         # menampilkan preview absensi hanya pada hari ini                
        #         cek_tanggal = datetime.datetime.now().strftime("%B %d, %Y")        
        #         views = app.db.query('SELECT * FROM absensi WHERE tanggal_absen=?', [cek_tanggal])
        #         viewInJSON = json.dumps(views)
        #         return success_handle(viewInJSON)
        # else:
        #     return error_handle("terjadi kesalahan")

# --RUN THE APP-- #
if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'Thisissupossedtobesecret!'
    app.run(debug=True)
