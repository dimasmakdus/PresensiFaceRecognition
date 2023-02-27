from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
import cv2
from PIL import Image
import numpy as np
import os
import time
from datetime import date, datetime
from dotenv import dotenv_values
from config.db import *

env = dotenv_values(".env")

cnt = 0
pause_cnt = 0
justscanned = False

presensi_pegawai_id = 0
presensi_msg = ""
presensi_status = 0

img_frame_count = 0

resourcePath = env['HAARCASCADE_FRONTALFACE_DEFAULT']
datasetPath = env['DATASET']
deviceCamera = int(env['CAMERA_DEVICE'])

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Generate dataset >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def generate_dataset(nbr):
    face_classifier = cv2.CascadeClassifier(resourcePath)

    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        # scaling factor=1.3
        # Minimum neighbor = 5

        if faces == ():
            return None
        for (x, y, w, h) in faces:
            cropped_face = img[y:y + h, x:x + w]
        return cropped_face

    cap = cv2.VideoCapture(deviceCamera)

    mycursor.execute("select ifnull(max(img_id), 0) from img_dataset")
    row = mycursor.fetchone()
    lastid = row[0]

    img_id = lastid
    max_imgid = img_id + 100
    count_img = 0

    global img_frame_count

    while True:
        ret, img = cap.read()
        if face_cropped(img) is not None:
            count_img += 1
            img_id += 1
            face = cv2.resize(face_cropped(img), (200, 200))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

            img_frame_count = count_img
            file_name_path = "dataset/" + nbr + "." + str(img_id) + ".jpg"
            cv2.imwrite(file_name_path, face)
            cv2.putText(face, str(count_img), (50, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

            mycursor.execute("""INSERT INTO `img_dataset` (`img_id`, `img_person`) VALUES
                                ('{}', '{}')""".format(img_id, nbr))
            mydb.commit()

            frame = cv2.imencode('.jpg', face)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            if cv2.waitKey(1) == 13 or int(img_id) == int(max_imgid):
                break
                cap.release()
                cv2.destroyAllWindows()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Train Classifier >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def train_classifier(nbr):
    dataset_dir = datasetPath

    path = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir)]
    faces = []
    ids = []

    # Add photo dataset per ID pegawai
    for image in path:
        img = Image.open(image).convert('L')
        imageNp = np.array(img, 'uint8')
        id = int(os.path.split(image)[1].split(".")[1])

        faces.append(imageNp)
        ids.append(id)
    ids = np.array(ids)

    # Train the classifier and save
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    clf.write("classifier.xml")

    return redirect('/datapegawai')


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Face Recognition >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def face_recognition():  # generate frame by frame from camera
    def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, clf):
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        features = classifier.detectMultiScale(
            gray_image, scaleFactor, minNeighbors)

        coords = []

        for (x, y, w, h) in features:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            id, pred = clf.predict(gray_image[y:y + h, x:x + w])
            confidence = int(100 * (1 - pred / 300))

            mycursor.execute("select b.pegawai_name "
                             "  from img_dataset a "
                             "  left join pegawai b on a.img_person = b.pegawai_id "
                             " where img_id = " + str(id))
            s = mycursor.fetchone()

            # print(confidence)
            # if confidence >= 85 and confidence <= 90 and (s is not None):
            if confidence >= int(env['CONFIDENCE_START']) and confidence <= int(env['CONFIDENCE_END']) and (s is not None):
                s = '' + ''.join(s)
                cv2.putText(img, s, (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
            else:
                cv2.putText(img, "TIDAK DIKENALI", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)

            coords = [x, y, w, h]
        return coords

    def recognize(img, clf, faceCascade):
        coords = draw_boundary(img, faceCascade, 1.1, 10,
                               (255, 255, 0), "Face", clf)
        return img

    faceCascade = cv2.CascadeClassifier(resourcePath)
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier.xml")

    wCam, hCam = 500, 400

    cap = cv2.VideoCapture(deviceCamera)
    cap.set(3, wCam)
    cap.set(4, hCam)

    while True:
        ret, img = cap.read()
        img = recognize(img, clf, faceCascade)

        frame = cv2.imencode('.jpg', img)[1].tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        key = cv2.waitKey(1)
        if key == 27:
            break


def presensi_recognition():  # generate frame by frame from camera
    def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, clf):
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        features = classifier.detectMultiScale(
            gray_image, scaleFactor, minNeighbors)

        global justscanned
        global pause_cnt

        global presensi_pegawai_id
        global presensi_msg
        global presensi_status

        pause_cnt += 1

        coords = []

        for (x, y, w, h) in features:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            id, pred = clf.predict(gray_image[y:y + h, x:x + w])
            confidence = int(100 * (1 - pred / 300))

            # print(confidence)
            # if confidence >= 85 and confidence <= 90 and not justscanned:
            if confidence >= int(env['CONFIDENCE_START']) and confidence <= int(env['CONFIDENCE_END']) and not justscanned:
                global cnt
                cnt += 1

                n = (100 / 30) * cnt
                # w_filled = (n / 100) * w
                w_filled = (cnt / 30) * w

                cv2.putText(img, str(int(n))+' %', (x + 20, y + h + 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (153, 255, 255), 2, cv2.LINE_AA)

                cv2.rectangle(img, (x, y + h + 40),
                              (x + w, y + h + 50), color, 2)
                cv2.rectangle(img, (x, y + h + 40), (x + int(w_filled),
                              y + h + 50), (153, 255, 255), cv2.FILLED)

                mycursor.execute("select a.img_person, b.pegawai_name, c.jabatan_name "
                                 "  from img_dataset a "
                                 "  left join pegawai b on a.img_person = b.pegawai_id "
                                 "  left join jabatan c on b.pegawai_jabatan_id = c.jabatan_id"
                                 " where img_id = " + str(id))
                row = mycursor.fetchone()

                if row:
                    pnbr = row[0]
                    pname = row[1]
                    pskill = row[2]

                if int(cnt) == 30:
                    cnt = 0

                    currentDateAndTime = datetime.now()
                    currentTime = currentDateAndTime.strftime("%H:%M:%S")

                    # Get Jam Masuk
                    mycursor.execute(
                        "select * from jamkerja where jamkerja_id = 1")
                    jam_masuk = mycursor.fetchone()

                    # Get Jam Masuk
                    mycursor.execute(
                        "select * from jamkerja where jamkerja_id = 2")
                    jam_pulang = mycursor.fetchone()

                    # Check Absen Pagi
                    mycursor.execute(
                        "select accs_date from access_history where accs_prsn = '" + str(pnbr) + "' and accs_date = '" + str(date.today()) + "' and accs_added between '"+str(jam_masuk[2])+"' and '"+str(jam_masuk[3])+"'")
                    absen_masuk = mycursor.fetchone()
                    check_absen_masuk = absen_masuk if absen_masuk else []

                    # Check Absen Sore
                    mycursor.execute(
                        "select accs_date from access_history where accs_prsn = '" + str(pnbr) + "' and accs_date = '" + str(date.today()) + "' and accs_added between '"+str(jam_pulang[2])+"' and '"+str(jam_pulang[3])+"'")
                    absen_pulang = mycursor.fetchone()
                    check_absen_pulang = absen_pulang if absen_pulang else []

                    # Check Absen Hari Ini
                    mycursor.execute(
                        "select accs_date from access_history where accs_prsn = '" + str(pnbr) + "' and accs_date = '" + str(date.today()) + "'")
                    absen_harini = mycursor.fetchone()
                    check_absen_harini = absen_harini if absen_harini else []

                    if datetime.strptime(str(currentTime), "%H:%M:%S") >= datetime.strptime(str(jam_masuk[2]), "%H:%M:%S") and datetime.strptime(str(currentTime), "%H:%M:%S") <= datetime.strptime(str(jam_masuk[3]), "%H:%M:%S"):

                        if len(check_absen_masuk) > 0:
                            print("SUDAH ABSEN PAGI HARI INI")

                            presensi_pegawai_id = pnbr
                            presensi_msg = ". . . Sudah Absen Pagi Hari Ini . . ."
                            presensi_status = 1
                        else:
                            mycursor.execute(
                                "insert into access_history (accs_date, accs_prsn, accs_type) values('"+str(date.today())+"', '" + pnbr + "', '"+str(jam_masuk[0])+"')")
                            mydb.commit()
                            print("BELUM ABSEN PAGI HARI INI")

                            presensi_pegawai_id = pnbr
                            presensi_msg = ". . . Berhasil Absen Pagi Hari Ini . . ."
                            presensi_status = 2

                    elif datetime.strptime(str(currentTime), "%H:%M:%S") >= datetime.strptime(str(jam_pulang[2]), "%H:%M:%S") and datetime.strptime(str(currentTime), "%H:%M:%S") <= datetime.strptime(str(jam_pulang[3]), "%H:%M:%S"):

                        if len(check_absen_pulang) > 0:
                            print("SUDAH ABSEN SORE HARI INI")

                            presensi_pegawai_id = pnbr
                            presensi_msg = ". . . Sudah Absen Sore Hari Ini . . ."
                            presensi_status = 1
                        else:
                            mycursor.execute(
                                "insert into access_history (accs_date, accs_prsn, accs_type) values('"+str(date.today())+"', '" + pnbr + "', '"+str(jam_pulang[0])+"')")
                            mydb.commit()
                            print("BELUM ABSEN SORE HARI INI")

                            presensi_pegawai_id = pnbr
                            presensi_msg = ". . . Berhasil Absen Sore Hari Ini . . ."
                            presensi_status = 2
                    else:
                        print("BELUM WAKTUNYA ABSEN")
                        presensi_pegawai_id = pnbr
                        presensi_msg = ". . . BELUM WAKTUNYA ABSEN . . ."
                        presensi_status = 1

                    cv2.putText(img, pname + ' | ' + pskill, (x - 10, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (153, 255, 255), 2, cv2.LINE_AA)
                    time.sleep(1)

                    justscanned = True
                    pause_cnt = 0

            else:
                if not justscanned:
                    cv2.putText(img, 'TIDAK DIKENALI', (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
                else:
                    cv2.putText(
                        img, ' ', (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

                if pause_cnt > 80:
                    justscanned = False

            coords = [x, y, w, h]
        return coords

    def recognize(img, clf, faceCascade):
        coords = draw_boundary(img, faceCascade, 1.1, 10,
                               (255, 255, 0), "Face", clf)
        return img

    faceCascade = cv2.CascadeClassifier(resourcePath)
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier.xml")

    wCam, hCam = 400, 400

    cap = cv2.VideoCapture(deviceCamera)
    cap.set(3, wCam)
    cap.set(4, hCam)

    while True:
        ret, img = cap.read()
        img = recognize(img, clf, faceCascade)

        frame = cv2.imencode('.jpg', img)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

        key = cv2.waitKey(1)
        if key == 27:
            break


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CONTROLLER >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def pegawai_table():
    if session.get('user'):
        mycursor.execute(
            "select pegawai_id, pegawai_name, jabatan_name, pegawai_status, pegawai_added, is_img_dataset, pegawai_jabatan_id from view_pegawai order by pegawai_id desc")
        data = mycursor.fetchall()

        mycursor.execute(
            "select * from jabatan order by jabatan_id desc")
        jabatanList = mycursor.fetchall()

        statusPegawai = [
            ('0', 'Tidak Aktif'),
            ('1', 'Aktif'),
        ]

        mycursor.execute(
            "select ifnull(max(pegawai_id) + 1, 101) from pegawai")
        row = mycursor.fetchone()
        nbr = row[0]

        return render_template('pages/master/datapegawai/datapegawai.html',
                               data=data,
                               navLink="datapegawai",
                               jabatanList=jabatanList,
                               statusPegawai=statusPegawai,
                               newnbr=int(nbr)
                               )
    else:
        return redirect("/login")


def pegawai_fr():
    if session.get('user'):
        return render_template('pages/master/datapegawai/fr_page.html', checkdata=checkdataset())
    else:
        return redirect("/login")


def addprsn_submit():
    prsnbr = request.form.get('txtnbr')
    prsname = request.form.get('txtname')
    prsskill = request.form.get('optskill')
    status = request.form.get('status_pegawai')
    username_pegawai = request.form.get('username_pegawai')
    password_pegawai = request.form.get('password_pegawai')

    mycursor.execute("""INSERT INTO `pegawai` (`pegawai_id`, `pegawai_name`, `pegawai_jabatan_id`, `pegawai_status`) VALUES
                    ('{}', '{}', '{}', '{}')""".format(prsnbr, prsname, prsskill, status))

    mycursor.execute("""INSERT INTO `users` (`username`, `password`, `id_user_role`, `status`, `full_name`, `user_pegawai_id`) VALUES
                    ('{}', '{}', '{}', '{}', '{}', '{}')""".format(username_pegawai, password_pegawai, 2, status, prsname, prsnbr))

    mydb.commit()

    return redirect("/datapegawai")
    # return redirect(url_for('vfdataset_page', prs=prsnbr))


def updateprsn_submit():
    pegawai_id = request.form.get('pegawai_id')
    nama_pegawai = request.form.get('nama_pegawai')
    jabatan_id = request.form.get('jabatan_id')
    status = request.form.get('status_pegawai')

    mycursor.execute("UPDATE pegawai SET pegawai_name = '{}', pegawai_jabatan_id = '{}', pegawai_status = '{}' WHERE pegawai_id = '{}'".format(
        nama_pegawai, jabatan_id, status, pegawai_id))

    mydb.commit()
    alert = [
        "success",
        "Data Pegawai berhasil diubah"
    ]

    return redirect('/datapegawai')


def delete_pegawai(nbr):
    # Hapus db pegawai
    mycursor.execute(
        "DELETE FROM pegawai WHERE pegawai_id = "+str(nbr))

    # Hapus db img_dataset
    mycursor.execute(
        "DELETE FROM img_dataset WHERE img_person = "+str(nbr))

    # Hapus file dataset per ID pegawai
    datasetFile = [os.path.join(datasetPath, f)
                   for f in os.listdir(datasetPath)]
    for image in datasetFile:
        id = int(os.path.split(image)[1].split(".")[0])
        if (id == int(nbr)):
            os.remove(image)

    mydb.commit()

    return redirect('/datapegawai')


def vfdataset_page(prs):
    mycursor.execute(
        "select * from pegawai where pegawai_id = "+str(prs)+" limit 1")
    pegawai = mycursor.fetchone()

    mycursor.execute(
        "select * from img_dataset where img_person = "+str(prs)+" limit 1")
    checkDataset = mycursor.fetchone()

    if (checkDataset is not None) and (len(checkDataset) > 0):
        # Hapus db img_dataset
        mycursor.execute(
            "DELETE FROM img_dataset WHERE img_person = "+str(prs))

        # Hapus file dataset per ID pegawai
        datasetFile = [os.path.join(datasetPath, f)
                       for f in os.listdir(datasetPath)]
        for image in datasetFile:
            id = int(os.path.split(image)[1].split(".")[0])
            if (id == int(prs)):
                os.remove(image)

        mydb.commit()

    return render_template('pages/master/datapegawai/gendataset.html', prs=prs, pegawai=pegawai)


def vidfeed_dataset(nbr):
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(generate_dataset(nbr), mimetype='multipart/x-mixed-replace; boundary=frame')


def video_feed():
    # Cam Test Recognition
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(face_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


def video_presensi():
    # Cam Presensi Recognition
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(presensi_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


def countTodayScan():
    mycursor.execute("select count(*) "
                     "  from access_history "
                     " where accs_date = curdate() ")
    row = mycursor.fetchone()
    rowcount = row[0]

    return jsonify({'rowcount': rowcount})


def countImgFrameScan():
    global img_frame_count
    framecount = img_frame_count

    return jsonify({'framecount': framecount})


def loadData():

    global presensi_pegawai_id
    global presensi_msg
    global presensi_status

    id = presensi_pegawai_id
    msg = presensi_msg
    status = presensi_status

    response = []

    if (status != 0):
        mycursor.execute(
            "SELECT pegawai_name, jabatan_name FROM view_pegawai WHERE pegawai_id = "+str(id)+" limit 1")
        data = mycursor.fetchone()
        response = {
            'status': status,
            'msg': msg,
            'data': {
                'pegawai_id': id,
                'pegawai_name': data[0],
                'jabatan_name': data[1]
            }
        }
    else:
        response = {
            'status': status,
            'msg': msg,
            'data': {
                'pegawai_name': '',
                'jabatan_name': '',
            }
        }

    presensi_pegawai_id = 0
    presensi_msg = ""
    presensi_status = 0
    return jsonify(response=response)
