# generar_cotizacion.py
from flask import Blueprint, request, redirect, url_for, session, jsonify, render_template
from datetime import date, timedelta, datetime
from utils.db import conectar_bd
import os
from flask import send_from_directory, abort

# Blueprint con el nombre que usan tus plantillas (cotizaciones)
generar_cotizacion_bp = Blueprint("cotizaciones", __name__, url_prefix="/cotizaciones")

# ─────────────────────────────
# Normalización de productos
# ─────────────────────────────
SKU_5KG  = "BR5KG"
SKU_15KG = "BR15KG"

ALIAS_A_SKU = {
    "5": SKU_5KG, "5KG": SKU_5KG, "B5KG": SKU_5KG, "BOLSA 5": SKU_5KG, "BOLSA 5KG": SKU_5KG,
    "5 KILOGRAMOS": SKU_5KG, "BOLSA DE HIELO DE 5 KILOGRAMOS": SKU_5KG,

    "15": SKU_15KG, "15KG": SKU_15KG, "B15KG": SKU_15KG, "BOLSA 15": SKU_15KG, "BOLSA 15KG": SKU_15KG,
    "15 KILOGRAMOS": SKU_15KG, "BOLSA DE HIELO DE 15 KILOGRAMOS": SKU_15KG,
}

def normalizar_id_producto(raw) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().upper()
    return ALIAS_A_SKU.get(s, s)

def existe_producto(cur, id_producto: str) -> bool:
    cur.execute("SELECT 1 FROM productos WHERE id_producto = %s", (id_producto,))
    return cur.fetchone() is not None

# ─────────────────────────────
# Núcleo: registrar cotización
# ─────────────────────────────
def registrar_cotizacion(cliente_id: str, matricula: str, productos: list, *,
                         fecha: date | None = None,
                         dias_validez: int = 7,
                         tipo_inicial: str = "Cotización",
                         estatus_inicial: str = "Nuevo") -> int:
    """
    Inserta en 'cotizaciones' y 'detalle_cotizacion'.
    productos: lista de dicts o tuplas con:
      id_producto, descripcion, cantidad, precio_unitario, total
    """
    fecha = fecha or date.today()
    valido_hasta = fecha + timedelta(days=dias_validez)

    conn = conectar_bd()
    cur = conn.cursor()

    try:
        # Cabecera
        cur.execute("""
            INSERT INTO cotizaciones
                (fecha, valido_hasta, cliente_id, atendido_por, notas,
                 fecha_hora_creacion, creado_por, tipo, estatus)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_cotizacion
        """, (
            fecha, valido_hasta, cliente_id,
            matricula,              # atendido_por
            None,                   # notas
            datetime.now(),         # fecha_hora_creacion
            matricula,              # creado_por
            tipo_inicial, estatus_inicial
        ))
        id_cotizacion = cur.fetchone()[0]

        # Detalle
        for item in productos:
            if isinstance(item, dict):
                raw_id_producto  = item.get("id_producto")
                descripcion      = item.get("descripcion", "")
                cantidad         = int(item.get("cantidad", 0) or 0)
                precio_unitario  = float(item.get("precio_unitario", 0) or 0.0)
                total            = float(item.get("total", cantidad * precio_unitario))
            else:
                raw_id_producto, descripcion, cantidad, precio_unitario, total = item
                cantidad = int(cantidad)
                precio_unitario = float(precio_unitario)
                total = float(total if total is not None else cantidad * precio_unitario)

            id_producto = normalizar_id_producto(raw_id_producto)
            if not id_producto:
                raise ValueError("Falta id_producto en un renglón del detalle.")

            if not existe_producto(cur, id_producto):
                raise ValueError(
                    f"El producto '{raw_id_producto}' no existe (normalizado a '{id_producto}'). "
                    f"Crea el SKU en la tabla productos o corrige el ID."
                )

            cur.execute("""
                INSERT INTO detalle_cotizacion
                    (id_cotizacion, id_producto, descripcion, cantidad, precio_unitario, total)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
            """, (id_cotizacion, id_producto, descripcion, cantidad, precio_unitario, total))

        conn.commit()
        return id_cotizacion

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

