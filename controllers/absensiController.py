from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor, mydb

# controller


def absensi_riwayat_table():
    if session.get('user'):
        mycursor.execute(
            "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added from view_absensi order by accs_added desc")
        data = mycursor.fetchall()

        return render_template('pages/absensi/riwayatabsensi.html', data=data, navLink="riwayatabsensi")
    else:
        return redirect("/login")
