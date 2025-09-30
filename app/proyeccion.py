# proyeccion.py
from flask import Blueprint, render_template, request, session, redirect, url_for, Response
from datetime import datetime, date
from utils.db import conectar_bd
import io

# Matplotlib sin GUI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

proyeccion_bp = Blueprint('proyeccion', __name__, url_prefix='/proyeccion')


# ---------------------------
# Helpers
# ---------------------------
def y_m_label(d: date) -> str:
    return f"{d.year}-{str(d.month).zfill(2)}"

def month_first_day(d: date) -> date:
    return d.replace(day=1)

def month_shift(d: date, delta_months: int) -> date:
    y = d.year + (d.month - 1 + delta_months) // 12
    m = (d.month - 1 + delta_months) % 12 + 1
    return date(y, m, 1)


# ---------------------------
# Vista principal
# ---------------------------
@proyeccion_bp.route('/')
def ver_proyeccion():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    fecha_qs = request.args.get('fecha')
    fecha = datetime.strptime(fecha_qs, '%Y-%m-%d').date() if fecha_qs else date.today()

    conn = conectar_bd()
    cur = conn.cursor()

    # Pedidos del día seleccionado
    cur.execute("""
        SELECT c.id_cotizacion, cli.id_cliente, cli.nombre, d.descripcion, d.cantidad, c.fecha_entrega
        FROM cotizaciones c
        JOIN clientes cli ON cli.id_cliente = c.cliente_id
        JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
        WHERE c.fecha_entrega = %s AND c.tipo = 'Pedido'
        ORDER BY c.id_cotizacion
    """, (fecha,))
    registros = cur.fetchall()

    pedidos_dict = {}
    resumen = {"5kg": 0, "15kg": 0, "total_kg": 0}
    for id_cot, id_cliente, nombre, desc, cant, fecha_entrega in registros:
        if id_cot not in pedidos_dict:
            pedidos_dict[id_cot] = {
                "id": id_cot,
                "cliente": f"{id_cliente} - {nombre}",
                "fecha_entrega": fecha_entrega.strftime("%Y-%m-%d") if fecha_entrega else "Sin definir",
                "productos": []
            }
        pedidos_dict[id_cot]["productos"].append((desc, cant))

        if "5 kilogramos" in desc and "15" not in desc:
            resumen["5kg"] += cant
            resumen["total_kg"] += cant * 5
        elif "15 kilogramos" in desc:
            resumen["15kg"] += cant
            resumen["total_kg"] += cant * 15

    pedidos = list(pedidos_dict.values())

    # === Inventario (existencias reales) ===
    # Producción acumulada histórica
    cur.execute("""
        SELECT COALESCE(SUM(bolsas_5kg),0), COALESCE(SUM(bolsas_15kg),0)
        FROM produccion_lotes
    """)
    prod_5kg, prod_15kg = cur.fetchone()

    # Entregado histórico (solo registros marcados como "Pedido")
    cur.execute("""
        SELECT 
        COALESCE(SUM(CASE WHEN d.descripcion ILIKE '%%5 kilogramos%%'
                            AND d.descripcion NOT ILIKE '%%15%%'
                            THEN d.cantidad ELSE 0 END),0) AS bolsas5,
        COALESCE(SUM(CASE WHEN d.descripcion ILIKE '%%15 kilogramos%%'
                            THEN d.cantidad ELSE 0 END),0) AS bolsas15
        FROM cotizaciones c
        JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo = 'Pedido'
    """)
    bolsas5_ent_total, bolsas15_ent_total = cur.fetchone()

    stock_5  = max((prod_5kg  or 0) - (bolsas5_ent_total  or 0), 0)
    stock_15 = max((prod_15kg or 0) - (bolsas15_ent_total or 0), 0)

    inventario = {
        "5kg": stock_5,
        "15kg": stock_15,
        "total_kg": stock_5 * 5 + stock_15 * 15
    }

    # === Calcular faltantes (para alertas) ===
    faltan_5 = max(0, resumen["5kg"] - inventario["5kg"])
    faltan_15 = max(0, resumen["15kg"] - inventario["15kg"])

    # === Entregado e ingresos del MES ACTUAL (panel informativo) ===
    cur.execute("""
        SELECT 
          COALESCE(SUM(CASE WHEN d.descripcion ILIKE '%%5 kilogramos%%'
                             AND d.descripcion NOT ILIKE '%%15%%'
                            THEN d.cantidad ELSE 0 END),0) AS bolsas5_mes,
          COALESCE(SUM(CASE WHEN d.descripcion ILIKE '%%15 kilogramos%%'
                            THEN d.cantidad ELSE 0 END),0) AS bolsas15_mes,
          COALESCE(SUM(d.total),0) AS ingresos_mes
        FROM cotizaciones c
        JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo='Pedido' AND c.estatus='Entregado'
          AND DATE_TRUNC('month', c.fecha) = DATE_TRUNC('month', %s::date)
    """, (fecha,))
    bolsas5_entregadas_mes, bolsas15_entregadas_mes, ingresos_mes = cur.fetchone()

    # === Desglose mensual (últimos 12) ===
    cur.execute("""
        SELECT DATE_TRUNC('month', fecha_hora_registro)::date, SUM(total_kg)
        FROM produccion_lotes
        GROUP BY 1 ORDER BY 1 DESC LIMIT 12
    """)
    prod_m = dict(cur.fetchall())

    cur.execute("""
        SELECT DATE_TRUNC('month', c.fecha)::date, 
               SUM(CASE WHEN d.descripcion ILIKE '%%5 kilogramos%%' AND d.descripcion NOT ILIKE '%%15%%'
                        THEN d.cantidad*5
                        WHEN d.descripcion ILIKE '%%15 kilogramos%%'
                        THEN d.cantidad*15 ELSE 0 END)
        FROM cotizaciones c
        JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo='Pedido' AND c.estatus='Entregado'
        GROUP BY 1 ORDER BY 1 DESC LIMIT 12
    """)
    entr_m = dict(cur.fetchall())

    cur.close()
    conn.close()

    meses = []
    m0 = month_first_day(date.today())
    for i in range(11, -1, -1):
        m = month_shift(m0, -i)
        producido = int(prod_m.get(m, 0) or 0)
        entregado = int(entr_m.get(m, 0) or 0)
        neto = producido - entregado
        meses.append({
            "mes": y_m_label(m),
            "kg_producido": producido,
            "kg_entregado": entregado,
            "kg_neto": neto
        })

    return render_template(
        "ver_proyeccion.html",
        fecha=fecha.strftime('%Y-%m-%d'),
        pedidos=pedidos,
        resumen=resumen,
        inventario=inventario,
        bolsas5_entregadas=bolsas5_entregadas_mes,
        bolsas15_entregadas=bolsas15_entregadas_mes,
        ingresos_mes=ingresos_mes,
        fecha_actual=date.today(),
        desglose_mensual=meses,
        faltan_5=faltan_5,
        faltan_15=faltan_15
    )


