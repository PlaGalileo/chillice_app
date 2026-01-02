# app/mermas.py
from flask import Blueprint, request, flash, render_template, redirect, session, url_for
from utils.db import conectar_bd
from datetime import datetime
# NUEVO: Importar la función de stock desde el módulo del dashboard
try:
    from proyeccion import get_current_stock
except ImportError:
    # Fallback por si el archivo aún se llama proyeccion.py pero el blueprint es dashboard
    from proyeccion import get_current_stock as get_stock_helper
    get_current_stock = get_stock_helper


mermas_bp = Blueprint('mermas', __name__, url_prefix='/mermas')


@mermas_bp.route('/registrar', methods=['GET', 'POST'])
def registrar_merma():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        conn = None
        try:
            tamano_kg = int(request.form['tamano_kg'])
            cantidad_bolsas = int(request.form['cantidad_bolsas'])
            comentarios = request.form.get('comentarios', '')
            
            if cantidad_bolsas <= 0:
                flash("La cantidad de bolsas debe ser mayor a 0", "danger")
                return render_template("registrar_merma.html")

            kg_merma = tamano_kg * cantidad_bolsas
            
            conn = conectar_bd()
            cur = conn.cursor()

            # --- NUEVA Validación de Stock Separado ---
            stock_general, stock_diego = get_current_stock(conn)
            
            is_diego_merma = 'diego' in (comentarios or '').lower()
            stock_a_validar = None
            
            if is_diego_merma:
                stock_a_validar = stock_diego
                stock_label = "Inventario Diego"
            else:
                stock_a_validar = stock_general
                stock_label = "Stock General"

            stock_disponible = stock_a_validar.get(str(tamano_kg), 0)

            if cantidad_bolsas > stock_disponible:
                flash(f"Error: No se puede registrar la merma. {stock_label} de {tamano_kg}kg solo tiene {stock_disponible} bolsas.", "danger")
                cur.close()
                conn.close()
                return render_template("registrar_merma.html")
            
            # --- Inserción ---
            cur.execute("""
                INSERT INTO mermas.registros 
                    (tamano_kg, cantidad_bolsas, kg_merma, comentarios, fecha_hora)
                VALUES (%s, %s, %s, %s, %s)
            """, (tamano_kg, cantidad_bolsas, kg_merma, comentarios, datetime.now()))
            
            conn.commit()
            flash("✅ Merma registrada con éxito", "success")
        
        except Exception as e:
            if conn: conn.rollback()
            flash(f"Error al registrar merma: {e}", "danger")
        
        finally:
            if conn:
                cur.close()
                conn.close()
        
        return redirect(url_for('mermas.ver_mermas'))

    return render_template("registrar_merma.html")

@mermas_bp.route('/ver')
def ver_mermas():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    
    conn = conectar_bd()
    cur = conn.cursor()
    
    # Filtro de mes
    month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    cur.execute("""
        SELECT id_merma, fecha_hora, tamano_kg, cantidad_bolsas, kg_merma, comentarios
        FROM mermas.registros
        WHERE to_char(fecha_hora, 'YYYY-MM') = %s
        ORDER BY fecha_hora DESC
    """, (month_str,))
    
    mermas = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("ver_mermas.html", mermas=mermas, month_str=month_str)