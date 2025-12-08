# app/proyeccion.py
from flask import Blueprint, render_template, request, session, redirect, url_for, Response, jsonify
from datetime import datetime, date, timedelta
from utils.db import conectar_bd
import io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

# --- CORRECCIÓN: Definición del Blueprint movida al inicio del archivo ---
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def get_current_stock(conn):
    """
    Función auxiliar que calcula el stock 'General' y 'Diego'
    para ser usada por el dashboard y el módulo de mermas.
    DEVUELVE: (stock_general_bolsas, stock_diego_bolsas)
    """
    # ... (La lógica de esta función es compleja y correcta, no se necesita cambiar) ...
    stock_query = """
        WITH p_diego AS (
            SELECT
                COALESCE(SUM(bolsas_1kg), 0) AS prod_1kg, COALESCE(SUM(bolsas_3kg), 0) AS prod_3kg,
                COALESCE(SUM(bolsas_5kg), 0) AS prod_5kg, COALESCE(SUM(bolsas_15kg), 0) AS prod_15kg
            FROM produccion_lotes WHERE observaciones ILIKE '%%diego%%'
        ),
        p_general AS (
            SELECT
                COALESCE(SUM(bolsas_1kg), 0) AS prod_1kg, COALESCE(SUM(bolsas_3kg), 0) AS prod_3kg,
                COALESCE(SUM(bolsas_5kg), 0) AS prod_5kg, COALESCE(SUM(bolsas_15kg), 0) AS prod_15kg
            FROM produccion_lotes WHERE COALESCE(observaciones, '') NOT ILIKE '%%diego%%'
        ),
        v_base AS (
            SELECT d.id_producto, c.cliente_id, COALESCE(SUM(d.cantidad), 0) as total_vendido
            FROM detalle_cotizacion d
            JOIN cotizaciones c ON d.id_cotizacion = c.id_cotizacion
            WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado'
            GROUP BY d.id_producto, c.cliente_id
        ),
        v_diego AS (
            SELECT
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR1KG'), 0) AS ventas_1kg,
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR3KG'), 0) AS ventas_3kg,
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR5KG'), 0) AS ventas_5kg,
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR15KG'), 0) AS ventas_15kg
            FROM v_base WHERE cliente_id = 'ICE000'
        ),
        v_general AS (
            SELECT
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR1KG'), 0) AS ventas_1kg,
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR3KG'), 0) AS ventas_3kg,
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR5KG'), 0) AS ventas_5kg,
                COALESCE(SUM(total_vendido) FILTER (WHERE id_producto = 'BR15KG'), 0) AS ventas_15kg
            FROM v_base WHERE cliente_id != 'ICE000'
        ),
        m_diego AS (
            SELECT
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 1), 0) AS merma_1kg,
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 3), 0) AS merma_3kg,
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 5), 0) AS merma_5kg,
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 15), 0) AS merma_15kg
            FROM mermas.registros WHERE comentarios ILIKE '%%diego%%'
        ),
        m_general AS (
            SELECT
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 1), 0) AS merma_1kg,
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 3), 0) AS merma_3kg,
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 5), 0) AS merma_5kg,
                COALESCE(SUM(cantidad_bolsas) FILTER (WHERE tamano_kg = 15), 0) AS merma_15kg
            FROM mermas.registros WHERE COALESCE(comentarios, '') NOT ILIKE '%%diego%%'
        )
        SELECT
         (p_general.prod_1kg - v_general.ventas_1kg - m_general.merma_1kg) AS stock_general_1kg,
         (p_general.prod_3kg - v_general.ventas_3kg - m_general.merma_3kg) AS stock_general_3kg,
         (p_general.prod_5kg - v_general.ventas_5kg - m_general.merma_5kg) AS stock_general_5kg,
         (p_general.prod_15kg - v_general.ventas_15kg - m_general.merma_15kg) AS stock_general_15kg,
         (p_diego.prod_1kg - v_diego.ventas_1kg - m_diego.merma_1kg) AS stock_diego_1kg,
         (p_diego.prod_3kg - v_diego.ventas_3kg - m_diego.merma_3kg) AS stock_diego_3kg,
         (p_diego.prod_5kg - v_diego.ventas_5kg - m_diego.merma_5kg) AS stock_diego_5kg,
         (p_diego.prod_15kg - v_diego.ventas_15kg - m_diego.merma_15kg) AS stock_diego_15kg
        FROM p_general, p_diego, v_general, v_diego, m_general, m_diego;
    """
    stock_df = pd.read_sql(stock_query, conn).iloc[0]
    
    stock_general_bolsas = {
        '1': int(stock_df['stock_general_1kg']),
        '3': int(stock_df['stock_general_3kg']),
        '5': int(stock_df['stock_general_5kg']),
        '15': int(stock_df['stock_general_15kg'])
    }
    
    stock_diego_bolsas = {
        '1': int(stock_df['stock_diego_1kg']),
        '3': int(stock_df['stock_diego_3kg']),
        '5': int(stock_df['stock_diego_5kg']),
        '15': int(stock_df['stock_diego_15kg'])
    }
    
    return stock_general_bolsas, stock_diego_bolsas


