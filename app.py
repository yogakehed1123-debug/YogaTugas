from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import mysql.connector
from fpdf import FPDF
import os

app = Flask(__name__)
app.secret_key = "yoga123"

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': "",
    'database': 'db_rapot_yoga'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)


def generate_id_nilai():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_nilai FROM nilai_yoga ORDER BY id_nilai DESC LIMIT 1")
    last = cursor.fetchone()

    if last:
        num = int(last[0][2:]) + 1
        new_id = f"NP{num:03d}"
    else:
        new_id = "NP001"

    cursor.close()
    conn.close()
    return new_id

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # dropdown kelas
    cursor.execute("SELECT DISTINCT kelas FROM siswa_yoga")
    kelas_list = cursor.fetchall()

    # query utama
    query = """
        SELECT
            a.id_nilai,
            a.nis,
            b.kelas,
            b.nama,
            c.nama_mapel,
            a.nilai_tugas,
            a.nilai_uts,
            a.nilai_uas,
            a.deskripsi,
            a.semester,
            a.tahun_ajaran,
            ROUND((a.nilai_tugas + a.nilai_uts + a.nilai_uas) / 3, 2) AS nilai_akhir
        FROM nilai_yoga a
        JOIN siswa_yoga b ON a.nis = b.nis
        JOIN mapel_yoga c ON a.id_mapel = c.id_mapel
        WHERE 1=1
    """

    params = []

    if request.method == 'POST':
        kelas = request.form.get('kelas')
        semester = request.form.get('semester')
        tahun_ajaran = request.form.get('tahun_ajaran')

        if kelas:
            query += " AND b.kelas = %s"
            params.append(kelas)

        if semester:
            query += " AND a.semester = %s"
            params.append(semester)

        if tahun_ajaran:
            query += " AND a.tahun_ajaran = %s"
            params.append(tahun_ajaran)

    cursor.execute(query, params)
    siswa = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        siswa=siswa,
        kelas_list=kelas_list
    )

