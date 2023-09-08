//Autor: Ibrahim Plasencia Castilla
//Referencias:
//https://docs.espressif.com/projects/esp-idf/en/latest/esp32/
// https://github.com/espressif/arduino-esp32/blob/master/libraries/BluetoothSerial/src/BluetoothSerial.h
//https://www.cplusplus.com/reference/cmath/pow/
//https://randomnerdtutorials.com/esp32-bluetooth-classic-arduino-ide/
//https://randomnerdtutorials.com/esp32-adc-analog-read-arduino-ide/
//https://en.wikipedia.org/wiki/Thermistor#Calculation_of_temperature_and_thermal_tolerances

//Descripción: Código empleado para conocer la dirección MAC del dispositivo ESP32, establecer una comunicación Bluetooth con otro dispositivo, obtener datos de irradiancia y temperatura, asi como del error cometido en el cálculo de dicha temperatura, su envío a través de Bluetooth, y control del estado de LEDs de encendido/apagadom y de estado de conexión Bluetooth
//Fecha de creación: 27 de marzo de 2023

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//Librerías para el ESP32
#include "BluetoothSerial.h" //Librería que contiene las declaraciones y definiciones necesarias para trabajar con Bluetooth en el ESP32
#include "esp_bt_device.h" //Librería que contiene el archivo de cabecera "esp_bt_device.h" que contiene las funciones y definiciones relacionadas con el manejo del Bluetooth en el ESP32
#include "math.h" //Librería que contiene funciones matemáticas, como la función "pow()"

//Comprobación de si la configuración Bluetooth está habilitada antes de compilar el código
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED) //se comprueba que están definidos los macros necesarios
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it //si no están habilitados los macros se pide al usuario que ejecute "make menuconfig" para habilitarlo
#endif

BluetoothSerial SerialBT; //Se crea instancia llamada SerialBT de la clase BluetoothSerial, empleada para establecer y administrar la comunicación Bluetooth

//Obtención de la dirección MAC del dispositivo ESP32 en formato hexadecimal, para identificarlo dentro de la red ("XX:XX:XX:XX:XX:XX")
void printDeviceAddress(){

  const uint8_t* point = esp_bt_dev_get_address(); //esta función devuelve un puntero a una matriz que contiene los bytes de la dirección MAC

  for (int i=0; i<6; i++){ //se itera sobre los 6 bytes de los que se compone la dirección MAC (en redes Ethernet y Bluetooth la dirección MAC se compone de 6 bytes, donde cada byte representa un valor hexadecimal)

    char str[3]; //arreglo de 3 caracteres (2 para el valor hezadecimal y 1 para el terminador nulo '\0' para marcar el final)

    sprintf(str, "%02X", (int)point[i]); //Se imprimen los bytes de la dirección MAC, de al menos dos dígitos, y si es solo uno, se completa con ceros a la izquierda
    Serial.print(str); //Se imprime la cadena a través de la UART de la placa ESP32

    if(i<5){
      Serial.print(":"); //entre byte y byte de la dirección MAC se incluye separador ":"
    }
  }
}

// Definición de pines empleados
const int pinIrradiancia = 26;
const int pinTemperatura = 35;
const int LED_ON_OFF = 16; //LED de estado de alimentación de la placa ("HIGH-encendida" y "LOW-apagada")
const int LED_BT = 17; //LED de estado de conexión Bluetooth ("HIGH- conectado" y "LOW-desconectado")

//Variables asociadas con el encendido de los LEDs
bool isConnected = false; //Variable que indica que si la placa está conectada a Bluetooth o no

//Variables asociados a la cuenta de tiempo transcurrido
unsigned long tiempoAnterior = 0;
const unsigned long intervalo = 500; // Intervalo de tiempo entre lecturas en milisegundos (en este caso, 500ms)

//Variables globales asociados a la lectura de la irradiancia solar
const float Vmax=3.3; //Tension de alimentación de referencia
const float Kirrad = 53.252; //cte de calibración de la célula solar (relación irradiancia solar/tensión de salida célula solar obtenida mediante cañibración experimental con piranómetro)
const float Gain = 106.50; //Ganancia calculada para el amplificador de instrumentación (Vout/Vin)
const float Kti=1.0125; //Cte de calibración del pin de entrada de la ESP32 asociado al canal de irradiancia (pin 26)