def get_dashboard_data_scoped(conn, scope, month_str):
    """
    Función que obtiene los datos que SÍ dependen del scope (mes / overall)
    """
    
    param = month_str if scope == 'month' else None
    
    # 1. KPIs de Ingresos (General + Diego)
    ingresos_query = """
        SELECT COALESCE(SUM(d.total), 0) AS ingresos
        FROM cotizaciones c 
        JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado'
          AND (%(scope)s = 'overall' OR to_char(c.fecha_entrega, 'YYYY-MM') = %(month)s)
    """
    kpis_ingresos = pd.read_sql(ingresos_query, conn, params={'scope': scope, 'month': param}).iloc[0]

    # 2. KPI de Merma (General + Diego)
    merma_kg_query = """
        SELECT COALESCE(SUM(kg_merma), 0) AS merma_kg
        FROM mermas.registros
        WHERE (%(scope)s = 'overall' OR to_char(fecha_hora, 'YYYY-MM') = %(month)s)
    """
    kpi_merma = pd.read_sql(merma_kg_query, conn, params={'scope': scope, 'month': param}).iloc[0]

    # 3. KPIs de Ventas TOTALES (Bolsas y KG)
    # --- MODIFICACIÓN: Esta query ahora incluye TODAS las ventas (Diego + General) ---
    # --- Se quitó 'precio_promedio_total' y se añadió 'total_kg_vendidos' ---
    ventas_totales_query = """
        SELECT
            COALESCE(SUM(d.cantidad), 0) AS total_bolsas_vendidas,
            
            -- NUEVO: Calcular el total de KG vendidos
            COALESCE(SUM(CASE 
                WHEN d.id_producto = 'BR1KG' THEN d.cantidad * 1
                WHEN d.id_producto = 'BR3KG' THEN d.cantidad * 3
                WHEN d.id_producto = 'BR5KG' THEN d.cantidad * 5
                WHEN d.id_producto = 'BR15KG' THEN d.cantidad * 15
                ELSE 0 
            END), 0) AS total_kg_vendidos,

            -- Bolsas vendidas por tamaño
            COALESCE(SUM(d.cantidad) FILTER (WHERE d.id_producto = 'BR1KG'), 0) AS ventas_1kg,
            COALESCE(SUM(d.cantidad) FILTER (WHERE d.id_producto = 'BR3KG'), 0) AS ventas_3kg,
            COALESCE(SUM(d.cantidad) FILTER (WHERE d.id_producto = 'BR5KG'), 0) AS ventas_5kg,
            COALESCE(SUM(d.cantidad) FILTER (WHERE d.id_producto = 'BR15KG'), 0) AS ventas_15kg
        FROM detalle_cotizacion d
        JOIN cotizaciones c ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado'
          AND (%(scope)s = 'overall' OR to_char(c.fecha_entrega, 'YYYY-MM') = %(month)s)
    """
    kpis_ventas_df = pd.read_sql(ventas_totales_query, conn, params={'scope': scope, 'month': param}).iloc[0]

    # 4. NUEVO: KPIs de Precio Promedio por Tamaño (TOTALES)
    precios_tamano_query = """
        SELECT
            d.id_producto,
            COALESCE(SUM(d.total) / NULLIF(SUM(d.cantidad), 0), 0) AS precio_promedio
        FROM detalle_cotizacion d
        JOIN cotizaciones c ON d.id_cotizacion = c.id_cotizacion
        WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado'
          AND (%(scope)s = 'overall' OR to_char(c.fecha_entrega, 'YYYY-MM') = %(month)s)
        GROUP BY d.id_producto
    """
    precios_df = pd.read_sql(precios_tamano_query, conn, params={'scope': scope, 'month': param})
    precios_dict = {'1': 0.0, '3': 0.0, '5': 0.0, '15': 0.0}
    for _, row in precios_df.iterrows():
        if row['id_producto'] == 'BR1KG': precios_dict['1'] = row['precio_promedio']
        if row['id_producto'] == 'BR3KG': precios_dict['3'] = row['precio_promedio']
        if row['id_producto'] == 'BR5KG': precios_dict['5'] = row['precio_promedio']
        if row['id_producto'] == 'BR15KG': precios_dict['15'] = row['precio_promedio']
    
    # 5. Producción Diego (Bolsas)
    diego_prod_query = """
        WITH lotes_filtrados AS (
          SELECT *
          FROM public.produccion_lotes
          WHERE (%(scope)s = 'overall' OR to_char(fecha_hora_registro, 'YYYY-MM') = %(month)s)
        )
        SELECT
          COALESCE(SUM(CASE WHEN observaciones ILIKE '%%diego%%' THEN bolsas_1kg ELSE 0 END), 0) AS diego_1kg,
          COALESCE(SUM(CASE WHEN observaciones ILIKE '%%diego%%' THEN bolsas_3kg ELSE 0 END), 0) AS diego_3kg,
          COALESCE(SUM(CASE WHEN observaciones ILIKE '%%diego%%' THEN bolsas_5kg ELSE 0 END), 0) AS diego_5kg,
          COALESCE(SUM(CASE WHEN observaciones ILIKE '%%diego%%' THEN bolsas_15kg ELSE 0 END), 0) AS diego_15kg
        FROM lotes_filtrados;
    """
    diego_df = pd.read_sql(diego_prod_query, conn, params={'scope': scope, 'month': param}).iloc[0]
    diego_produccion_bolsas = {
        '1': int(diego_df['diego_1kg']),
        '3': int(diego_df['diego_3kg']),
        '5': int(diego_df['diego_5kg']),
        '15': int(diego_df['diego_15kg'])
    }
    
    # 6. Producción General (Bolsas)
    general_prod_query = """
        WITH lotes_filtrados AS (
          SELECT *
          FROM public.produccion_lotes
          WHERE (%(scope)s = 'overall' OR to_char(fecha_hora_registro, 'YYYY-MM') = %(month)s)
        )
        SELECT
          COALESCE(SUM(CASE WHEN COALESCE(observaciones, '') NOT ILIKE '%%diego%%' THEN bolsas_1kg ELSE 0 END), 0) AS general_1kg,
          COALESCE(SUM(CASE WHEN COALESCE(observaciones, '') NOT ILIKE '%%diego%%' THEN bolsas_3kg ELSE 0 END), 0) AS general_3kg,
          COALESCE(SUM(CASE WHEN COALESCE(observaciones, '') NOT ILIKE '%%diego%%' THEN bolsas_5kg ELSE 0 END), 0) AS general_5kg,
          COALESCE(SUM(CASE WHEN COALESCE(observaciones, '') NOT ILIKE '%%diego%%' THEN bolsas_15kg ELSE 0 END), 0) AS general_15kg
        FROM lotes_filtrados;
    """
    general_df = pd.read_sql(general_prod_query, conn, params={'scope': scope, 'month': param}).iloc[0]
    produccion_general_bolsas = {
        '1': int(general_df['general_1kg']),
        '3': int(general_df['general_3kg']),
        '5': int(general_df['general_5kg']),
        '15': int(general_df['general_15kg'])
    }
    
    # --- Empaquetar datos ---
    
    # --- MODIFICACIÓN: Calcular precio_promedio_kg ---
    total_ingresos = kpis_ingresos['ingresos']
    total_kg = kpis_ventas_df['total_kg_vendidos']
    
    precio_kg = 0.0
    if total_kg > 0:
        precio_kg = total_ingresos / total_kg
    # --- FIN MODIFICACIÓN ---

    kpis = {
        'ingresos': total_ingresos,
        'merma_kg': kpi_merma['merma_kg'],
        'total_bolsas_vendidas': int(kpis_ventas_df['total_bolsas_vendidas']),
        'precio_promedio_kg': precio_kg # <-- MODIFICADO
    }
    
    ventas_por_tamano = {
        '1': int(kpis_ventas_df['ventas_1kg']),
        '3': int(kpis_ventas_df['ventas_3kg']),
        '5': int(kpis_ventas_df['ventas_5kg']),
        '15': int(kpis_ventas_df['ventas_15kg']),
    }

    return kpis, diego_produccion_bolsas, produccion_general_bolsas, precios_dict, ventas_por_tamano


