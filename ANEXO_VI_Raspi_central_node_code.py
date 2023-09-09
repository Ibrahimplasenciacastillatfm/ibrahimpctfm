# Archivo: Code_TFM_Ibrahim_Plasencia.py
# Autor: Ibrahim Plasencia Castilla
# Referencias para el código:
# Comunicacion Bluetooth--> https://github.com/karulis/pybluez/examples/simple/rfcomm-client.py
# Orientacion magnetica--> https://github.com/ControlEverythingCommunity/HMC5883/blob/master/Python/HMC5883.py
# Localizacion geográfica--> https://stackoverflow.com/questions/32191380/python-subprocess-check-output-with-pipeline
# Escritura en ficheros --> https://www.w3schools.com/python/python_file_write.asp
 
# Descripción: Código destinado a la recepción y tratamiento de datos de irradiancia y temperatura mediante comunicacion Bluetooth, y adquisición de datos de localización (GPS) y orientacion (compass)
# Fecha de creación: 2 de mayo de 2023
 
from bluetooth import *  #para trabajar con los elementos definidos en el módulo 'bluetooth'
from datetime import datetime  #para trabajar con fechas y horas
import time  #para trabajar con funciones relacionadas con el tiempo
import sys  #para trabajar con funciones y variables relacionadas con el intérprete de Python
import os  #para interactuar con el sistema operativo (acceder a archivos y directorios, etc)
import smbus  #para comunicarse con dispositivos I2C (en este caso la brújula)
import math  #para trabajar con funciones matemáticas
import subprocess  #para crear procesos secundarios y realizar operaciones en la línea de comandos
import json  #para trabajar con datos en formato JSON
 
# Matriz para almacenar los datos obtenidos en esta aplicación
datos = []
 
#Frecuencia de guardado de datos, en este caso coincidiendo con la frecuencia de recepción de mensajes de la ESP32 (500ms)
intervalo_guardado=0.5
 
#Declinación magnética (en grados) en la ubicación de los ensayos para el cálculo de la orientación magnética (brújula)- ACTUALIZAR SI ES NECESARIO (fuente: https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml?)
declination = 0.17 # MADRID
#declination = -3.57 # ISLAS CANARIAS
 
 
#Función para guardar los datos obtenidos en un archivo de texto (txt) para su posterior tratamiento y análisis
def guardar_datos(lat, lon, orient, cardinal_direction, irradiancia, temperatura, DT): #La función recibe como argumentos la ubicación y orientación obtenidas del módulo BN-880 GPS. En cuanto a los datos de irradiancia y temperatura los toma de la matriz global "datos"
 
    ruta = "/home/ibrahimplasenciatfm/datos.txt" #Ruta específica donde se desea almacenar el fichero txt creado (MODIFICAR SEGÚN UBICACIÓN DESEADA)
    encabezado1 = "Datos suministrados por el nodo sensor (ESP32, vía Bluetooth), y el módulo GPS (comunicacón I2C/UART, Raspberry Pi) para el análisis de la Irradiancia Solar recibida en un Vehículo con Integración Fotovoltaica, en un determinado periodo de conducción por carretera, y estudio de la influencia de la temperatura de la célula solar en los resultados obtenidos"
    encabezado2 = "Fecha Hora Latitud[°] Longitud[°] Orientación Geográfica[°] IrradianciaSolar[W/m2] Temperatura[°] Desv.Temperatura[°]"
   
    if not os.path.isfile(ruta): #Se verifica si el archivo de texto ya existe o no. Si no existe, se ejecutan las siguientes líneas
       
        with open(ruta, "w") as file: #se abre el archivo en 'modo escritura' y se escriben los encabezados definidos anteriormente
            file.write(encabezado1 + "\n")
            file.write(encabezado2 + "\n")
           
    datos_guardar = datos.copy() #Se crea una copia de la lista de datos recolectados previamente
   
    with open(ruta, "a") as file: #se abre el archivo en 'modo de escritura adicional', lo que significa que los nuevos datos se agregan al final sin sobreescribir los datos existentes
        for fila in datos:
            fila_str=datetime.now().strftime("%d-%m-%Y %H:%M:%S ") #Se obtienen la fecha y hora actuales, que se asocian a cada conjunto de datos recogido
            fila_str += f"{lat:.6f} {lon:.6f} {orient:.2f} {cardinal_direction} {irradiancia:.2f} {temperatura:.2f} {DT:.2f}" #Se añaden a continuación datos de latitud, longitud, orientación, dirección cardinal, irradiancia, temperatura y desviación de temperatura
            file.write(fila_str + "\n") # se escribe el conjunto de datos y se introduce salto de línea en el archivo
   
        file.flush() #se fuerza la escritura en el archivo datos.txt
   
    datos.clear() #se vacía la lista 'datos' después de que han sido escritos para asegurarnos de que no vuelvan a ser incluidos en futuras escrituras
           
    #Se comprueba que el archivo se ha creado correctamente
    if os.path.isfile(ruta):
       
        print("Archivo guardado en: ", ruta)
       
    else:
       
        print("No se pudo crear el archivo en la ruta especificada.")

