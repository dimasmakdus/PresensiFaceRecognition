from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from PIL import Image
import numpy as np
import os
import time
from datetime import date

from config.db import mycursor, mydb

# controller


def absensi_hari_ini():
    if session.get('user'):
        mycursor.execute(
            "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_date = '" + str(date.today()) + "' order by accs_added desc")
        data = mycursor.fetchall()

        return render_template('pages/absensi/absensihariini.html', data=data, navLink="absensihariini")
    else:
        return redirect("/login")


def absensi_pegawai():
    if session.get('user'):
        absensi_pegawai = ''
        absensi_bulan = ''
        absensi_tahun = ''
        jml_absen_masuk = 0
        jml_absen_pulang = 0
        isFilter = False
        pegawai_detail = []
        data = []

        is_report = request.args.get('report')
        if (is_report is not None):
            isFilter = True
            absensi_pegawai = request.args.get('absensi_pegawai')
            absensi_bulan = request.args.get('absensi_bulan')
            absensi_tahun = request.args.get('absensi_tahun')
            mycursor.execute(
                "select pegawai_name, jabatan_name from view_pegawai where pegawai_id = '"+absensi_pegawai+"'")
            pegawai_detail = mycursor.fetchone()

            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_type = 1 and accs_prsn = '"+absensi_pegawai+"' and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            jml_absen_masuk = len(mycursor.fetchall())
            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_type = 2 and accs_prsn = '"+absensi_pegawai+"' and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            jml_absen_pulang = len(mycursor.fetchall())

            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_prsn = '"+absensi_pegawai+"' and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            data = mycursor.fetchall()

        mycursor.execute(
            "select pegawai_id, pegawai_name, pegawai_status from pegawai where pegawai_status = 1 order by pegawai_name asc")
        pegawaiList = mycursor.fetchall()

        mycursor.execute(
            "SELECT DISTINCT DATE_FORMAT(accs_date,'%Y') AS tahun FROM view_absensi ORDER BY tahun DESC")
        tahunList = mycursor.fetchall()

        bulanList = [
            ('01', 'Januari'),
            ('02', 'Februari'),
            ('03', 'Maret'),
            ('04', 'April'),
            ('05', 'Mei'),
            ('06', 'Juni'),
            ('07', 'Juli'),
            ('08', 'Agustus'),
            ('09', 'September'),
            ('10', 'Oktober'),
            ('11', 'November'),
            ('12', 'Desember'),
        ]

        return render_template('pages/absensi/absensipegawai.html',
                               data=data,
                               absensi_pegawai=absensi_pegawai,
                               absensi_bulan=absensi_bulan,
                               absensi_tahun=absensi_tahun,
                               pegawai_detail=pegawai_detail,
                               jml_absen_masuk=jml_absen_masuk,
                               jml_absen_pulang=jml_absen_pulang,
                               isFilter=isFilter,
                               pegawaiList=pegawaiList,
                               bulanList=bulanList,
                               tahunList=tahunList,
                               navLink="absensipegawai")
    else:
        return redirect("/login")


def absensi_riwayat_table():
    if session.get('user'):
        absensi_bulan = ''
        absensi_tahun = ''
        jml_absen_masuk = 0
        jml_absen_pulang = 0
        isFilter = False
        data = []

        is_report = request.args.get('report')
        if (is_report is not None):
            isFilter = True
            absensi_bulan = request.args.get('absensi_bulan')
            absensi_tahun = request.args.get('absensi_tahun')

            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_type = 1 and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            jml_absen_masuk = len(mycursor.fetchall())
            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_type = 2 and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            jml_absen_pulang = len(mycursor.fetchall())

            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            data = mycursor.fetchall()

        mycursor.execute(
            "SELECT DISTINCT DATE_FORMAT(accs_date,'%Y') AS tahun FROM view_absensi ORDER BY tahun DESC")
        tahunList = mycursor.fetchall()

        bulanList = [
            ('01', 'Januari'),
            ('02', 'Februari'),
            ('03', 'Maret'),
            ('04', 'April'),
            ('05', 'Mei'),
            ('06', 'Juni'),
            ('07', 'Juli'),
            ('08', 'Agustus'),
            ('09', 'September'),
            ('10', 'Oktober'),
            ('11', 'November'),
            ('12', 'Desember'),
        ]

        return render_template('pages/absensi/riwayatabsensi.html',
                               data=data,
                               absensi_bulan=absensi_bulan,
                               absensi_tahun=absensi_tahun,
                               jml_absen_masuk=jml_absen_masuk,
                               jml_absen_pulang=jml_absen_pulang,
                               isFilter=isFilter,
                               bulanList=bulanList,
                               tahunList=tahunList,
                               navLink="riwayatabsensi")
    else:
        return redirect("/login")