@dashboard_bp.route('/')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    conn = None
    try:
        # --- Pedidos del día (Lógica de fecha separada) ---
        fecha_qs = request.args.get('fecha_pedidos')
        fecha_filtrada_pedidos = datetime.strptime(fecha_qs, '%Y-%m-%d').date() if fecha_qs else date.today()

        conn = conectar_bd()
        pedidos_query = """
            SELECT c.id_cotizacion, cli.id_cliente, cli.nombre, d.descripcion, d.cantidad, c.estatus
            FROM cotizaciones c
            JOIN clientes cli ON cli.id_cliente = c.cliente_id
            JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion
            WHERE c.fecha_entrega = %s AND c.tipo = 'Pedido' ORDER BY c.id_cotizacion
        """
        pedidos_df = pd.read_sql(pedidos_query, conn, params=(fecha_filtrada_pedidos,))
        pedidos_dict = {}
        for _, row in pedidos_df.iterrows():
            if row['id_cotizacion'] not in pedidos_dict:
                pedidos_dict[row['id_cotizacion']] = {"id": row['id_cotizacion'], "cliente": f"{row['id_cliente']} - {row['nombre']}", "estatus": row['estatus'], "productos": []}
            pedidos_dict[row['id_cotizacion']]['productos'].append((row['descripcion'], row['cantidad']))
        pedidos_hoy = list(pedidos_dict.values())

        # --- KPIs, Stock y Diego (Lógica de scope/mes) ---
        scope = request.args.get('scope', 'month')
        month_str = request.args.get('month', date.today().strftime('%Y-%m'))
        if scope == 'overall':
            month_str = None # Ignora el mes si es overall
        
        # --- MODIFICACIÓN: Llamadas a las funciones separadas ---
        kpis, diego_produccion_bolsas, produccion_general_bolsas, precios_promedio_por_tamano, ventas_por_tamano = get_dashboard_data_scoped(conn, scope, month_str) # <-- Updated return values
        stock_general_bolsas, stock_diego_bolsas = get_current_stock(conn) # El stock siempre es "overall"

        kpis_data = {
            'kpis': kpis, # <-- Este diccionario ya contiene 'precio_promedio_kg'
            'stock_general': stock_general_bolsas,
            'stock_diego': stock_diego_bolsas,
            'diego_produccion': diego_produccion_bolsas,
            'produccion_general': produccion_general_bolsas,
            'precios_promedio_por_tamano': precios_promedio_por_tamano, 
            'ventas_por_tamano': ventas_por_tamano 
        }
        # --- MODIFICACIÓN TERMINA ---

        return render_template("ver_proyeccion_v2.html", 
                               fecha_pedidos=fecha_filtrada_pedidos.strftime('%Y-%m-%d'), 
                               pedidos_hoy=pedidos_hoy, 
                               kpis_data=kpis_data, 
                               scope=scope,
                               month_selected=month_str if scope == 'month' else date.today().strftime('%Y-%m'),
                               now=datetime.now)
    
    finally:
        if conn:
            conn.close()

