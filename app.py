from flask import Flask, session, redirect, url_for, render_template
from lotes import lotes_bp
from auth import auth_bp
from clientes import clientes_bp
from generar_cotizacion import generar_cotizacion_bp
# MODIFICACIÓN: Importar el nuevo dashboard_bp desde proyeccion
from proyeccion import dashboard_bp
from nota_pedido import nota_pedido_bp
from gestion_cotizaciones import ges_cotizaciones_bp
# NUEVO: Importar el nuevo mermas_bp
from mermas import mermas_bp

app = Flask(__name__)
app.secret_key = 'clave-super-secreta'

# Registrar módulos
app.register_blueprint(lotes_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(ges_cotizaciones_bp)
app.register_blueprint(generar_cotizacion_bp)
# MODIFICACIÓN: Registrar dashboard_bp (en lugar de proyeccion_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(nota_pedido_bp)
# NUEVO: Registrar mermas_bp
app.register_blueprint(mermas_bp)


@app.route('/')
def menu():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    # MODIFICACIÓN: Redirigir al nuevo dashboard
    return redirect(url_for('dashboard.dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)