# ─────────────────────────────
# Descarga de archivos generados
# ─────────────────────────────
@generar_cotizacion_bp.route("/descargar/<path:filename>")
def descargar_cotizacion(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    posibles_dirs = [
        os.path.normpath(os.path.join(base_dir, "..", "cotizaciones")),
        os.path.normpath(os.path.join(base_dir, "..", "notas_pedido")),
        os.path.normpath(os.path.join(base_dir, "cotizaciones"))
    ]
    for carpeta in posibles_dirs:
        ruta = os.path.join(carpeta, filename)
        if os.path.isfile(ruta):
            return send_from_directory(carpeta, filename, as_attachment=True)
    abort(404, description=f"Archivo no encontrado: {filename}")

# ─────────────────────────────
# UI + API en el MISMO endpoint
# ─────────────────────────────
@generar_cotizacion_bp.route("/generar", methods=["GET", "POST"])
def generar_web():
    # GET: muestra formulario web
    if request.method == "GET":
        return render_template("generar_cotizacion.html")

    # POST: acepta JSON o formulario HTML
    data = request.get_json(silent=True)

    if not data:
        # Formularios HTML (campos con [] en name)
        cliente_id = (request.form.get("cliente_id") or "").strip()
        matricula  = (request.form.get("matricula")  or session.get("usuario") or "").strip()

        ids   = request.form.getlist("id_producto[]")
        descs = request.form.getlist("descripcion[]")
        cants = request.form.getlist("cantidad[]")
        precios = request.form.getlist("precio_unitario[]")

        productos = []
        for i in range(len(ids)):
            if not ids[i].strip():
                continue
            cantidad = int(cants[i] or 0)
            pu = float(precios[i] or 0)
            productos.append({
                "id_producto": ids[i],
                "descripcion": descs[i] if i < len(descs) else "",
                "cantidad": cantidad,
                "precio_unitario": pu,
                "total": cantidad * pu
            })

        if not cliente_id:
            return render_template("generar_cotizacion.html", error="cliente_id requerido"), 400
        if not matricula:
            return render_template("generar_cotizacion.html", error="matricula requerida"), 400
        if not productos:
            return render_template("generar_cotizacion.html", error="Agrega al menos un producto"), 400

        try:
            id_cot = registrar_cotizacion(cliente_id, matricula, productos)
            # Redirige al detalle en tu módulo de gestión
            return redirect(url_for("cotizaciones_gestion.detalle_cotizacion_unico", cotizacion_id=id_cot))
        except ValueError as ve:
            return render_template("generar_cotizacion.html", error=str(ve)), 400
        except Exception:
            return render_template("generar_cotizacion.html", error="Error al registrar la cotización"), 500

    # POST JSON (API)
    cliente_id = (data.get("cliente_id") or "").strip()
    matricula  = (data.get("matricula")  or session.get("usuario") or "").strip()
    productos  = data.get("productos")

    if not cliente_id:
        return jsonify({"ok": False, "error": "cliente_id requerido"}), 400
    if not matricula:
        return jsonify({"ok": False, "error": "matricula (creado_por) requerida"}), 400
    if not productos or not isinstance(productos, (list, tuple)):
        return jsonify({"ok": False, "error": "productos debe ser una lista"}), 400

    try:
        id_cotizacion = registrar_cotizacion(cliente_id, matricula, productos)
        return jsonify({"ok": True, "id_cotizacion": id_cotizacion})
    except ValueError as ve:
        return jsonify({"ok": False, "error": str(ve)}), 400
    except Exception:
        return jsonify({"ok": False, "error": "Error al registrar la cotización"}), 500

# Aliases de compatibilidad
gen_cotizacion_bp = generar_cotizacion_bp
generar_cot_bp = generar_cotizacion_bp
