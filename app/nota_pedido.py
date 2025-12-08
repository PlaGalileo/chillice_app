# nota_pedido.py
from flask import Blueprint, send_from_directory
from generar_nota_pedido import generar_nota_pedido
import os

nota_pedido_bp = Blueprint('nota_pedido', __name__, url_prefix='/pedido')

@nota_pedido_bp.route('/descargar/xlsx/<int:cotizacion_id>')
def descargar_xlsx_pedido(cotizacion_id):
    ruta = generar_nota_pedido(cotizacion_id)  # genera o regenera XLSX y PDF
    return send_from_directory(os.path.dirname(ruta), os.path.basename(ruta), as_attachment=True)

@nota_pedido_bp.route('/descargar/pdf/<int:cotizacion_id>')
def descargar_pdf_pedido(cotizacion_id):
    ruta = generar_nota_pedido(cotizacion_id)
    nombre_pdf = os.path.splitext(os.path.basename(ruta))[0] + ".pdf"
    return send_from_directory(os.path.dirname(ruta), nombre_pdf, as_attachment=True)
