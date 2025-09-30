
import psycopg2

def conectar_bd():
    return psycopg2.connect(
        dbname="chillice_db",
        user="postgres",
        password="Cocos121",
        host="localhost",
        port="5432"
    )

def obtener_nombre_empleado(matricula):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM public.rrhh_empleados WHERE id_empleado = %s", (matricula,))
    nombre = cur.fetchone()[0] if cur.rowcount else "Desconocido"
    cur.close()
    conn.close()
    return nombre

def obtener_datos_cliente(cliente_id):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        SELECT nombre, calle, numero_exterior, numero_interior, colonia,
               codigo_postal, municipio, estado, telefono, correo, rfc
        FROM public.clientes
        WHERE id_cliente = %s
    """, (cliente_id,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    return resultado

def obtener_id_producto_por_nombre(nombre_producto):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("""
        SELECT id_producto FROM public.productos
        WHERE nombre = %s
    """, (nombre_producto,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    return resultado[0] if resultado else None

def obtener_descripcion_producto(id_producto):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute("SELECT descripcion FROM public.productos WHERE id_producto = %s", (id_producto,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    return resultado[0] if resultado else id_producto
