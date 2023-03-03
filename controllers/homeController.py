from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date
from urllib.parse import urlparse

from config.db import mycursor, checkdataset

# controller


def home_index():
    hostName = urlparse(request.base_url).hostname
    if (hostName == '127.0.0.1' or hostName == 'localhost'):
        #  """Video streaming home page."""
        mycursor.execute("select a.accs_id, a.accs_prsn, b.pegawai_name, b.pegawai_jabatan_id, a.accs_added "
                         "  from access_history a "
                         "  left join pegawai b on a.accs_prsn = b.pegawai_id "
                         " where a.accs_date = curdate() "
                         " order by 1 desc")
        data = mycursor.fetchall()
        return render_template('index.html', data=data, checkdata=checkdataset())
    else:
        return redirect('/login')

def absensi2():
    hostName = urlparse(request.base_url).hostname
    if (hostName == '127.0.0.1' or hostName == 'localhost'):
        #  """Video streaming home page."""
        mycursor.execute("select a.accs_id, a.accs_prsn, b.pegawai_name, b.pegawai_jabatan_id, a.accs_added "
                         "  from access_history a "
                         "  left join pegawai b on a.accs_prsn = b.pegawai_id "
                         " where a.accs_date = curdate() "
                         " order by 1 desc")
        data = mycursor.fetchall()
        return render_template('absensi2.html', data=data, checkdata=checkdataset())
    else:
        return redirect('/login')