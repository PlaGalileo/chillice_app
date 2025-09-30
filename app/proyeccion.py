# app/proyeccion.py
from flask import Blueprint, render_template, request, session, redirect, url_for, Response
from datetime import datetime, date, timedelta
from utils.db import conectar_bd
import io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

proyeccion_bp = Blueprint('proyeccion', __name__, url_prefix='/proyeccion')

@proyeccion_bp.route('/')
def ver_proyeccion():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    # Toma la fecha de la URL, si no existe, usa la fecha de hoy
    fecha_qs = request.args.get('fecha')
    fecha_filtrada = datetime.strptime(fecha_qs, '%Y-%m-%d').date() if fecha_qs else date.today()

    conn = conectar_bd()
    try:
        # --- Pedidos del día ---
        pedidos_query = """
            SELECT c.id_cotizacion, cli.id_cliente, cli.nombre, d.descripcion, d.cantidad, c.estatus
            FROM cotizaciones c
            JOIN clientes cli ON cli.id_cliente = c.cliente_id
            JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
            WHERE c.fecha_entrega = %s AND c.tipo = 'Pedido' ORDER BY c.id_cotizacion
        """
        pedidos_df = pd.read_sql(pedidos_query, conn, params=(fecha_filtrada,))
        pedidos_dict = {}
        for _, row in pedidos_df.iterrows():
            if row['id_cotizacion'] not in pedidos_dict:
                pedidos_dict[row['id_cotizacion']] = {"id": row['id_cotizacion'], "cliente": f"{row['id_cliente']} - {row['nombre']}", "estatus": row['estatus'], "productos": []}
            pedidos_dict[row['id_cotizacion']]['productos'].append((row['descripcion'], row['cantidad']))
        pedidos_hoy = list(pedidos_dict.values())

        # --- KPIs (Mensual e Histórico) y Stock ---
        # (Aquí va toda la lógica de consultas que ya corregimos)
        kpis_mensual_query = """
            SELECT
                COALESCE(SUM(CASE WHEN d.id_producto = 'BR5KG' THEN d.cantidad ELSE 0 END), 0) AS bolsas5,
                COALESCE(SUM(CASE WHEN d.id_producto = 'BR15KG' THEN d.cantidad ELSE 0 END), 0) AS bolsas15,
                COALESCE(SUM(d.total), 0) AS ingresos
            FROM cotizaciones c JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
            WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado' AND DATE_TRUNC('month', c.fecha_entrega) = DATE_TRUNC('month', CURRENT_DATE)
        """
        kpis_mensual = pd.read_sql(kpis_mensual_query, conn).iloc[0]
        tasa_mensual_query = "SELECT (SUM(CASE WHEN tipo = 'Pedido' THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0)::float * 100) AS val FROM cotizaciones WHERE DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)"
        tasa_mensual = (pd.read_sql(tasa_mensual_query, conn)['val'].iloc[0] or 0)
        kpis_historico_query = """
            SELECT
                COALESCE(SUM(CASE WHEN d.id_producto = 'BR5KG' THEN d.cantidad ELSE 0 END), 0) AS bolsas5,
                COALESCE(SUM(CASE WHEN d.id_producto = 'BR15KG' THEN d.cantidad ELSE 0 END), 0) AS bolsas15,
                COALESCE(SUM(d.total), 0) AS ingresos
            FROM cotizaciones c JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
            WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado'
        """
        kpis_historico = pd.read_sql(kpis_historico_query, conn).iloc[0]
        tasa_historica_query = "SELECT (SUM(CASE WHEN tipo = 'Pedido' THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0)::float * 100) AS val FROM cotizaciones"
        tasa_historica = (pd.read_sql(tasa_historica_query, conn)['val'].iloc[0] or 0)
        inventario_df = pd.read_sql("""
            SELECT 
                (SELECT COALESCE(SUM(bolsas_5kg),0) FROM produccion_lotes) - 
                (SELECT COALESCE(SUM(d.cantidad),0) FROM detalle_cotizacion d JOIN cotizaciones c ON d.id_cotizacion=c.id_cotizacion WHERE c.tipo='Pedido' AND c.estatus='Entregado' AND d.id_producto = 'BR5KG') 
                AS stock_5kg,
                
                (SELECT COALESCE(SUM(bolsas_15kg),0) FROM produccion_lotes) - 
                (SELECT COALESCE(SUM(d.cantidad),0) FROM detalle_cotizacion d JOIN cotizaciones c ON d.id_cotizacion=c.id_cotizacion WHERE c.tipo='Pedido' AND c.estatus='Entregado' AND d.id_producto = 'BR15KG') 
                AS stock_15kg
        """, conn)
        inventario = inventario_df.iloc[0]

    finally:
        conn.close()

    kpis_data = {
        'mensual': { 'ingresos': kpis_mensual['ingresos'], 'bolsas5': kpis_mensual['bolsas5'], 'bolsas15': kpis_mensual['bolsas15'], 'conversion': f"{tasa_mensual:.1f}%" },
        'historico': { 'ingresos': kpis_historico['ingresos'], 'bolsas5': kpis_historico['bolsas5'], 'bolsas15': kpis_historico['bolsas15'], 'conversion': f"{tasa_historica:.1f}%" },
        'stock_5kg': inventario['stock_5kg'], 'stock_15kg': inventario['stock_15kg']
    }

    return render_template("ver_proyeccion.html", 
                           fecha=fecha_filtrada.strftime('%Y-%m-%d'), 
                           pedidos_hoy=pedidos_hoy, 
                           kpis=kpis_data, 
                           now=datetime.now)
