from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor, mydb

# controller


def user_table():
    if session.get('user'):
        mycursor.execute(
            "select id, username, full_name, role_name, id_user_role, status from view_users order by id desc")
        data = mycursor.fetchall()

        mycursor.execute(
            "select * from roles where role_status = 1 order by role_id desc")
        accessList = mycursor.fetchall()

        statusUser = [
            (0, 'Tidak Aktif'),
            (1, 'Aktif'),
        ]

        return render_template('pages/akun/pengguna/pengguna.html',
                               data=data,
                               navLink="pengguna",
                               accessList=accessList,
                               statusUser=statusUser)
    else:
        return redirect("/login")


def user_submit():
    username = request.form.get('username')
    id_user_role = request.form.get('id_user_role')
    status = request.form.get('status')
    full_name = request.form.get('full_name')
    defaultPassword = "Password"

    mycursor.execute("""INSERT INTO `users` (`username`, `password`, `id_user_role`, `status`, `full_name`) VALUES
                    ('{}', '{}', '{}', '{}', '{}')""".format(username, defaultPassword, id_user_role, status, full_name))
    mydb.commit()

    return redirect("/pengguna")


def user_update_submit():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    id_user_role = request.form.get('id_user_role')
    status = request.form.get('status')
    full_name = request.form.get('full_name')

    mycursor.execute("UPDATE users SET username = '{}', id_user_role = '{}', status = '{}', full_name = '{}'  WHERE id = '{}'".format(
        username, id_user_role, status, full_name, user_id))

    mydb.commit()

    return redirect("/pengguna")


def delete_user(nbr):
    # Hapus db user
    mycursor.execute(
        "DELETE FROM users WHERE id = "+str(nbr))

    mydb.commit()

    return redirect('/pengguna')
