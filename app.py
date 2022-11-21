from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
import mysql.connector
import cv2
from PIL import Image
import numpy as np
import os
import time
from datetime import date

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

cnt = 0
pause_cnt = 0
justscanned = False

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="presensi_mki"
)
mycursor = mydb.cursor()

resourcePath = "/Users/dimasmohammadmakdus/PycharmProjects/PresensiFaceRecognition/resources/haarcascade_frontalface_default.xml"
datasetPath = "/Users/dimasmohammadmakdus/PycharmProjects/PresensiFaceRecognition/dataset"

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

    cap = cv2.VideoCapture(0)

    mycursor.execute("select ifnull(max(img_id), 0) from img_dataset")
    row = mycursor.fetchone()
    lastid = row[0]

    img_id = lastid
    max_imgid = img_id + 100
    count_img = 0

    while True:
        ret, img = cap.read()
        if face_cropped(img) is not None:
            count_img += 1
            img_id += 1
            face = cv2.resize(face_cropped(img), (200, 200))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

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
@app.route('/train_classifier/<nbr>')
def train_classifier(nbr):
    dataset_dir = datasetPath

    path = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir)]
    faces = []
    ids = []

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

    return redirect('/')


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

            mycursor.execute("select b.prs_name "
                             "  from img_dataset a "
                             "  left join prs_mstr b on a.img_person = b.prs_nbr "
                             " where img_id = " + str(id))
            s = mycursor.fetchone()
            s = '' + ''.join(s)

            # print(confidence)
            if confidence >= 85 and confidence <= 90:
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

    cap = cv2.VideoCapture(0)
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

        pause_cnt += 1

        coords = []

        for (x, y, w, h) in features:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            id, pred = clf.predict(gray_image[y:y + h, x:x + w])
            confidence = int(100 * (1 - pred / 300))

            # print(confidence)
            if confidence >= 85 and confidence <= 90 and not justscanned:
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

                mycursor.execute("select a.img_person, b.prs_name, b.prs_skill "
                                 "  from img_dataset a "
                                 "  left join prs_mstr b on a.img_person = b.prs_nbr "
                                 " where img_id = " + str(id))
                row = mycursor.fetchone()

                if row:
                    pnbr = row[0]
                    pname = row[1]
                    pskill = row[2]

                if int(cnt) == 30:
                    cnt = 0

                    mycursor.execute(
                        "select accs_date from accs_hist where accs_prsn = '" + str(pnbr) + "' and accs_date = '" + str(date.today()) + "'")

                    data = mycursor.fetchone()
                    checkdate = data if data else []

                    if len(checkdate) > 0:
                        print("SUDAH ABSEN HARI INI")
                    else:
                        mycursor.execute(
                            "insert into accs_hist (accs_date, accs_prsn) values('"+str(date.today())+"', '" + pnbr + "')")
                        mydb.commit()
                        print("BELUM ABSEN HARI INI")

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

    cap = cv2.VideoCapture(0)
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


def checkdataset():
    mycursor.execute(
        "select * from prs_mstr")
    person = mycursor.fetchall()

    mycursor.execute(
        "select * from img_dataset")
    imgdata = mycursor.fetchall()

    checkdata = False
    if len(person) > 0 or len(imgdata) > 0:
        checkdata = True

    return checkdata


@app.route('/')
def home():
    #  """Video streaming home page."""
    mycursor.execute("select a.accs_id, a.accs_prsn, b.prs_name, b.prs_skill, a.accs_added "
                     "  from accs_hist a "
                     "  left join prs_mstr b on a.accs_prsn = b.prs_nbr "
                     " where a.accs_date = curdate() "
                     " order by 1 desc")
    data = mycursor.fetchall()

    return render_template('index.html', data=data, checkdata=checkdataset())


@app.route('/datapegawai')
def datapegawai():
    if session.get('user'):
        mycursor.execute(
            "select prs_nbr, prs_name, prs_skill, prs_active, prs_added from prs_mstr")
        data = mycursor.fetchall()

        return render_template('datapegawai.html', data=data)
    else:
        return redirect("/login")


@app.route('/addprsn')
def addprsn():
    if session.get('user'):
        mycursor.execute("select ifnull(max(prs_nbr) + 1, 101) from prs_mstr")
        row = mycursor.fetchone()
        nbr = row[0]
        # print(int(nbr))

        return render_template('addprsn.html', newnbr=int(nbr))
    else:
        return redirect("/login")


@app.route('/addprsn_submit', methods=['POST'])
def addprsn_submit():
    prsnbr = request.form.get('txtnbr')
    prsname = request.form.get('txtname')
    prsskill = request.form.get('optskill')

    mycursor.execute("""INSERT INTO `prs_mstr` (`prs_nbr`, `prs_name`, `prs_skill`) VALUES
                    ('{}', '{}', '{}')""".format(prsnbr, prsname, prsskill))
    mydb.commit()

    # return redirect(url_for('home'))
    return redirect(url_for('vfdataset_page', prs=prsnbr))


@app.route('/vfdataset_page/<prs>')
def vfdataset_page(prs):
    return render_template('gendataset.html', prs=prs)


@app.route('/vidfeed_dataset/<nbr>')
def vidfeed_dataset(nbr):
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(generate_dataset(nbr), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed')
def video_feed():
    # Cam Test Recognition
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(face_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_presensi')
def video_presensi():
    # Cam Presensi Recognition
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(presensi_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/fr_page')
def fr_page():
    if session.get('user'):
        return render_template('fr_page.html', checkdata=checkdataset())
    else:
        return redirect("/login")


@app.route('/countTodayScan')
def countTodayScan():
    mycursor.execute("select count(*) "
                     "  from accs_hist "
                     " where accs_date = curdate() ")
    row = mycursor.fetchone()
    rowcount = row[0]

    return jsonify({'rowcount': rowcount})


@app.route('/loadData', methods=['GET', 'POST'])
def loadData():
    mycursor.execute("select a.accs_id, a.accs_prsn, b.prs_name, b.prs_skill, date_format(a.accs_added, '%H:%i:%s') "
                     "  from accs_hist a "
                     "  left join prs_mstr b on a.accs_prsn = b.prs_nbr "
                     " where a.accs_date = curdate() "
                     " order by accs_added desc")
    data = mycursor.fetchall()

    return jsonify(response=data)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route("/authentication", methods=["POST"])
def authentication():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        mycursor.execute(
            "select * from users where username = '"+str(username)+"'")

        user = mycursor.fetchone()
        data = user if user else []

        print(data[6])
        if len(data) > 0:
            if str(data[2]) == str(password):
                session['user'] = data[0]
                session['full_name'] = data[6]
                return redirect('/datapegawai')

            else:
                return render_template('login.html', error='username dan password salah...!')
        else:
            return render_template('login.html', error='username dan password salah...!')

    except Exception as error:
        return jsonify({
            'status': 'error',
            'message': str(error)
        })


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
