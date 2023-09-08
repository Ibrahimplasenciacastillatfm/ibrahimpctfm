# ibrahimpctfm
Proyecto destinado al Diseño y Desarrollo de un Sensor IoT comunicado con Nodo Central para la Medida del Recurso Solar en Vehículos con Integración Fotovoltaica

En el repositorio se incluyen los siguientes archivos:

- Anexo_IV_Hojas_de_caracteristicas_componentes --> Enlaces a las hojas e caracteristicas de los componentes adquiridos para el diseño
- Anexo_VI_ESP32_Sensor_IoT_code.ino --> Código implementado en el sensor IoT, basado en un microcontrolador ESP32 Bluetooth & Wifi Battery (programado en Arduino IDE, C++) para la recogida de datos de irradiancia solar y temperatura empleando un módulo solar fotovoltaico de 0.3W y un termistor NTC.
- Anexo_VI_Raspi_central_node_code.py --> Código implementado en el nodo central para la recogida y registro de lso datos enviados por el sensor IoT (irradiancia solar y temperatura), así como los datos de ubicación (latitud y longitud) y orientación (magnetómetro HMC5883L) recibidos de un módulo BN-880 GPS. Basado en una Raspberry Pi 3 Model B v1.2 (programado en Python).
- ANEXO_VII_Calibracion_Modulo_Solar_Fotovoltaico --> Datos y resultados obtenidos de la calibración del Módulo Solar Fotovoltaico
-  ANEXO_VIII_Calibracion_Canales_ESP32 --> Datos y resultados obtenidos de la calibración de los canales del ESP32 empleados para la medida de la irradiancia solar y la temperatura (pines 26 y 35).
-  Archivos de diseño de la carcasa diseñada para el dispositivo sensor (en formato .ipt y .stl). El formato .ipt es el empleado por el programa Inventor Professional (se ha usado al versión 2021), mientras que el formato .stl es el empleado para las impresoras 3D. El diseño se compone de 4 piezas:
    - Pieza_base_TFM --> Parte inferior de la carcasa a la que se fija la electrónica
    - Pieza_tapa_TFM --> Parte superior de cierre del conjunto y soporte para el módulo solar fotovoltaico
    - Tapa_1_TFM --> Pieza de cierre del hueco del interruptor del ESP32
    - Tapa_2_TFM --> Pieza de cierre del hueco del conector USB del ESP32
- ANEXO_IX_Resultados_Prueba_Carretera --> Datos registrados por el sistema diseñado y desarrollado en este TFM como prueba de validación del sistema. Se corresponde con los datos recogidos en una prueba en carretera con el equipo montado en un vehículo real, bajo unas condiciones de conducción reales.