# ---------------------------
# Gráficas
# ---------------------------
@proyeccion_bp.route('/grafica_inventario/<int:year>/<int:month>')
def grafica_inventario(year, month):
    conn = conectar_bd(); cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(total_kg),0)
        FROM produccion_lotes
        WHERE DATE_TRUNC('month', fecha_hora_registro) = %s
    """, (date(year, month, 1),))
    kg_prod = int(cur.fetchone()[0] or 0)

    cur.execute("""
        SELECT SUM(CASE WHEN d.descripcion ILIKE '%%5 kilogramos%%' AND d.descripcion NOT ILIKE '%%15%%'
                        THEN d.cantidad*5
                        WHEN d.descripcion ILIKE '%%15 kilogramos%%'
                        THEN d.cantidad*15 ELSE 0 END)
        FROM cotizaciones c
        JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo='Pedido' AND c.estatus='Entregado'
          AND DATE_TRUNC('month', c.fecha) = DATE_TRUNC('month', %s::date)
    """, (date(year, month, 1),))
    kg_ent = int(cur.fetchone()[0] or 0)

    cur.close(); conn.close()

    kg_neto = kg_prod - kg_ent
    labels = ["Producido", "Entregado", "Inventario"]
    values = [kg_prod, kg_ent, kg_neto]
    colors = ["#2C7DA0", "#89CFF0", "#0A2463"]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color=colors, edgecolor="#333", linewidth=1.2)

    # Números encima
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2,
                yval + (max(values) * 0.02),
                f"{yval:,}", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color="#0A2463")

    # Espacio extra arriba
    ax.set_ylim(0, max(values) * 1.15)

    ax.set_title(f"Inventario Mensual (kg) — {year}-{str(month).zfill(2)}",
                 fontsize=13, fontweight="bold", color="#0A2463")
    ax.set_ylabel("Producción (kg)", fontsize=11, color="#0A2463")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    buf = io.BytesIO(); plt.tight_layout(); fig.savefig(buf, format="png", dpi=120)
    plt.close(fig); buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

@proyeccion_bp.route('/grafica_diaria/<int:year>/<int:month>')
def grafica_diaria(year, month):
    conn = conectar_bd(); cur = conn.cursor()
    cur.execute("""
        SELECT EXTRACT(DAY FROM fecha_hora_registro)::int, SUM(total_kg)
        FROM produccion_lotes
        WHERE DATE_TRUNC('month', fecha_hora_registro) = %s
        GROUP BY 1 ORDER BY 1
    """, (date(year, month, 1),))
    rows = cur.fetchall(); cur.close(); conn.close()

    dias = [r[0] for r in rows]; kg = [int(r[1]) for r in rows]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(dias, kg, marker="o", markersize=8,
            color="#0A2463", linewidth=2)
    ax.fill_between(dias, kg, color="#2C7DA0", alpha=0.2)

    # Números encima
    if kg:
        for x, y in zip(dias, kg):
            ax.text(x, y + (max(kg) * 0.02),
                    f"{y:,}", ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="#0A2463")

        # Espacio extra arriba
        ax.set_ylim(0, max(kg) * 1.15)

    ax.set_xticks(range(min(dias), max(dias)+1))  # enteros en eje X
    ax.set_title(f"Producción Diaria (kg) — {year}-{str(month).zfill(2)}",
                 fontsize=13, fontweight="bold", color="#0A2463")
    ax.set_xlabel("Día del mes", fontsize=11, color="#0A2463")
    ax.set_ylabel("Producción (kg)", fontsize=11, color="#0A2463")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    buf = io.BytesIO(); plt.tight_layout(); fig.savefig(buf, format="png", dpi=120)
    plt.close(fig); buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

@proyeccion_bp.route('/grafica_ingresos/<int:year>/<int:month>')
def grafica_ingresos(year, month):
    conn = conectar_bd(); cur = conn.cursor()
    cur.execute("""
        SELECT DATE_TRUNC('month', c.fecha)::date, SUM(d.total)
        FROM cotizaciones c
        JOIN detalle_cotizacion d ON d.id_cotizacion=c.id_cotizacion
        WHERE c.tipo='Pedido' AND c.estatus='Entregado'
        GROUP BY 1 ORDER BY 1 LIMIT 12
    """)
    rows = cur.fetchall(); cur.close(); conn.close()

    meses = [y_m_label(r[0]) for r in rows]
    ingresos = [float(r[1]) for r in rows]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(meses, ingresos, color="#2C7DA0", edgecolor="#333")

    # Números encima
    if ingresos:
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2,
                    yval + (max(ingresos) * 0.02),
                    f"${yval:,.0f}", ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="#0A2463")

        # Espacio extra arriba
        ax.set_ylim(0, max(ingresos) * 1.15)

    ax.set_title("Ingresos Últimos 12 Meses",
                 fontsize=13, fontweight="bold", color="#0A2463")
    ax.set_ylabel("Ingresos ($)", fontsize=11, color="#0A2463")
    ax.set_xticklabels(meses, rotation=45, ha="right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    buf = io.BytesIO(); plt.tight_layout(); fig.savefig(buf, format="png", dpi=120)
    plt.close(fig); buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")
