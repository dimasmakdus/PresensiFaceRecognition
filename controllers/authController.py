from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from urllib.parse import urlparse
from datetime import date

from config.db import mycursor

# controller


def login():
    print(urlparse(request.base_url))
    if session.get('user'):
        return redirect("/dashboard")
    else:
        return render_template('pages/login/login.html')


def authentication():
    username = request.form.get('username')
    password = request.form.get('password')
    mycursor.execute(
        "select * from view_users where username = '"+str(username)+"'")

    user = mycursor.fetchone()
    data = user if user else []

    if len(data) > 0:
        if str(data[2]) == str(password):
            session['user'] = data[0]
            session['pegawai_id'] = data[7]
            session['full_name'] = data[6]
            session['access'] = data[3]
            session['access_name'] = data[9]
            return redirect('/dashboard')

        else:
            return render_template('pages/login/login.html', error='username dan password salah...!')
    else:
        return render_template('pages/login/login.html', error='username dan password salah...!')


def logout():
    session.pop('user', None)
    session.pop('access', None)
    session.pop('full_name', None)
    session.pop('access_name', None)
    return redirect('/login')
