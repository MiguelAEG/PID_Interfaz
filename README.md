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

## Estructura del Proyecto
