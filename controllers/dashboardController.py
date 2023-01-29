from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date
import json

from config.db import mycursor

# controller


def dashboard_index():
    if session.get('user'):
        if session.get('access') == 1:
            mycursor.execute(
                "select count(*) from view_pegawai")
            countPegawai = mycursor.fetchone()[0]

            mycursor.execute(
                "select count(*) from access_history where accs_date = '" + str(date.today()) + "'")
            countAbsen = mycursor.fetchone()[0]

            mycursor.execute(
                "select count(*) from access_history")
            countAbsenTotal = mycursor.fetchone()[0]

            mycursor.execute(
                "select count(*) from jabatan")
            countJabatan = mycursor.fetchone()[0]

            mycursor.execute(
                "select * from view_dashboard_jabatan")
            jmlPegawai = mycursor.fetchall()
            mycursor.execute(
                "select * from view_dashboard_absensi_khusus")
            jmlAbsensiKhusus = mycursor.fetchall()

            divisiTitle = []
            divisiCount = []
            for row in jmlPegawai:
                divisiTitle.append(row[1])
                divisiCount.append(row[2])

            count = [
                countPegawai,
                countAbsen,
                countAbsenTotal,
                countJabatan,
                json.dumps(divisiTitle),
                json.dumps(divisiCount),
                json.dumps(jmlAbsensiKhusus)
            ]
        elif session.get('access') == 2:
            pegawai_id = str(session.get('pegawai_id'))
            mycursor.execute(
                "select count(*) from access_history where accs_prsn = '"+pegawai_id+"' and accs_date = '" + str(date.today()) + "'")
            countAbsen = mycursor.fetchone()[0]

            mycursor.execute(
                "select count(*) from access_history where accs_prsn = '"+pegawai_id+"'")
            countAbsenTotal = mycursor.fetchone()[0]

            mycursor.execute(
                "select count(*) from absensi_khusus where absensi_khusus_pegawai_id = '"+pegawai_id+"'")
            countAbsensiKhusus = mycursor.fetchone()[0]
            count = [
                countAbsen,
                countAbsenTotal,
                countAbsensiKhusus,
            ]

        return render_template('pages/dashboard/dashboard.html', count=count, navLink="dashboard")
    else:
        return redirect("/login")
