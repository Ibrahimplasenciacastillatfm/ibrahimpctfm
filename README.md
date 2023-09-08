# ibrahimpctfm
Proyecto destinado al Diseño y Desarrollo de un Sensor IoT comunicado con Nodo Central para la Medida del Recurso Solar en Vehículos con Integración Fotovoltaica

En el repositorio se incluye:

- ESP32_Sensor_IoT_code.ino --> Código implementado en el sensor IoT, basado en un microcontrolador ESP32 Bluetooth & Wifi Battery (programado en Arduino IDE, C++) para la recogida de datos de irradiancia solar y temperatura empleando un módulo solar fotovoltaico de 0.3W y un termistor NTC.
- Raspi_central_node_code.py --> Código implementado en el nodo central para la recogida y registro de lso datos enviados por el sensor IoT (irradiancia solar y temperatura), así como los datos de ubicación (latitud y longitud) y orientación (magnetómetro HMC5883L) recibidos de un módulo BN-880 GPS. Basado en una Raspberry Pi 3 Model B v1.2 (programado en Python).
- Datos empleados para la calibración 
