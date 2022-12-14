from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor, mydb

# controller


def jamkerja_table():
    if session.get('user'):
        mycursor.execute(
            "select jamkerja_id, jamkerja_name, TIME_FORMAT(jamkerja_start, '%H:%i:%s') as jamkerja_start, TIME_FORMAT(jamkerja_end, '%H:%i:%s') as jamkerja_end from jamkerja order by jamkerja_id asc")
        data = mycursor.fetchall()

        return render_template('pages/pengaturan/jamkerja/jamkerja.html', data=data, navLink="jamkerja")
    else:
        return redirect("/login")


def jamkerja_update_submit():
    jamkerja_id = request.form.get('jamkerja_id')
    jamkerja_name = request.form.get('jamkerja_name')
    jamkerja_start = request.form.get('jamkerja_start')
    jamkerja_end = request.form.get('jamkerja_end')

    mycursor.execute("UPDATE jamkerja SET jamkerja_name = '{}', jamkerja_start = '{}', jamkerja_end = '{}'  WHERE jamkerja_id = '{}'".format(
        jamkerja_name, jamkerja_start, jamkerja_end, jamkerja_id))

    mydb.commit()

    return redirect("/jamkerja")