#Función para obtener la ubicación GPS de la Raspberry Pi (latitud y longitud) que viaja junto al dispositivo sensor construido
def get_gps_location():
   
    #Se inicializan las variables correspondientes a los datos de latitud y longitud con el valor '0'porque aun no se ha obtenido la ubicación
    lat = 0
    lon = 0
   
    try:
        # Se ejecuta el comando 'gpspipe' para obtener los datos del GPSD (servicio empleado en Raspberry para obtener la ubicación GPS)
        cmd = "gpspipe -w -n 5"  # Lee 5 mensajes del GPSD (SE PUEDE AJUSTAR ESTE VALOR, mínimo 5 mensajes)
        result = subprocess.check_output(cmd, shell=True, text=True) #se ejecuta el comando anterior en el sistema operativo y se captura la salida
 
        # Se analiza la salida JSON  del comando anterior para obtener los datos de ubicación. Se obtienen tantas líneas JSON como mensajes del GPSD haya. Cada línea JSON contiene un única objeto que representa un conjunto de datos estructurado en formato JSON
        for line in result.strip().split("\n"): #se itera sobre cada línea JSON
            data = json.loads(line) #Se convierte cada línea en un diccionario Python para almacenar pares clave-valor, de modo que luego se accede a la info de latitud y longitud mediante las claves 'lat' y 'lon' respectivamente
            if "lat" in data and "lon" in data:
                lat = data["lat"]
                lon = data["lon"]
                return lat, lon
 
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}") #en caso de que haya un error en el proceso
    except json.JSONDecodeError as e:
        print(f"Error al analizar el JSON: {e}") #en caso de obtener una salida no válida
 
    return lat, lon
#Función para calcular la orientación magnética (brújula) a partir de las lecturas del magnetómetro HMC5883L incorporado en el módulo BN-880 GPS empleado
def calculate_orient(x, y):
   
    orient_rad = math.atan2(y, x) #se calcula el ángulo en radianes (orientación en coordenadas polares) en función de las componentes X, Y del campo magnético. Es el ángulo entre el punto (x,y) y el eje X positivo en sentido antihorario
    orient_deg = math.degrees(orient_rad) #Se convierte el ángulo a grados
    orient_deg=orient_deg -declination #Se resta la declinación magnética al valor obtenido, para tener en cuenta la diferencia entre el norte magnético y el norte geográfica en la ubicación donde se realizan los ensayos, ajustando el ángulo a la referencia del norte geográfico
   
    #Se ajusta el ángulo al rango de 0º a 360º
    if orient_deg < 0:
        orient_deg += 360.0
       
    return orient_deg
 
