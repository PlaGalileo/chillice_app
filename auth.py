from flask import Blueprint, render_template, request, redirect, session, url_for, flash
import psycopg2
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def conectar_bd():
    return psycopg2.connect(
        dbname="chillice_db",
        user="postgres",
        password="Cocos121",
        host="localhost",
        port="5432"
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula'].strip().upper()
        password = request.form['password'].strip().encode('utf-8')

        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM public.rrhh_empleados WHERE id_empleado = %s", (matricula,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and bcrypt.checkpw(password, result[0].encode('utf-8')):
            session['usuario'] = matricula
            return redirect(url_for('menu'))
        else:
            flash("Matrícula o contraseña incorrecta", "error")

    return render_template("login.html")

@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('auth.login'))
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
import psycopg2
import bcrypt
from utils.db import conectar_bd 

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula'].strip().upper()
        password = request.form['password'].strip().encode('utf-8')

        conn = conectar_bd()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM public.rrhh_empleados WHERE id_empleado = %s", (matricula,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and bcrypt.checkpw(password, result[0].encode('utf-8')):
            session['usuario'] = matricula
            return redirect(url_for('menu'))
        else:
            flash("Matrícula o contraseña incorrecta", "error")

    return render_template("login.html")

@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('auth.login'))
