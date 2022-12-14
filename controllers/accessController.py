from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor, mydb

# controller


def access_table():
    if session.get('user'):
        mycursor.execute(
            "select * from roles order by role_id desc")
        data = mycursor.fetchall()

        statusAkses = [
            (0, 'Tidak Aktif'),
            (1, 'Aktif'),
        ]

        return render_template('pages/akun/akses/hakakses.html', data=data, navLink="hakakses", statusAkses=statusAkses)
    else:
        return redirect("/login")


def access_submit():
    role_name = request.form.get('role_name')
    role_status = request.form.get('role_status')

    mycursor.execute("""INSERT INTO `roles` (`role_name`, `role_status`) VALUES
                    ('{}', '{}')""".format(role_name, role_status))
    mydb.commit()

    return redirect("/hakakses")


def access_update_submit():
    role_id = request.form.get('role_id')
    role_name = request.form.get('role_name')
    role_status = request.form.get('role_status')

    mycursor.execute("UPDATE roles SET role_name = '{}', role_status = '{}'  WHERE role_id = '{}'".format(
        role_name, role_status, role_id))

    mydb.commit()

    return redirect("/hakakses")


def delete_access(nbr):
    mycursor.execute(
        "DELETE FROM roles WHERE role_id = "+str(nbr))

    mydb.commit()

    return redirect('/hakakses')
