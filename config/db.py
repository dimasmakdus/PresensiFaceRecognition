import mysql.connector
from dotenv import dotenv_values

env = dotenv_values(".env")

mydb = mysql.connector.connect(
    host = env['DB_HOST'],
    user = env['DB_USERNAME'],
    passwd = env["DB_PASSWORD"],
    database = env['DB_DATABASE']
)
mycursor = mydb.cursor()

# check dataset
def checkdataset():
    mycursor.execute(
        "select * from pegawai")
    person = mycursor.fetchall()

    mycursor.execute(
        "select * from img_dataset")
    imgdata = mycursor.fetchall()

    checkdata = False
    if len(person) > 0 or len(imgdata) > 0:
        checkdata = True

    return checkdata