//Variables globales asociados a la lectura de temperatura extraídas de la documentación de referencia para el sensor empleado
const int R1= 4700; //Resistencia de 4.7 kOhm (resistencia de referencia a 25 grados centígrados)
const int Bvalue= 3977; //Valor de B25/85 (tolerancia en B) extraído de la docu de referencia
const float X = 5; //[%] Tolerancia a una temperatura de referencia de 25ºC
const float Ktt=1.0221; //cte de calibración del pin de la ESP32 asociado al canal de temperatura (pin 35)

//Coeficientes para el cálculo de temperatura (extraído del catálogo de termistores de "Philips Components" - NTC thermistors, accuracy line 2322 640 6... )
const float A= 3.353832e-03;
const float B= 2.569355e-04;
const float C= 2.626311e-06;
const float D= 0.675278e-07;

//CALCULO DE LA DESVIACIÓN DE TEMPERATURA CON RESPECTO A LA TEMPERATURA NOMINAL
//Se define la tabla de valores que relaciona la temperatura calculada con la desviación de resistencia debido a la tolerancia en B (Y), y el coeficiente de temperatura (TC)
//(extraída de las columnas "Tamb", "AR DUE TO B-TOLERANCE (%)" y "TC (%/K)" de la "Table 3" del catálogo de termistores de "Philips Components" - NTC thermistors, accuracy line 2322 640 6... ))

float tabla[][3] ={ //tabla donde cada fila tiene 3 elementos flotantes
    {0, 0.89, 5.08},
    {5, 0.70, 4.92},
    {10, 0.52, 4.78},
    {15, 0.34, 4.64},
    {20, 0.17, 4.50},
    {25, 0.00, 4.37},
    {30, 0.16, 4.25},
    {35, 0.32, 4.13},
    {40, 0.47, 4.02},
    {45, 0.62, 3.91},
    {50, 0.77, 3.80},
    {55, 0.91, 3.70},
    {60, 1.05, 3.60},
    {65, 1.18, 3.51},
    {70, 1.31, 3.42},
    {75, 1.44, 3.33},
    {80, 1.57, 3.25},
    {85, 1.69, 3.16},
    {90, 1.81, 3.09},
    {95, 1.93, 3.01},
    {100, 2.04, 2.94}
};

int tablaSize=sizeof(tabla) / sizeof(tabla[0]); //se obtiene el número de elementos en el arreglo "tabla" como el cociente entre el tamaño total del arreglo y el tamaño de un elemento en bytes

//Función que recibe como entrada la tabla anterior y el valor de temperatura calculado, y devuelve los valores Y (Second_column_interp), TC (Third_column_interp) para el cálculo de la desviación de temperatura DT con respecto al valor nominal
void buscar_valor_tabla(float tabla[][3], int tablaSize, float Temperatura, float& Y, float& TC){ //Los parámetros "Y" y "TC" se pasan como parámetros de salida de tipo flotante por referencia "float& ", lo que significa que los valores se modifican dentro de la función y dichos cambios serán visibles fuera de ella, en el lugar en el que se llamó
    //Búsqueda del valor exacto en la tabla
    for (int i = 0; i < tablaSize; i++) {
      if (abs(tabla[i][0] - Temperatura)<0.2){ //aquí se indica que si la diferencia entre el valor de temperatura calculado, y el mostrado en la Tabla es menor a 0.1ºC, puede tomar directamente los valores de Y, TC correspondientes (es una comparación de igualdad aproximada)
        Y = tabla[i][1];
        TC = tabla[i][2];  //Se devuelven los valores de las otras dos columnas en función del valor de temperatura
        return;
      }
    }

    //Interpolación lineal si no se encuentra el valor exacto de temperatura en la tabla
    for (int i = 0; i < tablaSize - 1; i++) {
      if (tabla[i][0] < Temperatura && Temperatura < tabla[i + 1][0]) {

        //Interpolación lineal para obtener el valor de Y (resistance deviation due to B-tolerance)
        float temp1 = tabla[i][0];
        float Y1 = tabla[i][1];
        float temp2 = tabla[i + 1][0];
        float Y2 = tabla[i + 1][1];
        Y = Y1 + (Y2 - Y1) * (Temperatura - temp1) / (temp2 - temp1);

        //Interpolación lineal para obtener el valor de TC (temperature coefficient)
        float TC1 = tabla[i][2];
        float TC2 = tabla[i + 1][2];
        TC = TC1 + (TC2 - TC1) * (Temperatura - temp1) / (temp2 - temp1);

        return;
      }
    }

  // Retorno de un valor inválido si el valor está fuera del rango de la tabla, como marcadores
  Y = -1.0;
  TC = -1.0;
}

