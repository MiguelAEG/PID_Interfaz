import sys
import random
import json
import socket
import threading
from functools import partial
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QSlider, QLineEdit, QLabel, QTabWidget, QTableWidget,
                               QTableWidgetItem, QFileDialog, QCheckBox)
from PySide6.QtCore import (Qt, QTimer)
import pyqtgraph as pg
import pandas as pd

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación de control de péndulo con interfaz gráfica.
    Permite ajustar parámetros PID, visualizar datos en tiempo real recibidos por socket,
    y mostrar resultados en tablas y gráficas.
    """
    def __init__(self):
        """
        Inicializa la ventana principal, los datos y la interfaz.
        """
        super().__init__()
        self.simulation_data = pd.DataFrame()  # DataFrame para almacenar los datos de simulación
        self.fixed_pid_values = {}  # Diccionario para guardar valores PID fijos durante la simulación
        self.init_ui()
        self.setup_simulation()
        self.previous_error = 0.0
        self.integral_error = 0.0
        self.socket_thread = None  # Hilo para manejar el socket
        self.running = False  # Bandera para controlar el socket

    def init_ui(self):
        """
        Inicializa la interfaz de usuario principal, creando los layouts y columnas.
        """
        self.setWindowTitle("Control de Péndulo")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_column = self.create_left_column()
        right_column = self.create_right_column()

        main_layout.addLayout(left_column)
        main_layout.addLayout(right_column)

    def setup_simulation(self):
        """
        Configura los componentes de la simulación, inicializa datos y timer.
        """
        self.current_index = 0
        self.simulation_data = pd.DataFrame()  # Inicialmente vacío
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.fixed_pid_values = {}

    def create_left_column(self):
        """
        Crea la columna izquierda con controles PID y controles de simulación.
        """
        left_column = QVBoxLayout()
        control_section = self.create_control_section()
        left_column.addWidget(control_section)
        simulation_controls = self.create_simulation_controls()
        left_column.addLayout(simulation_controls)
        return left_column

    def create_simulation_controls(self):
        """
        Crea los controles para la simulación, incluyendo botones de simulación y controles de socket.
        """
        control_layout = QVBoxLayout()

        # Botones de simulación
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Simulación")
        self.pause_button = QPushButton("Pausar")
        self.reset_button = QPushButton("Resetear")

        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)
        self.pause_button.setEnabled(False)

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)

        # Controles de conexión socket
        socket_layout = QHBoxLayout()
        socket_layout.addWidget(QLabel("IP:"))
        self.ip_input = QLineEdit()
        self.ip_input.setText("127.0.0.1")
        self.ip_input.setMaximumWidth(120)
        socket_layout.addWidget(self.ip_input)

        socket_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QLineEdit()
        self.port_input.setText("5000")
        self.port_input.setMaximumWidth(80)
        socket_layout.addWidget(self.port_input)

        self.connect_socket_button = QPushButton("Conectar Socket")
        self.connect_socket_button.clicked.connect(self.handle_socket_connect)
        socket_layout.addWidget(self.connect_socket_button)

        self.disconnect_socket_button = QPushButton("Desconectar Socket")
        self.disconnect_socket_button.clicked.connect(self.handle_socket_disconnect)
        socket_layout.addWidget(self.disconnect_socket_button)

        socket_layout.addStretch()

        control_layout.addLayout(buttons_layout)
        control_layout.addLayout(socket_layout)
        # Se eliminó el layout de "Número de puntos"

        return control_layout

    def handle_socket_connect(self):
        """
        Lee IP y puerto de la UI y conecta el socket.
        """
        ip = self.ip_input.text().strip() or "127.0.0.1"
        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            port = 5000
            self.port_input.setText("5000")
        self.start_socket_connection(host=ip, port=port)

    def handle_socket_disconnect(self):
        """
        Detiene la conexión de socket al presionar el botón.
        """
        self.stop_socket_connection()

    def create_control_section(self):
        """
        Crea la sección de controles PID con sliders, inputs y checkboxes.
        """
        control_section = QTabWidget()
        pid_tab = QWidget()
        pid_layout = QVBoxLayout(pid_tab)

        self.pid_sliders = {}
        self.pid_enabled = {}

        for param in ['P', 'I', 'D']:
            param_layout = QHBoxLayout()
            enable_radio = QCheckBox()
            enable_radio.setChecked(True)
            enable_radio.stateChanged.connect(lambda state, p=param: self.toggle_pid_component(p, state))
            self.pid_enabled[param] = enable_radio

            label = QLabel(param)
            min_input = QLineEdit()
            min_input.setPlaceholderText("Min")
            min_input.setMaximumWidth(50)
            max_input = QLineEdit()
            max_input.setPlaceholderText("Max")
            max_input.setMaximumWidth(50)
            min_input.textChanged.connect(partial(self.update_pid_from_settings, param))
            max_input.textChanged.connect(partial(self.update_pid_from_settings, param))

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            slider.valueChanged.connect(partial(self.update_pid_from_slider, param))

            value_input = QLineEdit()
            value_input.setPlaceholderText("Valor")
            value_input.setMaximumWidth(60)
            value_input.textChanged.connect(partial(self.update_pid_from_value_input, param))

            value_label = QLabel("0.50")

            self.pid_sliders[param] = {
                'slider': slider,
                'value_label': value_label,
                'min_input': min_input,
                'max_input': max_input,
                'value_input': value_input
            }

            param_layout.addWidget(enable_radio)
            param_layout.addWidget(label)
            param_layout.addWidget(min_input)
            param_layout.addWidget(slider)
            param_layout.addWidget(max_input)
            param_layout.addWidget(value_label)
            param_layout.addWidget(value_input)

            pid_layout.addLayout(param_layout)
            self.update_pid_from_settings(param)

        control_section.addTab(pid_tab, "PID")
        control_section.addTab(QWidget(), "C.Law 2")
        control_section.addTab(QWidget(), "C.Law 3")

        return control_section

    def update_pid_from_slider(self, param, slider_position_0_100):
        """Actualiza el valor PID basado en la posición del slider y los rangos min/max."""
        if not self.pid_enabled[param].isChecked():
            self.pid_sliders[param]['value_label'].setText("0.00")
            self.pid_sliders[param]['value_input'].setText("0.00")
            self.update_pid_in_simulation_data(param, 0.0)
            return

        try:
            min_val_str = self.pid_sliders[param]['min_input'].text()
            max_val_str = self.pid_sliders[param]['max_input'].text()

            min_val = float(min_val_str) if min_val_str else 0.0
            max_val = float(max_val_str) if max_val_str else 1.0 # Default max si está vacío (o el que corresponda)
            
            if min_val > max_val: min_val, max_val = max_val, min_val # Swap if min > max

            actual_value = min_val + (slider_position_0_100 / 100.0) * (max_val - min_val)
            
            self.pid_sliders[param]['value_label'].setText(f"{actual_value:.2f}")
            # Actualizar el value_input sin disparar su propia señal de textChanged recursivamente
            self.pid_sliders[param]['value_input'].blockSignals(True)
            self.pid_sliders[param]['value_input'].setText(f"{actual_value:.2f}")
            self.pid_sliders[param]['value_input'].blockSignals(False)

            self.update_pid_in_simulation_data(param, actual_value)

        except ValueError:
            # En caso de error en min/max, usar un fallback o mostrar error
            raw_value = slider_position_0_100 / 100.0
            self.pid_sliders[param]['value_label'].setText(f"{raw_value:.2f}")
            self.pid_sliders[param]['value_input'].blockSignals(True)
            self.pid_sliders[param]['value_input'].setText(f"{raw_value:.2f}")
            self.pid_sliders[param]['value_input'].blockSignals(False)
            self.update_pid_in_simulation_data(param, raw_value)

    def update_pid_from_value_input(self, param, text_value):
        """Actualiza el valor PID y el slider basado en la entrada manual de valor."""
        if not self.pid_enabled[param].isChecked():
            # Si está deshabilitado, no hacer nada o resetear a 0
            return

        try:
            actual_value = float(text_value)
            self.pid_sliders[param]['value_label'].setText(f"{actual_value:.2f}")

            min_val_str = self.pid_sliders[param]['min_input'].text()
            max_val_str = self.pid_sliders[param]['max_input'].text()
            min_val = float(min_val_str) if min_val_str else 0.0
            max_val = float(max_val_str) if max_val_str else 1.0

            if min_val > max_val: min_val, max_val = max_val, min_val

            slider_widget = self.pid_sliders[param]['slider']
            slider_widget.blockSignals(True) # Evitar loop de actualización
            
            if max_val == min_val: # Evitar división por cero si min y max son iguales
                slider_widget.setValue(0 if actual_value <= min_val else 100)
            elif actual_value <= min_val:
                slider_widget.setValue(0)
            elif actual_value >= max_val:
                slider_widget.setValue(100)
            else:
                proportion = (actual_value - min_val) / (max_val - min_val)
                slider_widget.setValue(int(proportion * 100))
            
            slider_widget.blockSignals(False)
            self.update_pid_in_simulation_data(param, actual_value)

        except ValueError:
            # Si el valor no es un número, no hacer nada o mostrar un error en value_label
            # self.pid_sliders[param]['value_label'].setText("Inválido")
            pass

    def update_pid_from_settings(self, param, _=None): # _ para ignorar el valor de textChanged si se conecta a eso
        """Se llama cuando min/max cambian, o para inicializar."""
        # Re-evaluar el valor actual basado en el slider y los nuevos min/max
        slider_pos = self.pid_sliders[param]['slider'].value()
        self.update_pid_from_slider(param, slider_pos) # Esto actualizará todo

    def update_pid_in_simulation_data(self, param_name, value):
        """Actualiza la columna del parámetro PID en self.simulation_data."""
        if not self.simulation_data.empty:
            self.simulation_data[param_name] = [value] * len(self.simulation_data)
            # Actualizar la tabla si la simulación no está corriendo (si corre, se actualiza en update_plot)
            if not self.timer.isActive():
                self.update_table_with_dataframe(self.simulation_data)


    def toggle_pid_component(self, param, state):
        """Activa o desactiva un componente PID"""
        is_checked = bool(state)
        self.pid_enabled[param].setChecked(is_checked) # Asegurar estado del checkbox
        
        # Forzar una actualización del valor PID, que considerará el estado de enabled
        # Si está deshabilitado, update_pid_from_slider pondrá 0.00
        # Si está habilitado, tomará el valor actual del slider/inputs
        self.update_pid_from_slider(param, self.pid_sliders[param]['slider'].value())


    def get_pid_value_from_ui(self, param):
        """
        Obtiene el valor actual de un componente PID desde la UI,
        leyendo directamente el value_label que se asume es la fuente de verdad.
        """
        if self.pid_enabled[param].isChecked():
            try:
                # El value_label debe reflejar el valor actual configurado en la UI
                return float(self.pid_sliders[param]['value_label'].text())
            except ValueError:
                # Fallback si el label no es un número válido (poco probable si la UI funciona bien)
                # Podríamos recalcular desde el slider y min/max como en update_pid_from_slider
                # o simplemente devolver un valor por defecto o el raw del slider.
                # Por simplicidad, intentamos leer el input de valor si el label falla.
                try:
                    return float(self.pid_sliders[param]['value_input'].text())
                except ValueError:
                    return 0.0 # Último recurso
        return 0.0

    # NO USAR get_pid_value como antes, ahora usamos get_pid_value_from_ui o fixed_pid_values

    def create_right_column(self):
        """Crea la columna derecha con tabla y gráfica"""
        right_column = QVBoxLayout()

        # Sección de tabla
        table_section = self.create_table_section()

        # Sección de gráfica
        graph_section = self.create_graph_section()

        right_column.addWidget(table_section)
        right_column.addWidget(graph_section)

        self.setup_tab_sync(table_section, graph_section)

        return right_column

    def create_table_section(self):
        """Crea la sección de tablas de datos"""
        table_section = QTabWidget()
        # Asegurarse que los headers coincidan con las columnas del DataFrame
        self.headers_pid = ["Time", "Setpoint", "Valor Medido", "Error", "P", "I", "D"]
        headers_lc2 = ["Time", "Setpoint", "Valor Medido", "Error"] # Ejemplo

        self.add_table_to_tab(table_section, "PID", self.headers_pid)
        self.add_table_to_tab(table_section, "C.Law 1", headers_lc2, rows=10, columns=4)
        self.add_table_to_tab(table_section, "C.Law 2", [], rows=100, columns=10) # Ejemplo

        return table_section

    def toggle_plot_visibility(self, name, state):
        """Controla la visibilidad de las líneas del gráfico"""
        self.plot_lines[name]['visible'] = bool(state)
        if not self.plot_lines[name]['visible']:
            self.plot_lines[name]['line'].setData([], [])
        else:
            # Actualizar con los datos actuales si la simulación está en curso o hay datos
            if self.current_index > 0 or not self.simulation_data.empty:
                data_to_plot = self.simulation_data.iloc[:self.current_index] if self.current_index > 0 else self.simulation_data
                if name == "Esperado" and "Setpoint" in data_to_plot:
                    self.plot_lines[name]['line'].setData(data_to_plot["Time"], data_to_plot["Setpoint"])
                elif name == "Real" and "Valor Medido" in data_to_plot:
                    self.plot_lines[name]['line'].setData(data_to_plot["Time"], data_to_plot["Valor Medido"])
                elif name == "Error" and "Error" in data_to_plot:
                    self.plot_lines[name]['line'].setData(data_to_plot["Time"], data_to_plot["Error"])


    def create_graph_section(self):
        """Crea la sección de gráficos"""
        graph_section = QTabWidget()

        # Contenedor para el gráfico y los controles
        pid_container = QWidget()
        pid_layout = QVBoxLayout(pid_container)

        # Se crea el gráfico
        self.graph_pid = pg.PlotWidget()
        self.setup_graph(self.graph_pid)

        # Inicializamos las líneas del gráfico con puntos
        self.plot_lines = {
            "Esperado": {
                'line': self.graph_pid.plot([], [], pen=pg.mkPen('r', width=2), symbol='o', symbolSize=5, symbolBrush='r', name="Esperado"),
                'visible': True
            },
            "Real": {
                'line': self.graph_pid.plot([], [], pen=pg.mkPen('g', width=2), symbol='o', symbolSize=5, symbolBrush='g', name="Real"),
                'visible': True
            },
            "Error": {
                'line': self.graph_pid.plot([], [], pen=pg.mkPen('b', width=2), symbol='o', symbolSize=5, symbolBrush='b', name="Error"),
                'visible': True
            }
        }

        # Controles de visibilidad
        visibility_layout = QHBoxLayout()
        visibility_layout.addWidget(QLabel("Mostrar:"))

        for name in self.plot_lines.keys():
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, n=name: self.toggle_plot_visibility(n, state))
            visibility_layout.addWidget(checkbox)

        visibility_layout.addStretch()

        pid_layout.addWidget(self.graph_pid)
        pid_layout.addLayout(visibility_layout)

        graph_section.addTab(pid_container, "PID")
        graph_section.addTab(QWidget(), "C.Law 1")
        graph_section.addTab(QWidget(), "C.Law 2")

        return graph_section

    def setup_graph(self, graph):
        """Configura las propiedades del gráfico"""
        graph.setBackground('w')
        graph.setLabel('left', 'Valor')
        graph.setLabel('bottom', 'Tiempo (s)')
        graph.addLegend(offset=(30, 30))
        graph.showGrid(x=True, y=True)


    def setup_tab_sync(self, table_section, graph_section):
        """Configura la sincronización entre pestañas"""
        # Guardar referencias a las secciones de pestañas
        self.table_section = table_section
        self.graph_section = graph_section
        # self.control_section lo obtenemos más tarde si es necesario, o pasarlo como arg

        # Conectar el cambio de pestaña
        table_section.currentChanged.connect(self.sync_tabs_from_table)
        graph_section.currentChanged.connect(self.sync_tabs_from_graph)
        # Si tienes una referencia a control_section (la QTabWidget de los controles PID, C.Law2, etc.):
        # self.control_section.currentChanged.connect(self.sync_tabs_from_control)


    def sync_tabs_from_table(self, index):
        if hasattr(self, 'graph_section') and self.graph_section.currentIndex() != index:
            self.graph_section.setCurrentIndex(index)
        # if hasattr(self, 'control_section_ref') and self.control_section_ref.currentIndex() != index:
        # self.control_section_ref.setCurrentIndex(index)

    def sync_tabs_from_graph(self, index):
        if hasattr(self, 'table_section') and self.table_section.currentIndex() != index:
            self.table_section.setCurrentIndex(index)
        # if hasattr(self, 'control_section_ref') and self.control_section_ref.currentIndex() != index:
        # self.control_section_ref.setCurrentIndex(index)

    # def sync_tabs_from_control(self, index):
    #     if hasattr(self, 'table_section') and self.table_section.currentIndex() != index:
    #         self.table_section.setCurrentIndex(index)
    #     if hasattr(self, 'graph_section') and self.graph_section.currentIndex() != index:
    #         self.graph_section.setCurrentIndex(index)

    def sync_tabs(self, index): # Método antiguo, puedes borrarlo si usas los específicos
        """Sincroniza las pestañas entre las diferentes secciones"""
        sender = self.sender()
        # Suponiendo que self.control_section es la QTabWidget de controles
        if hasattr(self, 'control_section') and sender != self.control_section:
             if self.control_section.count() > index : self.control_section.setCurrentIndex(index) # Evitar error si no existe el tab
        if hasattr(self, 'table_section') and sender != self.table_section:
            if self.table_section.count() > index : self.table_section.setCurrentIndex(index)
        if hasattr(self, 'graph_section') and sender != self.graph_section:
            if self.graph_section.count() > index : self.graph_section.setCurrentIndex(index)


    def add_table_to_tab(self, tab_widget, tab_name, headers, rows=0, columns=0): # Default rows=0
        """Añade una tabla a una pestaña"""
        if not headers: # Si no hay headers, usar el número de columnas
            actual_columns = columns
        else:
            actual_columns = len(headers)

        table = QTableWidget(rows, actual_columns)
        if headers:
            table.setHorizontalHeaderLabels(headers)
        tab_widget.addTab(table, tab_name)


    def update_plot(self):
        """Actualiza el gráfico con nuevos datos"""
        if self.simulation_data.empty or self.current_index >= len(self.simulation_data):
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            # Habilitar controles PID al finalizar
            for param_controls in self.pid_sliders.values():
                param_controls['slider'].setEnabled(True)
                param_controls['min_input'].setEnabled(True)
                param_controls['max_input'].setEnabled(True)
                param_controls['value_input'].setEnabled(True)
            for checkbox in self.pid_enabled.values():
                checkbox.setEnabled(True)
            return

        # Get current setpoint and measured value from DataFrame for this step
        setpoint = self.simulation_data.at[self.current_index, "Setpoint"]
        measured_value = self.simulation_data.at[self.current_index, "Valor Medido"]

        # Calculate error as the difference
        error = setpoint - measured_value

        # Get PID coefficients from self.fixed_pid_values (set at simulation start)
        Kp = self.fixed_pid_values.get('P', 0.0)
        Ki = self.fixed_pid_values.get('I', 0.0)
        Kd = self.fixed_pid_values.get('D', 0.0)

        # Calculate PID terms
        # dt = 0.1 # Intervalo del timer en segundos, si es constante. O calcularlo desde "Time"
        dt = self.timer.interval() / 1000.0
        self.integral_error += error * dt
        derivative_error = (error - self.previous_error) / dt if dt > 0 else 0.0


        # PID output - esto simula el efecto del controlador
        pid_output = (Kp * error) + (Ki * self.integral_error) + (Kd * derivative_error)

        # Simular la respuesta del sistema al PID output.
        # Esta es una simplificación. Un modelo real del péndulo sería más complejo.
        # Aquí, asumimos que el pid_output ajusta directamente el valor medido.
        new_measured_value = measured_value + pid_output * dt # Ajuste proporcional al tiempo
        # new_measured_value = pid_output # Si el PID directamente establece la nueva posición (menos realista para un péndulo)

        # Para evitar que el valor medido se dispare, podemos limitarlo o hacerlo más realista
        # Por ejemplo, si el setpoint es un ángulo, podría oscilar alrededor de él.
        # Aquí solo actualizamos el DataFrame con el valor "controlado"
        self.simulation_data.at[self.current_index, "Valor Medido"] = new_measured_value

        # Update previous error
        self.previous_error = error

        # Update error in DataFrame
        self.simulation_data.at[self.current_index, "Error"] = error

        # Update plot data up to current_index + 1
        current_plot_data = self.simulation_data.iloc[:self.current_index + 1]

        if self.plot_lines["Esperado"]["visible"]:
            self.plot_lines["Esperado"]["line"].setData(
                current_plot_data["Time"], current_plot_data["Setpoint"]
            )
        if self.plot_lines["Real"]["visible"]:
            self.plot_lines["Real"]["line"].setData(
                current_plot_data["Time"], current_plot_data["Valor Medido"]
            )
        if self.plot_lines["Error"]["visible"]:
            self.plot_lines["Error"]["line"].setData(
                current_plot_data["Time"], current_plot_data["Error"]
            )

        # Actualizar la tabla solo con la fila actual o todas las filas hasta la actual
        self.update_table_row(self.current_index, self.simulation_data.iloc[self.current_index])
        # O para actualizar toda la tabla hasta el punto actual:
        # self.update_table_with_dataframe(current_plot_data)

        self.current_index += 1

    def update_table_row(self, row_index, data_series):
        """Actualiza una fila específica de la tabla PID."""
        table = self.table_section.widget(0) # Asume que la tabla PID es la primera
        if isinstance(table, QTableWidget):
            if row_index >= table.rowCount():
                table.setRowCount(row_index + 1)
            
            for col_idx, header_name in enumerate(self.headers_pid):
                if header_name in data_series:
                    item_value = data_series[header_name]
                    table.setItem(row_index, col_idx, QTableWidgetItem(f"{item_value:.2f}"))
                # else: # Si alguna columna esperada no está en data_series
                #     table.setItem(row_index, col_idx, QTableWidgetItem(""))


    def update_table_with_dataframe(self, df_data):
        """Actualiza toda la tabla PID con un DataFrame completo."""
        table = self.table_section.widget(0)  # Asume que la tabla PID es la primera
        if isinstance(table, QTableWidget):
            table.setRowCount(len(df_data))
            for row_idx in range(len(df_data)):
                row_series = df_data.iloc[row_idx]
                for col_idx, header_name in enumerate(self.headers_pid):
                    if header_name in row_series:
                        item_value = row_series[header_name]
                        table.setItem(row_idx, col_idx, QTableWidgetItem(f"{item_value:.2f}"))
                    # else:
                    #     table.setItem(row_idx, col_idx, QTableWidgetItem(""))


    def start_simulation(self):
        """Inicia la simulación"""
        if self.simulation_data.empty:
            print("No hay datos para simular.")
            return

        self.timer.start()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)

        # Deshabilitar sliders y entradas de PID para que no puedan cambiar durante la simulación
        for param_controls in self.pid_sliders.values():
            param_controls['slider'].setEnabled(False)
            param_controls['min_input'].setEnabled(False)
            param_controls['max_input'].setEnabled(False)
            param_controls['value_input'].setEnabled(False)
        for checkbox in self.pid_enabled.values():
            checkbox.setEnabled(False)

        # Guardar los valores PID actuales de la UI en fixed_pid_values para esta simulación
        self.fixed_pid_values = {
            param: self.get_pid_value_from_ui(param) for param in ['P', 'I', 'D']
        }

        # Asegurarse que las columnas P, I, D en el DataFrame reflejen estos valores fijados
        for param, value in self.fixed_pid_values.items():
            if param in self.simulation_data.columns:
                self.simulation_data[param] = [value] * len(self.simulation_data)

        # Reiniciar errores acumulados para el PID
        self.previous_error = 0.0
        self.integral_error = 0.0
        self.current_index = 0  # Reiniciar el índice de simulación

        # Limpiar la tabla antes de llenarla con nuevos datos de simulación
        pid_table = self.table_section.widget(0)
        if isinstance(pid_table, QTableWidget):
            pid_table.setRowCount(0)

    def pause_simulation(self):
        """Pausa la simulación"""
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        # No re-habilitar los controles PID aquí, solo en reset o al finalizar.

    def reset_simulation(self):
        """Resetea la simulación. Limpia datos, errores y reinicia la interfaz."""
        self.timer.stop()
        self.current_index = 0
        self.previous_error = 0.0
        self.integral_error = 0.0
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

        # Habilitar sliders y entradas de PID para permitir cambios
        for param_controls in self.pid_sliders.values():
            param_controls['slider'].setEnabled(True)
            param_controls['min_input'].setEnabled(True)
            param_controls['max_input'].setEnabled(True)
            param_controls['value_input'].setEnabled(True)
        for checkbox in self.pid_enabled.values():
            checkbox.setEnabled(True)

        self.fixed_pid_values = {} # Limpiar los valores PID fijados

        for line_data in self.plot_lines.values():
            if 'line' in line_data: # Asegurarse que 'line' existe
                line_data['line'].setData([], [])

        table = self.table_section.widget(0) # Asume PID es el tab 0
        if isinstance(table, QTableWidget):
            table.setRowCount(0) # Limpia la tabla

        # Limpia también los datos recibidos por socket
        self.simulation_data = pd.DataFrame()

        # También podrías querer redibujar el gráfico con todos los datos existentes
        self.toggle_plot_visibility("Esperado", self.plot_lines["Esperado"]["visible"])
        self.toggle_plot_visibility("Real", self.plot_lines["Real"]["visible"])
        self.toggle_plot_visibility("Error", self.plot_lines["Error"]["visible"])


    def generate_default_data(self, num_points):
        """Elimina la generación de datos por defecto."""
        pass

    def start_socket_connection(self, host="127.0.0.1", port=5000):  # Cambia a localhost
        """Inicia la conexión de socket en un hilo separado."""
        self.running = True
        self.socket_thread = threading.Thread(target=self.receive_data, args=(host, port), daemon=True)
        self.socket_thread.start()

    def stop_socket_connection(self):
        """Detiene la conexión de socket."""
        self.running = False
        if self.socket_thread:
            self.socket_thread.join()

    def receive_data(self, host, port):
        """Recibe datos JSON a través de un socket y los procesa."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                print(f"Intentando conectar a {host}:{port}...")
                client_socket.connect((host, port))
                print("Conexión establecida.")
                while self.running:
                    print("Esperando datos...")
                    data = client_socket.recv(1024)  # Recibe datos en bloques de 1024 bytes
                    if not data:
                        print("Conexión cerrada por el servidor.")
                        break
                    print(f"Datos recibidos: {data.decode('utf-8')}")  # Verifica si los datos llegan
                    try:
                        json_data = json.loads(data.decode('utf-8'))
                        self.process_received_data(json_data)
                    except json.JSONDecodeError:
                        print("Error al decodificar JSON")
        except ConnectionRefusedError:
            print(f"Error: No se pudo conectar a {host}:{port}. Verifica que el servidor esté en ejecución.")
        except Exception as e:
            print(f"Error en la conexión de socket: {e}")

    def process_received_data(self, json_data):
        """Procesa los datos recibidos y actualiza la gráfica y la tabla."""
        if not isinstance(json_data, dict):
            print("Formato de datos inválido")
            return

        # Imprimir los datos recibidos en la consola
        print(f"Datos recibidos: {json_data}")

        # Agregar los datos al DataFrame
        new_row = pd.DataFrame([json_data])
        self.simulation_data = pd.concat([self.simulation_data, new_row], ignore_index=True)

        # Actualizar la gráfica y la tabla
        self.update_plot()
        self.update_table_with_dataframe(self.simulation_data)

    def closeEvent(self, event):
        """Sobrescribe el evento de cierre para detener el socket."""
        self.stop_socket_connection()
        super().closeEvent(event)

    def update_simulation_points(self):
        """Actualiza el número de puntos de la simulación (placeholder para evitar error)."""
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Ya no conectamos automáticamente el socket aquí, ahora es manual desde la UI
    sys.exit(app.exec())