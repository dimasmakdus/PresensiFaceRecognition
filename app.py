from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify, send_file
from controllers.authController import login, authentication, logout
from controllers.homeController import home_index
from controllers.dashboardController import dashboard_index
from controllers.pegawaiController import pegawai_table, pegawai_fr, train_classifier, addprsn_submit, updateprsn_submit, delete_pegawai, vfdataset_page, vidfeed_dataset, video_feed, video_presensi, countTodayScan, countImgFrameScan, loadData
from controllers.jabatanController import jabatan_table, jabatan_submit, jabatan_update_submit, delete_jabatan
from controllers.userController import user_table, user_submit, user_update_submit, delete_user
from controllers.accessController import access_table, access_submit, access_update_submit, delete_access
from controllers.jamkerjaController import jamkerja_table, jamkerja_update_submit
from controllers.absensiController import absensi_riwayat_table
import os
from dotenv import dotenv_values

env = dotenv_values(".env")

app = Flask(__name__)
app.secret_key = os.urandom(32)

@app.route('/getDatasetImg/<string:imgName>')
def getDatasetImg(imgName):
    filePath = env['DATASET']
    return send_file(os.path.join(filePath, imgName))

# Home
app.route('/', methods=['GET'])(home_index)

# Login
app.route('/login')(login)
app.route("/authentication", methods=["POST"])(authentication)
app.route("/logout")(logout)

# Dashboard
app.route("/dashboard")(dashboard_index)

# Data Pegawai
app.route('/datapegawai')(pegawai_table)
app.route('/fr_page')(pegawai_fr)
app.route('/train_classifier/<nbr>')(train_classifier)
app.route('/addprsn_submit', methods=['POST'])(addprsn_submit)
app.route('/updateprsn_submit', methods=['POST'])(updateprsn_submit)
app.route('/delete_pegawai/<nbr>')(delete_pegawai)
app.route('/vfdataset_page/<prs>')(vfdataset_page)
app.route('/vidfeed_dataset/<nbr>')(vidfeed_dataset)
app.route('/video_feed')(video_feed)
app.route('/video_presensi')(video_presensi)
app.route('/countTodayScan')(countTodayScan)
app.route('/countImgFrameScan')(countImgFrameScan)
app.route('/loadData', methods=['GET', 'POST'])(loadData)

# Data Jabatan
app.route("/datajabatan")(jabatan_table)
app.route('/jabatan_submit', methods=['POST'])(jabatan_submit)
app.route('/jabatan_update_submit', methods=['POST'])(jabatan_update_submit)
app.route('/delete_jabatan/<nbr>')(delete_jabatan)

# Riwayat Absensi
app.route("/riwayatabsensi")(absensi_riwayat_table)

# Akun
# Pengguna
app.route("/pengguna")(user_table)
app.route('/user_submit', methods=['POST'])(user_submit)
app.route('/user_update_submit', methods=['POST'])(user_update_submit)
app.route('/delete_user/<nbr>')(delete_user)

# Hak Akses
app.route("/hakakses")(access_table)
app.route('/access_submit', methods=['POST'])(access_submit)
app.route('/access_update_submit', methods=['POST'])(access_update_submit)
app.route('/delete_access/<nbr>')(delete_access)

# Pengaturan
# Jam Kerja
app.route("/jamkerja")(jamkerja_table)
app.route('/jamkerja_update_submit', methods=['POST'])(jamkerja_update_submit)

if __name__ == "__main__":
    app.run(host=env['FLASK_HOST'], port=int(
        env['FLASK_PORT']), debug=env['FLASK_DEBUG'])