void setup() {

  //Se inicializa el LED de encendido/apagado a nivel alto
  pinMode(LED_ON_OFF, OUTPUT);
  digitalWrite(LED_ON_OFF, HIGH); //Al alimentar el sistema, se va a encender el LED, y al desconectarlo se va a apagar

  //CONFIG COMUNICACIÓN BLUETOOTH
  //Se inicializa la comunicación Serial
  Serial.begin(115200); //velocidad de la transmisión de datos en baudios
  Serial.println("\n---Start---\n");
  SerialBT.begin("ESP32"); //Nombre del dispositivo Bluetooth
  
  Serial.println("El dispositivo se ha iniciado, ¡ahora puedes emparejarlo mediante Bluetooth!");
  Serial.println("Nombre del dispositivo: ESP32");
  Serial.print("BT MAC: ");
  printDeviceAddress(); //dirección MAC del dispositivo
  Serial.println();//Se imprime salto de línea

  //Mantener apagado el LED_BT al inicio, hasta que no se establezca el emparejamiento con el otro dispositivo
  pinMode(LED_BT, OUTPUT);
  digitalWrite(LED_BT, LOW);

  //Configuración de los pines asociados con la lectura de irradiancia y temperatura como entradas
  pinMode(pinIrradiancia, INPUT);
  pinMode(pinTemperatura, INPUT);
}

void loop() {

  //Se obtiene el tiempo actual transcurrido
  unsigned long tiempoActual = millis();

  //Se verifica si ha pasado el intervalo de tiempo deseado entre tomas de datos
  if (tiempoActual - tiempoAnterior >= intervalo) {

    //MEDIDA DE IRRADIANCIA SOLAR
    int valorADCIrrad = analogRead(pinIrradiancia); //se obtiene la lectura del ADC en el pin al que se conecta el módulo solar
    float valorTensionIrrad = (valorADCIrrad *Vmax / 4095)*Kti; // Se traduce el valor obtenido del conversor ADC en un valor de tensión. Se divide el valor de salida del ADC entre 4095, porque el ADC es de 12 bits, y se multiplica por 3.3V porque el sistema se alimenta con 3.3V (valorde tensión de referencia)
    float Irradiancia = valorTensionIrrad *pow(10,3) /Gain *Kirrad; //Se obtiene el dato de irradiancia solar

    //MEDIDA DE TEMPERATURA
    int valorADCTemp = analogRead(pinTemperatura); //se obtiene la lectura del ADC en el pin al que se conecta el termistor
    float valorTensionTemp = (valorADCTemp *Vmax / 4095)*Ktt; //Seria el denominado Vadc en la memoria
    float R2=(valorTensionTemp *R1)/(Vmax-valorTensionTemp); //Resistencia del termistor (NTC) que se traduce en un valor de temperatura
    //Cálculo de la temperatura nominal usando la ecuación de Steinhart-Hart
    float E = log(R2/R1);
    float TemperaturaK = pow(A + B*E + C*pow(E,2) + D*pow(E,3),-1); //Temperatura nominal en Kelvin (K) en función de la resistencia R2 del termistor (NTC)
    float Temperatura= TemperaturaK - 273.15; //Temperatura en ºC

    //Cálculo de la desviación de temperatura con respecto a la nominal
    float Y, TC;
    buscar_valor_tabla(tabla, tablaSize, Temperatura, Y, TC);
    float Z = X+Y;
    float DT = Z/TC; //Desviación de temperatura calculada

    // Envío de los valores de irradiancia y temperatura en un ÚNICO mensaje Bluetooth
    String mensaje = String(Irradiancia) + " " + String(Temperatura) + " " + String(DT)+ " ";
    SerialBT.print(mensaje);

    // Actualizar el tiempo anterior
    tiempoAnterior = tiempoActual;
  }

  //CONTROL DEL ENCENDIDO DEL LED DE ESTADO DE LA CONEXIÓN BLUETOOTH
  //Código para verificar la conexión Bluetooth y controlar el encendido de LED_BT
  if (SerialBT.connected()) {
    // Si está conectado y no estaba conectado previamente, encender el LED_BT
    if (!isConnected) {
      isConnected = true;
      digitalWrite(LED_BT, HIGH);
    }
  } else {
    // Si no está conectado y estaba conectado previamente, apagar el LED_BT
    if (isConnected) {
      isConnected = false;
      digitalWrite(LED_BT, LOW);
    }
  }
}