#
# --- RESTO DE RUTAS DE GRÁFICAS (API) ---
# (Sin cambios)
#

def crear_grafica(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

@dashboard_bp.route('/grafica/produccion_vs_entregas')
def grafica_produccion_vs_entregas():
    conn = conectar_bd()
    produccion_df = pd.read_sql("""
        SELECT EXTRACT(DAY FROM fecha_hora_registro)::int as dia, SUM(total_kg) as kg
        FROM produccion_lotes
        WHERE DATE_TRUNC('month', fecha_hora_registro) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1
    """, conn)
    
    entregas_df = pd.read_sql("""
        SELECT EXTRACT(DAY FROM c.fecha_entrega)::int as dia, 
               SUM(CASE 
                    WHEN d.id_producto = 'BR1KG' THEN d.cantidad*1
                    WHEN d.id_producto = 'BR3KG' THEN d.cantidad*3
                    WHEN d.id_producto = 'BR5KG' THEN d.cantidad*5 
                    WHEN d.id_producto = 'BR15KG' THEN d.cantidad*15 ELSE 0 END) as kg
        FROM cotizaciones c JOIN detalle_cotizacion d ON c.id_cotizacion = d.id_cotizacion
        WHERE c.tipo='Pedido' AND c.estatus='Entregado' 
              AND DATE_TRUNC('month', c.fecha_entrega) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1
    """, conn)
    conn.close()

    df = pd.merge(produccion_df.rename(columns={'kg': 'Producción (kg)'}), 
                  entregas_df.rename(columns={'kg': 'Entregas (kg)'}), 
                  on='dia', how='outer').fillna(0)
    hoy = date.today()
    ultimo_dia_mes = (date(hoy.year, hoy.month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    dias_del_mes = pd.DataFrame({'dia': range(1, ultimo_dia_mes.day + 1)})
    df = pd.merge(dias_del_mes, df, on='dia', how='left').fillna(0)
    df_melted = df.melt(id_vars='dia', var_name='Tipo', value_name='Kilogramos')
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x='dia', y='Kilogramos', hue='Tipo', data=df_melted, 
                palette={'Producción (kg)': '#2C7DA0', 'Entregas (kg)': '#FFC107'}, ax=ax)
    nombre_mes = hoy.strftime('%B %Y').capitalize()
    ax.set_title(f"Producción vs. Entregas - {nombre_mes}", fontsize=14, fontweight="bold")
    ax.set_ylabel("Kilogramos (kg)"); ax.set_xlabel("Día del Mes"); ax.legend(title="")
    return crear_grafica(fig)


@dashboard_bp.route('/grafica/ingresos_mensuales')
def grafica_ingresos_mensuales():
    conn = conectar_bd()
    df = pd.read_sql("SELECT TO_CHAR(DATE_TRUNC('month', c.fecha), 'YYYY-MM') as mes, SUM(d.total) as ingresos FROM cotizaciones c JOIN detalle_cotizacion d ON d.id_cotizacion = c.id_cotizacion WHERE c.tipo='Pedido' AND c.estatus='Entregado' GROUP BY 1 ORDER BY 1 DESC LIMIT 12", conn)
    conn.close()
    if df.empty: return Response(status=204)
    df = df.iloc[::-1]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(x='mes', y='ingresos', data=df, palette="viridis", ax=ax)
    ax.set_title("Ingresos Mensuales", fontsize=14, fontweight="bold"); ax.set_ylabel("Ingresos ($)"); ax.set_xlabel(""); ax.tick_params(axis='x', rotation=45)
    return crear_grafica(fig)


@dashboard_bp.route('/grafica/top_clientes')
def grafica_top_clientes():
    conn = conectar_bd()
    df = pd.read_sql("SELECT cl.nombre, SUM(d.total) as total FROM cotizaciones c JOIN detalle_cotizacion d ON c.id_cotizacion = d.id_cotizacion JOIN clientes cl ON c.cliente_id = cl.id_cliente WHERE c.tipo = 'Pedido' AND c.estatus = 'Entregado' GROUP BY 1 ORDER BY 2 DESC LIMIT 5", conn)
    conn.close()
    if df.empty: return Response(status=204)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(y='nombre', x='total', data=df, palette="plasma", orient='h', ax=ax)
    ax.set_title("Top 5 Clientes por Ingresos", fontsize=14, fontweight="bold"); ax.set_xlabel("Total Comprado ($)"); ax.set_ylabel("")
    return crear_grafica(fig)


@dashboard_bp.route('/grafica/mix_productos')
def grafica_mix_productos():
    conn = conectar_bd()
    df = pd.read_sql("""
        SELECT 
            CASE 
                WHEN d.id_producto = 'BR1KG' THEN 'Bolsa 1kg'
                WHEN d.id_producto = 'BR3KG' THEN 'Bolsa 3kg'
                WHEN d.id_producto = 'BR5KG' THEN 'Bolsa 5kg'
                WHEN d.id_producto = 'BR15KG' THEN 'Bolsa 15kg'
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
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = sns.color_palette('pastel')[0:len(df)]
    ax.pie(df['ingresos'], labels=df['producto'], autopct='%.1f%%', startangle=90, colors=colors, 
           wedgeprops={"edgecolor": "white", 'linewidth': 2})
    ax.set_title("Mix de Ingresos por Producto", fontsize=14, fontweight="bold")
    return crear_grafica(fig)


@dashboard_bp.route('/grafica/produccion_diaria')
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
    fig, ax = plt.subplots(figsize=(7, 5))
    lineplot = sns.lineplot(x='dia', y='total_kg', data=df, marker='o', color=sns.color_palette("viridis")[3], ax=ax)
    ax.fill_between(df['dia'], df['total_kg'], alpha=0.3, color=sns.color_palette("viridis")[3])
    for index, row in df.iterrows():
        ax.text(row['dia'], row['total_kg'] + df['total_kg'].max()*0.02, f"{row['total_kg']:.0f} kg", 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_title("Producción Diaria (Mes Actual)", fontsize=14, fontweight="bold"); ax.set_ylabel("Producción (kg)"); ax.set_xlabel("Día del Mes"); ax.set_ylim(0, df['total_kg'].max() * 1.18)
    return crear_grafica(fig)