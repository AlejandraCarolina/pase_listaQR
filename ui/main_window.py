import os
import csv
from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QWidget, QDialog
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Grupos")
        self.setGeometry(100, 100, 800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        # Crear un widget central y un layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # Crear la tabla para mostrar los grupos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID del Grupo", "Cantidad de Alumnos", "Fecha de Inicio", "Fecha de Final", "Ver", "Lista"])
        layout.addWidget(self.table)
        
        # Botón para crear grupo
        self.create_group_button = QPushButton("Crear Grupo")
        self.create_group_button.clicked.connect(self.create_group)
        layout.addWidget(self.create_group_button)
        
        central_widget.setLayout(layout)
        
        # Cargar los grupos existentes
        self.load_groups()
    
    def load_groups(self):
        # Limpia la tabla antes de cargar los datos
        self.table.setRowCount(0)
        
        # Carpeta de datos
        data_folder = "data"
        
        for group_id in os.listdir(data_folder):
            group_folder = os.path.join(data_folder, group_id)
            if os.path.isdir(group_folder):
                csv_file_path = os.path.join(group_folder, f"{group_id}.csv")
                
                # Leer el archivo CSV
                if os.path.exists(csv_file_path):
                    with open(csv_file_path, mode='r', encoding='utf-8') as file:
                        reader = csv.reader(file)
                        header = next(reader)
                        num_students = len(list(reader)) - 1  # Contar filas, restar el encabezado

                else:
                    num_students = 0
                
                # Añadir una fila en la tabla
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(group_id))
                self.table.setItem(row_position, 1, QTableWidgetItem(str(num_students+1)))
                
                # Añadir las fechas
                if os.path.exists(csv_file_path):
                    start_date, end_date = self.get_dates_from_csv(csv_file_path)
                    self.table.setItem(row_position, 2, QTableWidgetItem(start_date))
                    self.table.setItem(row_position, 3, QTableWidgetItem(end_date))
                else:
                    self.table.setItem(row_position, 2, QTableWidgetItem("N/A"))
                    self.table.setItem(row_position, 3, QTableWidgetItem("N/A"))
                
                # Botón para ver lista
                view_button = QPushButton("Ver Lista")
                view_button.clicked.connect(lambda _, id=group_id: self.view_list(id))
                self.table.setCellWidget(row_position, 4, view_button)

                # Boton para pasar lista
                attendance_button = QPushButton("Pasar Lista")
                attendance_button.clicked.connect(lambda _, id=group_id: self.take_attendance(id))
                self.table.setCellWidget(row_position, 5, attendance_button)
    
    def get_dates_from_csv(self, csv_file_path):
        # Lee el archivo CSV para obtener las fechas de inicio y final
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)
            if len(header) >= 3:
                start_date = header[2]
                end_date = header[-1]
                return start_date, end_date
        return "N/A", "N/A"
    
    def create_group(self):
        # Crear un grupo utilizando el diálogo GroupManager
        from ui.group_manager import GroupManager
        dialog = GroupManager()
        if dialog.exec():
            self.load_groups()
    
    def view_list(self, group_id):
        # Crear y mostrar la ventana de la lista de asistencia
        from ui.attendance import AttendanceWindow
        self.attendance_window = AttendanceWindow(group_id)
        self.attendance_window.show()

    def take_attendance(self, group_id):
        # Crear y mostrar la ventana para pasar lista
        from ui.take_attendance import AttendanceWindow
        self.attendance_window = AttendanceWindow(group_id)
        self.attendance_window.show()

        
    def add_student(self):
        # Crear y mostrar el diálogo para agregar un nuevo alumno
        from ui.student_manager import StudentManager
        dialog = StudentManager(self.group_id)
        if dialog.exec():
            self.load_attendance()