# --- RUTAS PARA LAS GRÁFICAS (API) ---

def crear_grafica(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

# --- ¡NUEVA GRÁFICA! ---
# En app/proyeccion.py

@proyeccion_bp.route('/grafica/produccion_vs_entregas')
def grafica_produccion_vs_entregas():
    conn = conectar_bd()
    # Obtenemos la producción diaria del mes actual
    produccion_df = pd.read_sql("""
        SELECT EXTRACT(DAY FROM fecha_hora_registro)::int as dia, SUM(total_kg) as kg
        FROM produccion_lotes
        WHERE DATE_TRUNC('month', fecha_hora_registro) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1
    """, conn)
    
    # Obtenemos las entregas diarias del mes actual
    entregas_df = pd.read_sql("""
        SELECT EXTRACT(DAY FROM c.fecha_entrega)::int as dia, 
               SUM(CASE WHEN d.id_producto = 'BR5KG' THEN d.cantidad*5 
                        WHEN d.id_producto = 'BR15KG' THEN d.cantidad*15 ELSE 0 END) as kg
        FROM cotizaciones c JOIN detalle_cotizacion d ON c.id_cotizacion = d.id_cotizacion
        WHERE c.tipo='Pedido' AND c.estatus='Entregado' 
              AND DATE_TRUNC('month', c.fecha_entrega) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1
    """, conn)
    conn.close()

    # Combinamos ambos dataframes
    df = pd.merge(produccion_df.rename(columns={'kg': 'Producción (kg)'}), 
                  entregas_df.rename(columns={'kg': 'Entregas (kg)'}), 
                  on='dia', how='outer').fillna(0)
    
    # Nos aseguramos de tener todos los días del mes
    hoy = date.today()
    ultimo_dia_mes = (date(hoy.year, hoy.month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    dias_del_mes = pd.DataFrame({'dia': range(1, ultimo_dia_mes.day + 1)})
    df = pd.merge(dias_del_mes, df, on='dia', how='left').fillna(0)
    
    # Preparamos los datos para una gráfica de barras agrupada
    df_melted = df.melt(id_vars='dia', var_name='Tipo', value_name='Kilogramos')

    # --- Creación de la Gráfica ---
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5)) # Hacemos la gráfica un poco más ancha
    
    sns.barplot(x='dia', y='Kilogramos', hue='Tipo', data=df_melted, 
                palette={'Producción (kg)': '#2C7DA0', 'Entregas (kg)': '#FFC107'}, ax=ax)
    
    # Títulos y etiquetas
    nombre_mes = hoy.strftime('%B %Y').capitalize()
    ax.set_title(f"Producción vs. Entregas - {nombre_mes}", fontsize=14, fontweight="bold")
    ax.set_ylabel("Kilogramos (kg)")
    ax.set_xlabel("Día del Mes")
    ax.legend(title="")
    
    return crear_grafica(fig)

@proyeccion_bp.route('/grafica/ingresos_mensuales')
def grafica_ingresos_mensuales():
    conn = conectar_bd()
    df = pd.read_sql("SELECT TO_CHAR(DATE_TRUNC('month', c.fecha), 'YYYY-MM') as mes, SUM(d.total) as ingresos FROM cotizaciones c JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion WHERE c.tipo='Pedido' AND c.estatus='Entregado' GROUP BY 1 ORDER BY 1 DESC LIMIT 12", conn)
    conn.close()
    if df.empty: return Response(status=204)
    df = df.iloc[::-1]

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(x='mes', y='ingresos', data=df, palette="viridis", ax=ax)
    ax.set_title("Ingresos Mensuales", fontsize=14, fontweight="bold")
    ax.set_ylabel("Ingresos ($)"); ax.set_xlabel("")
    ax.tick_params(axis='x', rotation=45)
    return crear_grafica(fig)


@proyeccion_bp.route('/grafica/top_clientes')
def grafica_top_clientes():
    conn = conectar_bd()
    df = pd.read_sql("SELECT cl.nombre, SUM(d.total) as total FROM cotizaciones c JOIN detalle_cotizacion d ON c.id_cotizacion = d.id_cotizacion JOIN clientes cl ON c.cliente_id = cl.id_cliente WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado' GROUP BY 1 ORDER BY 2 DESC LIMIT 5", conn)
    conn.close()
    if df.empty: return Response(status=204)

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 5)) # Tamaño ajustado
    sns.barplot(y='nombre', x='total', data=df, palette="plasma", orient='h', ax=ax)
    ax.set_title("Top 5 Clientes por Ingresos", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Comprado ($)"); ax.set_ylabel("")
    return crear_grafica(fig)

# En app/proyeccion.py

# En app/proyeccion.py

@proyeccion_bp.route('/grafica/mix_productos')
def grafica_mix_productos():
    conn = conectar_bd()
    # ESTA CONSULTA AHORA TAMBIÉN REVISA EL id_producto
    df = pd.read_sql("""
        SELECT 
            CASE 
                WHEN d.descripcion ILIKE '%%5 kilogramos%%' OR d.id_producto = 'BR5KG' THEN 'Bolsa 5kg'
                WHEN d.descripcion ILIKE '%%15 kilogramos%%' OR d.id_producto = 'BR15KG' THEN 'Bolsa 15kg'
                ELSE 'Otros'
            END as producto,
            SUM(d.total) as ingresos
        FROM detalle_cotizacion d
        JOIN cotizaciones c ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado'
        GROUP BY 1
    """, conn)
    conn.close()
    if df.empty: return Response(status=204)

    # El resto del código para generar la imagen no cambia
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = sns.color_palette('pastel')[0:len(df)]
    ax.pie(df['ingresos'], labels=df['producto'], autopct='%.1f%%', startangle=90, colors=colors, 
           wedgeprops={"edgecolor": "white", 'linewidth': 2})
    ax.set_title("Mix de Ingresos por Producto", fontsize=14, fontweight="bold")
    return crear_grafica(fig)

# === ¡NUEVA GRÁFICA DE PRODUCCIÓN DIARIA! ===
@proyeccion_bp.route('/grafica/produccion_diaria')
def grafica_produccion_diaria():
    conn = conectar_bd()
    df = pd.read_sql("""
        SELECT EXTRACT(DAY FROM fecha_hora_registro)::int as dia, SUM(total_kg) as total_kg
        FROM produccion_lotes
        WHERE DATE_TRUNC('month', fecha_hora_registro) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1 ORDER BY 1
    """, conn)
    conn.close()
    if df.empty: return Response(status=204)

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 5)) # Tamaño ajustado
    
    # Dibuja la línea y el área
    lineplot = sns.lineplot(x='dia', y='total_kg', data=df, marker='o', color=sns.color_palette("viridis")[3], ax=ax)
    ax.fill_between(df['dia'], df['total_kg'], alpha=0.3, color=sns.color_palette("viridis")[3])

    # Agrega los números encima de cada punto
    for index, row in df.iterrows():
        ax.text(row['dia'], row['total_kg'] + df['total_kg'].max()*0.02, f"{row['total_kg']:.0f} kg", 
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_title("Producción Diaria (Mes Actual)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Producción (kg)"); ax.set_xlabel("Día del Mes")
    ax.set_ylim(0, df['total_kg'].max() * 1.18) # Espacio extra para los números
    
    return crear_grafica(fig)