#Función para obtener las componentes del campo magnético a través del bus I2C, y obtener la orientación magnética usando la función anterior 'calculate_orient'
def get_orient():
   
    #Obtenemos el bus I2C (sudo i2cdetect -y 1)
    bus = smbus.SMBus(1) #se crea instancia 'smbus.SMBus' para interactuar con el bus I2C empleado para la comunicación con el sensor HMC5883L conectado a través del bus I2C
   
    # HMC5883L address, 0x1E(30) - dirección I2C del sensor
    # Select configuration register A, 0x00(00) - Dirección del registro de configuración del sensor
    #   0x60(96)    Normal measurement configuration, Data output rate = 0.75 Hz - El valor 0x60 configura el sensor para realizar mediciones normales con una frecuencia de 0.75Hz
    #bus.write_byte_data(0x1E, 0x00, 0x60) - DESCOMENTAR PARA FUNCIONAR EN ESTE MODO
    # HMC5883 address, 0x1E(30) - dirección I2C del sensor
    # Select mode register, 0x02(02) - Registro de modo del sensor
    #   0x00(00)    Continuous measurement mode - Configuración del sensor en modo de medición continua, de manera constante sin detenerse
    bus.write_byte_data(0x1E, 0x02, 0x00) #COMENTAR SI SE VA A EMPLEAR EL OTRO MODO
   
    try:
        # HMC5883 address, 0x1E(30) - dirección I2C del sensor
        # Read data back from 0x03(03), 6 bytes - Se leerá un total de 6 bytes de datos del sensor, comenzando por la dirección 0X03 hasta la dirección 0X08
        # X-Axis MSB, X-Axis LSB, Z-Axis MSB, Z-Axis LSB, Y-Axis MSB, Y-Axis LSB - LOs datos de campo magnético medidos en cada eje se almacenan en 2 bytes cada uno (MSB - Most Significant Byte y LSB - Less Significant Byte)
        data = bus.read_i2c_block_data(0x1E, 0x03, 6) #se leen 6 bytes de datos del sensor comenzando por la dirección 0x03. Estos bytes contienen las lecturas de los ejes X, Y, Z del magnetómetro
        xMag = data[0] * 256 + data[1] -201
        if xMag > 32767:
            xMag -= 65536

        zMag = data[2] * 256 + data[3]
        if zMag > 32767:
            zMag -= 65536

        yMag = data[4] * 256 + data[5] +432
        if yMag > 32767:
            yMag -= 65536
        # Se obtiene la orientación (brújula) a partir de las lecturas de campo magnético en los ejes X e Y usando la función anteriormente definida y los valores de campo magnético extraídos
        orient = calculate_orient(xMag, yMag)
   
        return orient #valor de orientación calculada en grados

    except KeyboardInterrupt: 
        pass

#Función para obtener cardinal correspondiente a un ángulo de orientación determinado
def get_cardinal_direction(orient_deg):
   
    directions= ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"] #Lista de direcciones cardinales en orden
    index=round((orient_deg % 360)/22.5) #Se calcula el indice de la lista anterior correspondiente al ángulo de orientación determinado. Se calcula el resto de dividir el ángulo por 360, asegurandose de que está en el rango de 0 a 359; se divide entre 22.5 y se redondea al valor más cercano, dando un valor de índice entre 0 y 15, que es el rango válido para la lista anterior.
   
    return directions[index % 16] #se devuelve la dirección cardinal correspondiente la índice calculado, asegurando de nuevo que está en el rango válido
   
