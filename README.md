# Sistema de Control PID con Interfaz Gráfica y Comunicación por Socket

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-GUI-green)
![Socket](https://img.shields.io/badge/Socket-TCP/IP-orange)
![Pandas](https://img.shields.io/badge/Pandas-Data-yellow)
![PyQtGraph](https://img.shields.io/badge/PyQtGraph-Plotting-purple)

## Descripción General

Este proyecto implementa un sistema de simulación y visualización de un controlador PID para un sistema tipo péndulo, con una interfaz gráfica moderna y comunicación en tiempo real mediante sockets TCP/IP. Permite ajustar parámetros PID, visualizar la respuesta del sistema, recibir datos desde un servidor externo y analizar el comportamiento del controlador.

## Características Principales

- **Interfaz Gráfica Intuitiva:** Desarrollada con PySide6, permite el ajuste dinámico de parámetros PID (Proporcional, Integral, Derivativo) mediante sliders, inputs y checkboxes.
- **Visualización en Tiempo Real:** Gráficas interactivas de la señal esperada, real y el error, utilizando PyQtGraph.
- **Comunicación por Socket:** Recepción de datos en tiempo real desde un servidor TCP/IP externo, con procesamiento y actualización automática de la interfaz.
- **Tablas Dinámicas:** Visualización y actualización de los datos de simulación en tablas sincronizadas con las gráficas.
- **Control Total de la Simulación:** Funcionalidades para iniciar, pausar, resetear la simulación y gestionar la conexión de socket desde la propia interfaz.
- **Código Modular y Documentado:** Fácil de mantener, modificar y expandir para nuevas leyes de control o modelos de sistema.

## 📁 Estructura del Proyecto

```
SS/
├── PID_GUI_Experimental.py   # Interfaz gráfica y lógica de simulación PID
├── server.py                 # Servidor TCP/IP que envía datos de simulación
├── requirements.txt          # Dependencias del proyecto
└── docs/
    └──                       # Documentación completa en PDF (generada desde la interfaz)
```

---

## ⚡ Instalación

1. **Clona el repositorio:**
   ```sh
   git clone https://github.com/MiguelAEG/PID_Interfaz.git
   cd SS
   ```

2. **Instala las dependencias:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Ejecuta el servidor de datos:**
   ```sh
   python server.py
   ```

4. **Ejecuta la interfaz gráfica:**
   ```sh
   python PID_GUI_Experimental.py
   ```

---

## 🖥️ Uso

- Ajusta los parámetros PID desde la interfaz gráfica.
- Conecta al servidor usando la IP y puerto configurables.
- Visualiza en tiempo real la respuesta del sistema y los datos recibidos.
- Exporta los resultados y genera la documentación en PDF con un solo clic.

---


## 👨‍💻 Créditos

Desarrollado por **[Miguel Angel Enríquez Garía]**  
Contacto: [miguel.egk@gmail.com]

