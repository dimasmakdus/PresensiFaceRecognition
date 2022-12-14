from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor, mydb

# controller


def jabatan_table():
    if session.get('user'):
        mycursor.execute(
            "select * from jabatan order by jabatan_id desc")
        data = mycursor.fetchall()

        return render_template('pages/master/datajabatan/datajabatan.html', data=data, navLink="datajabatan")
    else:
        return redirect("/login")


def jabatan_submit():
    nama_jabatan = request.form.get('nama_jabatan')
    status = 1

    mycursor.execute("""INSERT INTO `jabatan` (`jabatan_name`, `jabatan_status`) VALUES
                    ('{}', '{}')""".format(nama_jabatan, status))
    mydb.commit()

    return redirect("/datajabatan")


def jabatan_update_submit():
    jabatan_id = request.form.get('jabatan_id')
    nama_jabatan = request.form.get('nama_jabatan')

    mycursor.execute("UPDATE jabatan SET jabatan_name = '{}' WHERE jabatan_id = '{}'".format(
        nama_jabatan, jabatan_id))

    mydb.commit()

    return redirect("/datajabatan")


def delete_jabatan(nbr):
    # Hapus db jabatan
    mycursor.execute(
        "DELETE FROM jabatan WHERE jabatan_id = "+str(nbr))

    mydb.commit()

    return redirect('/datajabatan')
