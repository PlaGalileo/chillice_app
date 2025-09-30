from generar_cotizacion import registrar_cotizacion, generar_cotizacion

matricula = 'CHILL001'
cliente_id = 'ICE001'
productos = [
    ['Bolsa 5kg', 10, 24.00, True],
    ['Bolsa 15kg', 5, 44.00, True]
]

# 1. Registrar en base de datos y obtener ID
id_cotizacion = registrar_cotizacion(cliente_id, matricula, productos)

# 2. Generar archivo Excel con ese ID
generar_cotizacion(matricula, cliente_id, id_cotizacion, productos)
