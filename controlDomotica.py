from flask import Flask, render_template, request, jsonify, send_from_directory
import os
#import Adafruit_BBIO.GPIO as GPIO
#import Adafruit_BBIO.PWM as PWM

app = Flask(__name__)

# ==== CONFIGURACIÓN DE PINES ====
leds = {
    "baño_master": "P8_11",
    "pasillo_master": "P8_12",
    "pasillo": "P8_13",
    "sala": "P9_14", #P8_14
    "cocina": "P8_15",
    "dormitorio_master": "P8_16",
    "dormitorio_secundario": "P8_17"
}

sensores = {
    "puerta": "P8_18",
    "luz": "P8_19"
}

# ==== INICIALIZAR PINES ====
#for pin in leds.values():
#    GPIO.setup(pin, GPIO.OUT)
#    GPIO.output(pin, GPIO.LOW)  # todos apagados inicialmente

#for pin in sensores.values():
#    GPIO.setup(pin, GPIO.IN)
    
# ==== RUTAS FLASK ====
@app.route('/sources/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'templates', 'sources'), filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_led', methods=['POST'])
def set_led():
    """
    Endpoint para encender/apagar un LED.
    Espera JSON: { "habitacion": "sala", "estado": true }
    """
    data = request.get_json()
    habitacion = data.get('habitacion')
    estado = data.get('estado', False)

    if habitacion not in leds:
        return jsonify({"error": "Habitación no reconocida"}), 400

    #GPIO.output(leds[habitacion], GPIO.HIGH if estado else GPIO.LOW)
    return jsonify({"ok": True, "habitacion": habitacion, "estado": estado})

@app.route('/set_intensity', methods=['POST'])
def set_intensity():
    """
    Endpoint para ajustar la intensidad de un LED usando PWM.
    Espera JSON: { "habitacion": "sala", "intensidad": 75 }
    """
    data = request.get_json()
    habitacion = data.get('habitacion')
    intensidad = int(data.get('intensidad', 0))

    if habitacion not in leds:
        return jsonify({"error": "Habitación no reconocida"}), 400

    # Por ahora, solo encendemos si intensidad > 0:
    #PWM.start(leds[habitacion], intensidad)
    return jsonify({"ok": True, "habitacion": habitacion, "intensidad": intensidad})

@app.route('/leer_sensores')
def leer_sensores():
    """
    Devuelve el estado de los sensores conectados.
    """
    # Simulación de lectura analógica / digital (sustituir por GPIO.input / ADC real)
    # En un escenario real podrías tener: valor_puerta = GPIO.input(sensores['puerta'])
    # o lectura ADC para luz ambiente.
    valor_puerta = 600  # Ejemplo: valor crudo del sensor de puerta
    valor_luz = 300     # Ejemplo: valor crudo del sensor de luz

    # Umbrales (ajusta según calibración real). Podrías moverlos a variables de entorno.
    UMBRAL_PUERTA = 500  # < umbral => puerta abierta
    UMBRAL_LUZ = 500     # > umbral => hay luz (día)

    puerta_abierta = valor_puerta < UMBRAL_PUERTA
    luz_dia = valor_luz > UMBRAL_LUZ

    payload = {
        # Valores crudos
        "puerta": valor_puerta,            # compatibilidad con código anterior
        "luz": valor_luz,                 # compatibilidad con código anterior
        # Nuevos campos semánticos
        "puerta_valor": valor_puerta,
        "puerta_abierta": puerta_abierta,
        "luz_valor": valor_luz,
        "luz_dia": luz_dia,
        "umbrales": {"puerta": UMBRAL_PUERTA, "luz": UMBRAL_LUZ}
    }
    return jsonify(payload)

@app.route('/set_all', methods=['POST'])
def set_all():
    data = request.get_json()
    intensidad = int(data.get('intensidad', 0))
    #for pin in leds.values():
    #    GPIO.output(pin, GPIO.HIGH if intensidad > 0 else GPIO.LOW)
    return jsonify({"ok": True, "intensidad": intensidad})


# ==== APAGAR TODOS LOS LEDS AL SALIR ====
@app.teardown_appcontext
def cleanup(exception=None):
    pass
    #GPIO.cleanup()

# ==== EJECUTAR SERVIDOR ====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