@app.route('/Tambah', methods=['GET', 'POST'])
def Tambah():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nis, nama, kelas FROM siswa_yoga")
    dropdown_siswa = cursor.fetchall()

    cursor.execute("SELECT id_mapel, nama_mapel FROM mapel_yoga")
    dropdown_m = cursor.fetchall()

    if request.method == 'POST':
        id_nilai = generate_id_nilai()
        nis = request.form['nis']
        id_mapel = request.form['id_mapel']
        nilai_tugas = float(request.form['nilai_tugas'])
        nilai_uts = float(request.form['nilai_uts'])
        nilai_uas = float(request.form['nilai_uas'])
        semester = request.form['semester']
        tahun_ajaran = request.form['tahun_ajaran']

        # Hapus kolom deskripsi dari query
        sql = """
            INSERT INTO nilai_yoga
            (id_nilai, nis, id_mapel, nilai_tugas, nilai_uts, nilai_uas, semester, tahun_ajaran)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(sql, (
            id_nilai, nis, id_mapel, nilai_tugas,
            nilai_uts, nilai_uas, semester, tahun_ajaran
        ))

        conn.commit()
        flash("Data berhasil ditambahkan")

        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    cursor.close()
    conn.close()
    return render_template('Tambah.html',
                           dropdown_siswa=dropdown_siswa,
                           dropdown_m=dropdown_m)


@app.route('/filter', methods=['GET', 'POST'])
def filter_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # dropdown siswa
    cursor.execute("SELECT kelas FROM siswa_yoga")
    siswa = cursor.fetchall()

    hasil = []

    if request.method == 'POST':
        kelas = request.form['kelas']
        semester = request.form['semester']
        tahun_ajaran = request.form['tahun_ajaran']

        query = """
            SELECT
                a.id_nilai,
                a.nis,
                b.kelas,
                b.nama,
                c.nama_mapel,
                a.nilai_tugas,
                a.nilai_uts,
                a.nilai_uas,
                a.deskripsi,
                a.semester,
                a.tahun_ajaran,
                ROUND((a.nilai_tugas + a.nilai_uts + a.nilai_uas) / 3, 2) AS nilai_akhir
            FROM nilai_yoga a
            JOIN siswa_yoga b ON a.nis = b.nis
            JOIN mapel_yoga c ON a.id_mapel = c.id_mapel
            WHERE a.nis=%s AND a.semester=%s AND a.tahun_ajaran=%s
        """

        cursor.execute(query, (kelas, semester, tahun_ajaran))
        hasil = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        siswa=siswa,
        hasil=hasil
    )


@app.route('/edit/<id_nilai>')
def edit_form(id_nilai):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM nilai_yoga WHERE id_nilai=%s", (id_nilai,))
    siswa_edit = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('update.html', siswa_edit=siswa_edit)

@app.route('/update', methods=['POST'])
def update():
    nis = request.form['nis']
    nilai_tugas = float(request.form['nilai_tugas'])
    nilai_uts = float(request.form['nilai_uts'])
    nilai_uas = float(request.form['nilai_uas'])
    semester = request.form['semester']
    tahun_ajaran = request.form['tahun_ajaran']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Hapus kolom deskripsi dari update query
    cursor.execute("""
        UPDATE nilai_yoga SET
            nilai_tugas=%s,
            nilai_uts=%s,
            nilai_uas=%s,
            semester=%s,
            tahun_ajaran=%s
        WHERE nis=%s
    """, (
        nilai_tugas, nilai_uts, nilai_uas,
        semester, tahun_ajaran, nis
    ))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Data berhasil diupdate")
    return redirect(url_for('index'))


@app.route('/Hapus/<id_nilai>')
def Hapus(id_nilai):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM nilai_yoga WHERE id_nilai=%s", (id_nilai,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Data berhasil dihapus")
    return redirect(url_for('index'))

def get_deskripsi(nilai_akhir):
    nilai_akhir = float(nilai_akhir)

    if nilai_akhir >= 90:
        return "Sangat baik, pertahankan prestasi."
    elif nilai_akhir >= 80:
        return "Baik, tingkatkan konsistensi belajar."
    elif nilai_akhir >= 70:
        return "Cukup baik, perlu lebih giat latihan."
    elif nilai_akhir >= 60:
        return "Kurang, perlu bimbingan dan belajar lebih rutin."
    else:
        return "Sangat kurang, harus belajar lebih keras dan perlu pendampingan."


@app.route('/cetak/<nis>/<semester>/<tahun_ajaran>')
def cetak(nis, semester, tahun_ajaran):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.nis,
            b.nama,
            c.nama_mapel,
            a.nilai_tugas,
            a.nilai_uts,
            a.nilai_uas,
            a.deskripsi,
            ROUND((a.nilai_tugas + a.nilai_uts + a.nilai_uas) / 3, 2) AS nilai_akhir,
            a.semester,
            a.tahun_ajaran
        FROM nilai_yoga a
        JOIN siswa_yoga b ON a.nis = b.nis
        JOIN mapel_yoga c ON a.id_mapel = c.id_mapel
        WHERE a.nis = %s
    """, (nis,))

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        return "Data siswa tidak ditemukan"

    # ambil identitas dari baris pertama
    nama = data[0]['nama']
    semester = data[0]['semester']
    tahun_ajaran = data[0]['tahun_ajaran']

    pdf = FPDF()
    pdf.add_page()

    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font('DejaVu', '', 12)

    pdf.cell(0, 10, 'LAPORAN HASIL BELAJAR SISWA', ln=True, align='C')
    pdf.ln(5)

    pdf.set_font('DejaVu', '', 10)
    pdf.cell(30, 8, 'NIS', 0)
    pdf.cell(5, 8, ':', 0)
    pdf.cell(0, 8, str(nis), ln=True)

    pdf.cell(30, 8, 'Nama', 0)
    pdf.cell(5, 8, ':', 0)
    pdf.cell(0, 8, str(nama), ln=True)

    pdf.cell(30, 8, 'Semester', 0)
    pdf.cell(5, 8, ':', 0)
    pdf.cell(0, 8, str(semester), ln=True)

    pdf.cell(30, 8, 'Tahun Ajaran', 0)
    pdf.cell(5, 8, ':', 0)
    pdf.cell(0, 8, str(tahun_ajaran), ln=True)

    pdf.ln(5)

    pdf.cell(10, 8, 'No', 1)
    pdf.cell(50, 8, 'Mata Pelajaran', 1)
    pdf.cell(25, 8, 'Nilai Akhir', 1)
    pdf.cell(50, 8, 'Deskripsi', 1)
    pdf.ln()

    no = 1
    for row in data:
        pdf.cell(10, 8, str(no), 1)
        pdf.cell(50, 8, row['nama_mapel'], 1)
        pdf.cell(25, 8, str(row['nilai_akhir']), 1)
        pdf.cell(50, 8, str(row['deskripsi']), 1)
        pdf.ln()
        no += 1

    pdf_bytes = pdf.output(dest='S').encode('latin-1')

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=rapot_{nis}.pdf'
    return response



if __name__ == '__main__':
    app.run(debug=True)
