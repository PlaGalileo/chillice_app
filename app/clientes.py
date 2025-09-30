# clientes.py refactorizado para usar templates separados
from flask import Blueprint, request, flash, render_template, redirect, session, url_for
from utils.db import conectar_bd

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

@clientes_bp.route('/registrar', methods=['GET', 'POST'])
def registrar_cliente():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST': 
        conn = conectar_bd()
        cur = conn.cursor()

        # Obtener el último id_cliente con el prefijo 'ICE' y extraer el número
        cur.execute("""
            SELECT id_cliente FROM clientes
            WHERE id_cliente LIKE 'ICE%%'
            ORDER BY id_cliente DESC
            LIMIT 1
        """)
        ultimo_id = cur.fetchone()
        if ultimo_id:
            numero = int(ultimo_id[0][3:]) + 1  # extrae el número después de 'ICE' y suma 1
        else:
            numero = 1

        nuevo_id = f"ICE{numero:03d}"  # formato ICE001, ICE002, etc.

        # Ahora sí insertamos incluyendo id_cliente
        cur.execute("""
            INSERT INTO public.clientes (
                id_cliente, categoria, nombre, telefono, correo,
                calle, numero_exterior, numero_interior, codigo_postal, colonia,
                municipio, estado, rfc, notas
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            nuevo_id,
            request.form['categoria'],
            request.form['nombre'],
            request.form['telefono'],
            request.form['correo'],
            request.form['calle'],
            request.form['numero_exterior'],
            request.form['numero_interior'],
            request.form['codigo_postal'],
            request.form['colonia'],
            request.form['municipio'],
            request.form['estado'],
            request.form['rfc'],
            request.form['notas']
        ))

        conn.commit()
        cur.close()
        conn.close()

        flash("✅ Cliente registrado con éxito", "success")
        return redirect(url_for('clientes.registrar_cliente'))


    return render_template("registrar_cliente.html")

@clientes_bp.route('/ver')
def ver_clientes():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    filtro = request.args.get('filtro', '').lower()
    conn = conectar_bd()
    cur = conn.cursor()
    if filtro:
        cur.execute("""
            SELECT id_cliente, nombre, telefono, correo, codigo_postal, municipio, estado
            FROM public.clientes
            WHERE LOWER(nombre) LIKE %s OR LOWER(telefono) LIKE %s OR CAST(id_cliente AS TEXT) LIKE %s
            ORDER BY id_cliente DESC
        """, (f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"))
    else:
        cur.execute("""
            SELECT id_cliente, nombre, telefono, correo, codigo_postal, municipio, estado
            FROM public.clientes
            ORDER BY id_cliente DESC
        """)
    clientes = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("ver_clientes.html", clientes=clientes, filtro=filtro)