#Función para recoger los datos recibidos del módulo BN-880 (latitud, longitud, orientación) y dirección cardinal y mediante conexión Bluetooth con la ESP32 (irradiancia, temperatura y DT)
def rx_and_echo():
   
    sock.send("\nSend data\n") #Envía un mensaje de confirmación al dispositivo ESP32 mediante conexión Bluetooth
    tiempo_ultima_recepcion=time.time() #Se toma el valor de tiempo actual en segundos
   
    try:
        while True: #se ejecuta un bucle infinito hasta que se interrumpa la comunicación Bluetooth
           
            data = sock.recv(buf_size) #se reciben datos del socket Bluetooth y se almacenan en la variable 'data'
           
            if data:
               
                data_str=data.decode("utf-8").strip() #Se decodifican los bytes a una cadena de texto utilizando el formato UTF-8 Y eliminando los espacios en blanco al inicio y final de la cadena
               
                #print(data_str) #DESCOMENTAR SI SE DESEAN VER LOS DATOS BRUTOS QUE LLEGAN DE LA ESP32 MEDIANTE BLUETOOTH
               
                # Se separa la cadena de texto en palabras individuales separadas por espacios. Se envían los datos desde la ESP32 separados por espacios, de modo que la Raspberry pueda identificar cada dato con facilidad
                valores = data_str.split()
               
                # Se verifica si se han recibido los tres valores necesarios de la ESP32 (irradiancia, temperatura y desviación de temperatura)
                if len(valores) >= 3:
                   
                    # Se extraen los valores de Irradiancia, Temperatura y DT (desviación temperatura) y se cambian a tipo punto flotante, ya que vienen en formato 'String'
                    irradiancia = float(valores[0])
                   
                    temperatura = float(valores[1])
                    DT = float(valores[2])
                   
                    #Se obtienen los datos de ubicación (latitud, longitud), orientación (brújula) y dirección cardinal
                    lat, lon = get_gps_location()
                    orient = get_orient()
                    cardinal_direction = get_cardinal_direction(orient)
                   
                    # Se agregan los valores a la matriz general 'datos'
                    datos.append([lat, lon, orient, cardinal_direction, irradiancia, temperatura, DT])
                   
                    # Se imprimen los valores recibidos en la consola con su etiqueta para visualizar los datos recibidos en tiempo real
                    if lat!=0 and lon !=0:
                        print(f"\nLatitud: {lat:.6f}, Longitud: {lon:.6f}")
                       
                    else:
                        print("No se pudo obtener la ubicación")
                       
                    print(f"Orientación (brújula): {orient:.2f}ºC")
                    print("Dirección cardinal:", cardinal_direction)
                    print(f"Irradiancia Solar: {irradiancia:.2f}W/m2")
                    print(f"Temperatura: {temperatura:.2f}ºC")
                    print(f"Desviación Temperatura: {DT:.2f}ºC")
                   
                    #Se toma el valor de tiempo actual transcurrido
                    tiempo_actual=time.time()
                   
                    #Se guardan los datos si ha pasado el intervalo de tiempo asignado para el guardado de datos (500ms en este caso)
                    if tiempo_actual - tiempo_ultima_recepcion >= intervalo_guardado:
                        guardar_datos(lat, lon, orient, cardinal_direction, irradiancia, temperatura, DT)
                        tiempo_ultima_recepcion=tiempo_actual
                       
    #En caso de pérdida en la conexión Bluetooth, se cierra el socket y guarda los datos, informando además de ello
    except BluetoothError:
        sock.close()
        guardar_datos(lat, lon, orient, cardinal_direction, irradiancia, temperatura, DT)
        print("Se produjo un error de conexión. Los datos se han guardado en el archivo")
 
           
#GESTIÓN DE LA COMUNICACIÓN BLUETOOTH
 
#Se define la dirección MAC de la ESP32 (server) al que se conecta la Raspberry Pi, y que lo identificada de forma única
addr= "C0:49:EF:69:A6:3A" #Dirección extraída mediante la función definida en la ESP32
service_matches = find_service( address = addr ) #Se busca el servicio asociado a la dirección MAC especificada. La función 'find_service' tratará de encontrar los servicios disponibles que pueden ser empleados para establecer la conexión Bluetooth
 
buf_size=1024 #Se define el tamaño del buffer de recepción de datos en 1024 bytes
 
if len(service_matches) == 0: #Si no se en encuntran servicios asociados a la dirección MAC especificada, se imprime mensaje que avisa de ello
    print("Servicio no encontrado=(")
    sys.exit(0) #Se cierra el programa si no se encuentra el servicio
 
for s in range(len(service_matches)): #se itera sobre la lista de servicios encontrados y se imprimen los detalles
    print("\nServicios encontrados: [" + str(s) + "]:")
    print(service_matches[s])
   
first_match = service_matches[0] #Se selecciona el primer servicio encontrado como el servicio con el que se establecerá la conexión Bluetooth
port = first_match["port"] #Se obtiene el número de puerto asociado al servicio
name = first_match["name"] #Se obtiene el nombre del servicio
host = first_match["host"] #Se obtiene el host (dirección IP) asociado al servicio
 
print("Conectando a \"%s\" en %s" % (name, host)) #se imprime un mensaje que indica el nombre del servicio al que se estña tratando de conectar y su IP
 
sock=BluetoothSocket(RFCOMM) #Se crea el objeto 'BluetoothSocket' para la comunicación Bluetooth utilizando el protocolo RFCOMM
sock.connect((host, port)) #Se realiza la conexión Bluetooth usando la dirección IP y el número de puerto
 
print("Conectado") #Se confirma la conexión Bluetooth establecida
 
try:
    rx_and_echo() #Se ejecuta la función principal 'rx_and_echo' que recibe y procesa los datos procedentes de la ESP32 y recoge los datos obtenidos con las demás funciones para crear la matriz global de datos que se pondrá a disposición el usuario en un fichero datos.txt
 
#Si se produce interrupción de teclado (Ctrl+C) finaliza el programa cerrando el socket Bluetooth
except KeyboardInterrupt:
    pass
   
finally:
    sock.close()
