import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from flask import Blueprint, request, render_template, redirect, abort, session, url_for
from datetime import datetime
from utils.db import conectar_bd

lotes_bp = Blueprint('lotes', __name__, url_prefix='/lotes')

# === Helper para hora local MX (con fallback a tz local del sistema) ===
def mx_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Mexico_City"))
    except Exception:
        return datetime.now().astimezone()

def generar_id_lote():
    ahora = mx_now()
    fecha_hoy = ahora.date()
    fecha_lote = ahora.strftime('%y%m%d')

    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM public.produccion_lotes
        WHERE DATE(fecha_hora_registro) = %s
    """, (fecha_hoy,))
    contador = cur.fetchone()[0] + 1
    cur.close()
    conn.close()

    return f"{fecha_lote}-{contador:02d}"

@lotes_bp.route('/registrar', methods=['GET', 'POST'])
def registrar_lote():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        ahora = mx_now()
        hora = ahora.hour
        turno = 'M' if 6 <= hora < 14 else 'V' if 14 <= hora < 22 else 'N'

        id_lote = generar_id_lote()

        # --- MODIFICACIÓN INICIA ---
        bolsas_1kg = int(request.form.get('bolsas_1kg') or 0)
        bolsas_3kg = int(request.form.get('bolsas_3kg') or 0)
        bolsas_5kg = int(request.form.get('bolsas_5kg') or 0)
        bolsas_15kg = int(request.form.get('bolsas_15kg') or 0)
        
        total_kg = (bolsas_1kg * 1) + (bolsas_3kg * 3) + (bolsas_5kg * 5) + (bolsas_15kg * 15)
        # --- MODIFICACIÓN TERMINA ---
        
        observaciones = request.form.get('observaciones', '')

        # Tiempos en segundos (enteros, >= 0)
        def to_nonneg_int(val):
            try:
                v = int(val)
                return v if v >= 0 else 0
            except Exception:
                return 0

        tiempo_congelacion_s = to_nonneg_int(request.form.get('tiempo_congelacion_s', 0))
        tiempo_defrost_s     = to_nonneg_int(request.form.get('tiempo_defrost_s', 0))

        conn = conectar_bd()
        cur = conn.cursor()
        
        # --- MODIFICACIÓN INICIA ---
        cur.execute("""
            INSERT INTO public.produccion_lotes (
                id_lote, turno,
                bolsas_1kg, bolsas_3kg, bolsas_5kg, bolsas_15kg,
                total_kg,
                observaciones,
                fecha_hora_registro,
                tiempo_congelacion_s,
                tiempo_defrost_s
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            id_lote, turno,
            bolsas_1kg, bolsas_3kg, bolsas_5kg, bolsas_15kg,
            total_kg,
            observaciones,
            ahora,
            tiempo_congelacion_s,
            tiempo_defrost_s
        ))
        # --- MODIFICACIÓN TERMINA ---
        
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/lotes/ver')

    # GET → mostrar form
    id_lote_mostrar = generar_id_lote()
    now_str = mx_now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("registrar_lote.html",
                           id_lote_mostrar=id_lote_mostrar,
                           now_str=now_str)

@lotes_bp.route('/ver')
def ver_lotes():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha_filtrada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_filtrada = mx_now().date()
    else:
        fecha_filtrada = mx_now().date()

    conn = conectar_bd()
    cur = conn.cursor()
    
    # --- MODIFICACIÓN INICIA ---
    cur.execute("""
        SELECT
            id_lote,                -- 0
            fecha_hora_registro,    -- 1
            turno,                  -- 2
            bolsas_1kg,             -- 3
            bolsas_3kg,             -- 4
            bolsas_5kg,             -- 5
            bolsas_15kg,            -- 6
            total_kg,               -- 7
            tiempo_congelacion_s,   -- 8
            tiempo_defrost_s,       -- 9
            observaciones           -- 10
        FROM public.produccion_lotes
        WHERE DATE(fecha_hora_registro) = %s
        ORDER BY id_lote DESC
    """, (fecha_filtrada,))
    lotes = cur.fetchall()

    total_1kg = sum([l[3] for l in lotes])
    total_3kg = sum([l[4] for l in lotes])
    total_5kg = sum([l[5] for l in lotes])
    total_15kg = sum([l[6] for l in lotes])
    total_kg = sum([l[7] for l in lotes])
    # --- MODIFICACIÓN TERMINA ---

    cur.close()
    conn.close()

    return render_template(
        "ver_lotes.html",
        lotes=lotes,
        fecha=fecha_filtrada.strftime('%Y-%m-%d'),
        # --- MODIFICACIÓN INICIA ---
        total_1kg=total_1kg,
        total_3kg=total_3kg,
        # --- MODIFICACIÓN TERMINA ---
        total_5kg=total_5kg,
        total_15kg=total_15kg,
        total_kg=total_kg
    )