from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from utils.db import conectar_bd
from datetime import datetime

# ==========================================
# Blueprint
# ==========================================
ges_cotizaciones_bp = Blueprint(
    "ges_cotizaciones", __name__, url_prefix="/cotizaciones"
)

# ==========================================
# Vista principal: lista de cotizaciones
# ==========================================
@ges_cotizaciones_bp.route("/")
def ver_cotizaciones():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    conn = conectar_bd()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT c.id_cotizacion, c.fecha, c.cliente_id, cl.nombre, c.valido_hasta,
                   c.tipo, c.estatus
            FROM cotizaciones c
            JOIN clientes cl ON c.cliente_id = cl.id_cliente
            ORDER BY c.id_cotizacion DESC
        """)
        cotizaciones = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template("ver_cotizaciones.html", cotizaciones=cotizaciones)

# ==========================================
# Detalle de una cotización (GET y POST)
# ==========================================
# En app/gestion_cotizaciones.py

@ges_cotizaciones_bp.route("/<int:id_cotizacion>", methods=["GET", "POST"])
def detalle_cotizacion(id_cotizacion):
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    conn = conectar_bd()
    try:
        cur = conn.cursor()

        if request.method == "POST":
            nuevo_tipo = request.form.get("tipo")
            nuevo_estatus = request.form.get("estatus")
            fecha_entrega_raw = request.form.get("fecha_entrega")
            
            fecha_entrega = None
            if fecha_entrega_raw:
                try:
                    fecha_entrega = datetime.strptime(fecha_entrega_raw, "%Y-%m-%d").date()
                except ValueError:
                    fecha_entrega = None

            cur.execute("""
                UPDATE cotizaciones
                SET tipo = %s, estatus = %s, fecha_entrega = %s
                WHERE id_cotizacion = %s
            """, (nuevo_tipo, nuevo_estatus, fecha_entrega, id_cotizacion))
            conn.commit()
            flash("Cotización actualizada correctamente", "success")
            
            return redirect(url_for("ges_cotizaciones.detalle_cotizacion", id_cotizacion=id_cotizacion))

        # --- Lógica para GET ---
        cur.execute("""
            SELECT c.id_cotizacion, c.fecha, c.cliente_id, cl.nombre,
                   c.valido_hasta, c.tipo, c.estatus, c.fecha_hora_creacion, c.fecha_entrega
            FROM cotizaciones c
            JOIN clientes cl ON c.cliente_id = cl.id_cliente
            WHERE c.id_cotizacion = %s
        """, (id_cotizacion,))
        cotizacion = cur.fetchone()

        if not cotizacion:
            flash("La cotización no existe", "warning")
            return redirect(url_for("ges_cotizaciones.ver_cotizaciones"))

        cur.execute("""
            SELECT d.descripcion, d.cantidad, d.precio_unitario, d.total
            FROM detalle_cotizacion d
            WHERE d.id_cotizacion = %s
        """, (id_cotizacion,))
        detalles = cur.fetchall()

        gran_total = sum(d[3] for d in detalles) if detalles else 0

        return render_template(
            "detalle_cotizacion.html",
            cotizacion=cotizacion,
            detalles=detalles,
            total=gran_total,
            fecha_entrega=cotizacion[8] if cotizacion and len(cotizacion) > 8 else None
        )

    except Exception as e:
        conn.rollback()
        flash(f"Error de base de datos: {e}", "danger")
        # Si algo falla, redirigimos a la lista para evitar bucles.
        return redirect(url_for("ges_cotizaciones.ver_cotizaciones"))
    finally:
        if conn:
            conn.close()

# ==========================================
# Eliminar cotización
# ==========================================
@ges_cotizaciones_bp.route("/eliminar/<int:id_cotizacion>", methods=["POST"])
def eliminar_cotizacion(id_cotizacion):
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    conn = conectar_bd()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM detalle_cotizacion WHERE id_cotizacion = %s", (id_cotizacion,))
        cur.execute("DELETE FROM cotizaciones WHERE id_cotizacion = %s", (id_cotizacion,))
        conn.commit()
        flash("Cotización eliminada correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar la cotización: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("ges_cotizaciones.ver_cotizaciones"))
