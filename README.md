# ibrahimpctfm
Proyecto destinado al Diseño y Desarrollo de un Sensor IoT comunicado con Nodo Central para la Medida del Recurso Solar en Vehículos con Integración Fotovoltaica

En el repositorio se incluye:

- Código implementado en el sensor IoT, basado en un microcontrolador ESP32 Bluetooth & Wifi Battery (programado en Arduino IDE) para la recogida de datos de irradiancia solar y temperatura empleando un módulo solar fotovoltaico de 0.3W y un termistor NTC.
- Código implementado en el nodo central para la recogida y registro de lso datos enviados por el sensor IoT (irradiancia solar y temperatura), así como los datos de ubicación (latitud y longitud) y orientación (magnetómetro HMC5883L) recibidos de un módulo BN-880 GPS.