def absensi_riwayat_userpegawai():
    if session.get('user'):
        pegawai_id = ''
        absensi_bulan = ''
        absensi_tahun = ''
        pegawai_detail = []
        jml_absen_masuk = 0
        jml_absen_pulang = 0
        isFilter = False
        data = []

        is_report = request.args.get('report')
        if (is_report is not None):
            isFilter = True
            pegawai_id = str(session.get('pegawai_id'))
            absensi_bulan = request.args.get('absensi_bulan')
            absensi_tahun = request.args.get('absensi_tahun')

            mycursor.execute(
                "select pegawai_name, jabatan_name from view_pegawai where pegawai_id = '"+pegawai_id+"'")
            pegawai_detail = mycursor.fetchone()

            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_type = 1 and accs_prsn = '"+pegawai_id+"' and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            jml_absen_masuk = len(mycursor.fetchall())
            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_type = 2 and accs_prsn = '"+pegawai_id+"' and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            jml_absen_pulang = len(mycursor.fetchall())

            mycursor.execute(
                "select accs_id, accs_prsn, pegawai_name, jabatan_name, accs_date, TIME_FORMAT(accs_added, '%H:%i:%s') as accs_added, accs_type from view_absensi where accs_prsn = '"+pegawai_id+"' and DATE_FORMAT(accs_date,'%m') = '"+absensi_bulan+"' AND DATE_FORMAT(accs_date,'%Y') = '"+absensi_tahun+"' order by accs_date desc")
            data = mycursor.fetchall()

        mycursor.execute(
            "SELECT DISTINCT DATE_FORMAT(accs_date,'%Y') AS tahun FROM view_absensi ORDER BY tahun DESC")
        tahunList = mycursor.fetchall()

        bulanList = [
            ('01', 'Januari'),
            ('02', 'Februari'),
            ('03', 'Maret'),
            ('04', 'April'),
            ('05', 'Mei'),
            ('06', 'Juni'),
            ('07', 'Juli'),
            ('08', 'Agustus'),
            ('09', 'September'),
            ('10', 'Oktober'),
            ('11', 'November'),
            ('12', 'Desember'),
        ]

        return render_template('pages/absensi/riwayatabsensi_pegawai.html',
                               data=data,
                               absensi_bulan=absensi_bulan,
                               absensi_tahun=absensi_tahun,
                               pegawai_detail=pegawai_detail,
                               jml_absen_masuk=jml_absen_masuk,
                               jml_absen_pulang=jml_absen_pulang,
                               isFilter=isFilter,
                               bulanList=bulanList,
                               tahunList=tahunList,
                               navLink="riwayatabsensi_pegawai")
    else:
        return redirect("/login")


def absensi_khusus():
    if session.get('user'):
        if session.get('access') == 1:
            mycursor.execute(
                "select absensi_khusus_id, absensi_khusus_judul, absensi_khusus_deskripsi, absensi_khusus_date, absensi_khusus_type, absensi_khusus_status, pegawai_id, pegawai_name, jabatan_name, absensi_khusus_updated_at from view_absensi_khusus order by absensi_khusus_updated_at desc")
            data = mycursor.fetchall()
        elif session.get('access') == 2:
            pegawai_id = str(session.get('pegawai_id'))
            mycursor.execute(
                "select absensi_khusus_id, absensi_khusus_judul, absensi_khusus_deskripsi, absensi_khusus_date, absensi_khusus_type, absensi_khusus_status, absensi_khusus_pegawai_id, absensi_khusus_updated_at from absensi_khusus where absensi_khusus_pegawai_id = '"+pegawai_id+"' order by absensi_khusus_updated_at desc")
            data = mycursor.fetchall()

        return render_template('pages/absensi/absensi_khusus.html', data=data, navLink="absensi_khusus")
    else:
        return redirect("/login")


def absensi_khusus_submit():
    if session.get('user'):
        absensi_khusus_judul = request.form.get('absensi_khusus_judul')
        absensi_khusus_deskripsi = request.form.get('absensi_khusus_deskripsi')
        absensi_khusus_date = request.form.get('absensi_khusus_date')
        absensi_khusus_type = request.form.get('absensi_khusus_type')
        absensi_khusus_status = 0
        absensi_khusus_pegawai_id = str(session.get('pegawai_id'))
        absensi_khusus_updated_at = date.today()

        mycursor.execute("""INSERT INTO `absensi_khusus` (`absensi_khusus_judul`, `absensi_khusus_deskripsi`, `absensi_khusus_date`, `absensi_khusus_status`, `absensi_khusus_type`, `absensi_khusus_pegawai_id`, `absensi_khusus_updated_at`) VALUES
                    ('{}', '{}', '{}', '{}', '{}', '{}', '{}')""".format(absensi_khusus_judul, absensi_khusus_deskripsi, absensi_khusus_date, absensi_khusus_status, absensi_khusus_type, absensi_khusus_pegawai_id, absensi_khusus_updated_at))
        mydb.commit()

        return redirect("/absensi_khusus")
    else:
        return redirect("/login")


def absensi_khusus_update_submit():
    if session.get('user'):
        absensi_khusus_id = request.form.get('absensi_khusus_id')
        absensi_khusus_status = request.form.get('absensi_khusus_status')
        absensi_khusus_updated_at = date.today()

        mycursor.execute("UPDATE absensi_khusus SET absensi_khusus_status = '{}', absensi_khusus_updated_at = '{}' WHERE absensi_khusus_id = '{}'".format(
            absensi_khusus_status, absensi_khusus_updated_at, absensi_khusus_id))

        mydb.commit()

        return redirect("/absensi_khusus")
    else:
        return redirect("/login")
