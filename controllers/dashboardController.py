from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor

# controller
def dashboard_index():
    if session.get('user'):
        mycursor.execute(
            "select count(*) from view_pegawai")
        countPegawai = mycursor.fetchone()[0]
        
        mycursor.execute(
            "select count(*) from access_history where accs_date = '" + str(date.today()) + "'")
        countAbsen = mycursor.fetchone()[0]

        count = [
            countPegawai,
            countAbsen
        ]

        return render_template('pages/dashboard/dashboard.html', count=count, navLink="dashboard")
    else:
        return redirect("/login")