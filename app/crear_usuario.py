import bcrypt
from utils.db import conectar_bd

# --- Parámetros de entrada ---
matricula = 'CHILL001'
password_plana = 'admin001'

# --- Hashear la contraseña ---
password_hash = bcrypt.hashpw(password_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# --- Conexión a la base de datos ---
conn = conectar_bd

cur = conn.cursor()

# --- Actualizar contraseña ---
cur.execute("""
    UPDATE public.rrhh_empleados
    SET password_hash = %s
    WHERE id_empleado = %s
""", (password_hash, matricula))

# --- Finalizar ---
conn.commit()
cur.close()
conn.close()
print(f"✅ Contraseña actualizada para el empleado {matricula}.")
