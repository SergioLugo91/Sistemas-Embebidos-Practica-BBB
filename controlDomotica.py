from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM

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
for pin in leds.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # todos apagados inicialmente

for pin in sensores.values():
    GPIO.setup(pin, GPIO.IN)
    
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

    GPIO.output(leds[habitacion], GPIO.HIGH if estado else GPIO.LOW)
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

    pin = leds[habitacion]
    
    # Lista de pines que soportan PWM en BeagleBone Black
    pwm_pins = ["P9_14", "P9_16", "P9_21", "P9_22", "P8_13", "P8_19"]
    
    # Si intensidad es 0, apagar todo
    if intensidad == 0:
        try:
            PWM.stop(pin)
        except:
            pass
        GPIO.output(pin, GPIO.LOW)
        return jsonify({"ok": True, "habitacion": habitacion, "intensidad": intensidad})
    
    # Intentar usar PWM si el pin lo soporta
    if pin in pwm_pins:
        try:
            # Limpiar el pin primero - importante para evitar conflictos
            try:
                PWM.stop(pin)
            except:
                pass
            
            try:
                GPIO.cleanup(pin)
            except:
                pass
            
            # Iniciar PWM limpiamente
            PWM.start(pin, intensidad, 1000)
            return jsonify({"ok": True, "habitacion": habitacion, "intensidad": intensidad})
        except Exception as e:
            print(f"Error PWM en {pin} ({habitacion}): {str(e)}. Usando fallback GPIO.")
            # Si PWM falla, continuar con fallback GPIO
    
    # Fallback: usar GPIO simple on/off
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)
    return jsonify({"ok": True, "habitacion": habitacion, "intensidad": intensidad, "warning": f"PWM no disponible en {pin}, usando on/off"})

@app.route('/leer_sensores')
def leer_sensores():
    """
    Devuelve el estado de los sensores conectados.
    """
    valor_puerta = GPIO.input(sensores['puerta'])
    valor_luz = GPIO.input(sensores['luz'])

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
    for pin in leds.values():
        GPIO.output(pin, GPIO.HIGH if intensidad > 0 else GPIO.LOW)
    return jsonify({"ok": True, "intensidad": intensidad})


# ==== APAGAR TODOS LOS LEDS AL SALIR ====
@app.teardown_appcontext
def cleanup(exception=None):
    # Limpiar PWM
    for pin in leds.values():
        try:
            PWM.stop(pin)
        except:
            pass
    GPIO.cleanup()

# ==== EJECUTAR SERVIDOR ====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
