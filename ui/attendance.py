import csv
import os
import re
from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QTimer
import qrcode

class AttendanceWindow(QDialog):
    def __init__(self, group_id):
        super().__init__()
        self.group_id = group_id
        self.setWindowTitle(f"Lista de Asistencia - {group_id}")
        self.setGeometry(150, 150, 1000, 600)
        
        self.init_ui()
    
    def init_ui(self):
        # Crear el layout principal
        layout = QVBoxLayout()
        
        # Crear la tabla para mostrar la lista de asistencia
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Matrícula", "Nombre"] + [f"Día {i+1}" for i in range(30)]) 
        layout.addWidget(self.table)
        
        # Botón para agregar alumno
        self.add_student_button = QPushButton("Agregar Alumno")
        self.add_student_button.clicked.connect(self.add_student)
        layout.addWidget(self.add_student_button)
        
        # Botón para guardar cambios
        self.save_changes_button = QPushButton("Guardar Cambios")
        self.save_changes_button.clicked.connect(self.save_attendance)
        layout.addWidget(self.save_changes_button)
        
        # Configurar el layout
        self.setLayout(layout)
        
        # Cargar la lista de asistencia
        self.load_attendance()
    
    def load_attendance(self):
        # Limpia la tabla antes de cargar los datos
        self.table.setRowCount(0)
        
        # Carpeta del grupo
        group_folder = f"data/{self.group_id}"
        csv_file_path = os.path.join(group_folder, f"{self.group_id}.csv")
        
        if not os.path.exists(csv_file_path):
            return
        
        # Leer el archivo CSV
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)
            self.table.setColumnCount(len(header))
            self.table.setHorizontalHeaderLabels(header)
            
            # Añadir filas a la tabla
            for row_data in reader:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for col, data in enumerate(row_data):
                    if col >= 2:  # Días de asistencia
                        checkbox = QTableWidgetItem()
                        checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                        checkbox.setCheckState(Qt.CheckState.Checked if data == "1" else Qt.CheckState.Unchecked)
                        self.table.setItem(row_position, col, checkbox)
                    else:  # Matrícula y Nombre
                        item = QTableWidgetItem(data)
                        item.setData(Qt.ItemDataRole.UserRole, data)  # Guardar el valor original
                        self.table.setItem(row_position, col, item)
        
        # Conectar las señales para la validación de celdas
        self.table.itemChanged.connect(self.validate_cell)
    
    def validate_cell(self, item):
        # Desconectar temporalmente la señal, entra en un bucle infinito si no se desconecta
        self.table.itemChanged.disconnect(self.validate_cell)
        
        try:
            if item.column() == 0:  # Matrícula
                current_value = item.text()
                old_value = item.data(Qt.ItemDataRole.UserRole)
                
                if self.is_new_matricula(item.row()) and not self.is_unique_matricula(current_value):
                    QMessageBox.critical(self, "Error", "La matrícula ya existe.")
                    item.setText(old_value)  # Revertir al valor antiguo
                else:
                    item.setData(Qt.ItemDataRole.UserRole, current_value)  # Actualizar el valor guardado
                
            elif item.column() == 1:  # Nombre
                current_value = item.text()
                
                if not self.is_valid_name(current_value):
                    QMessageBox.critical(self, "Error", "El nombre contiene caracteres no válidos.")
                    item.setText(item.data(Qt.ItemDataRole.UserRole))  # Revertir al valor antiguo
                else:
                    item.setData(Qt.ItemDataRole.UserRole, current_value)  # Actualizar el valor guardado
        
        finally:
            # Reconectar la señal después de la validación
            QTimer.singleShot(0, lambda: self.table.itemChanged.connect(self.validate_cell))
    
    def is_new_matricula(self, row):
        # Verificar si la matrícula en la fila es para un nuevo alumno
        current_item = self.table.item(row, 0)
        if not current_item:
            return False
        current_matricula = current_item.text()
        original_value = current_item.data(Qt.ItemDataRole.UserRole)
        return current_matricula != original_value
    
    # Verificar si la matrícula ya existe en el archivo CSV
    def is_unique_matricula(self, matricula):
        group_folder = f"data/{self.group_id}"
        csv_file_path = os.path.join(group_folder, f"{self.group_id}.csv")
        
        if not os.path.exists(csv_file_path):
            return True
        
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)
            for row in reader:
                if row[0] == matricula:
                    return False
        return True
    
    def is_valid_name(self, name):
        # expresión regular para validar el nombre
        return bool(re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+$', name))
    
    def add_student(self):
        # Crear y mostrar el diálogo para agregar un nuevo alumno
        from ui.student_manager import StudentManager
        dialog = StudentManager(self.group_id)
        if dialog.exec():
            self.load_attendance()
    
    def save_attendance(self):
        # Carpeta del grupo
        group_folder = f"data/{self.group_id}"
        csv_file_path = os.path.join(group_folder, f"{self.group_id}.csv")
        
        if not os.path.exists(csv_file_path):
            QMessageBox.warning(self, "Advertencia", "El archivo CSV no existe. No se pueden guardar los cambios.")
            return
        
        # Leer las matrículas actuales del archivo CSV
        old_matriculas = []
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  # Leer el encabezado
            for row in reader:
                old_matriculas.append(row[0])  # Guardar las matrículas

        # Detectar cambios en las matrículas
        changes_detected = False
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                current_matricula = item.text()
                if row < len(old_matriculas):
                    old_matricula = old_matriculas[row]
                    if current_matricula != old_matricula:
                        QMessageBox.information(self, "Cambio Detectado", f"Matrícula cambió de {old_matricula} a {current_matricula}")
                        self.update_folder(current_matricula, old_matricula)
                        self.update_qr_code(current_matricula, old_matricula)
                        changes_detected = True
        
        # Guardar los datos modificados en el archivo CSV
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Escribir el encabezado
            headers = [self.table.horizontalHeaderItem(col).text() for col in range(self.table.columnCount())]
            writer.writerow(headers)
            
            # Escribir los datos de la tabla
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item is not None:
                        if col >= 2:  # Para las columnas de asistencia
                            row_data.append("1" if item.checkState() == Qt.CheckState.Checked else "0")
                        else:  # Para matrícula y nombre
                            row_data.append(item.text())
                writer.writerow(row_data)
        
        if not changes_detected:
            QMessageBox.information(self, "Éxito", "Cambios guardados exitosamente.")
  
    def create_qr_code(self, student_id, file_path):
        # Crear datos para el QR
        qr_data = f"{student_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Crear una imagen del QR
        img = qr.make_image(fill='black', back_color='white')
        img.save(file_path)

    def update_folder(self, new_student_id, old_student_id):
        # Carpeta del grupo
        group_folder = f"data/{self.group_id}"
        # Renombrar la carpeta del estudiante
        os.rename(f"{group_folder}/{old_student_id}", f"{group_folder}/{new_student_id}")

    def update_qr_code(self, new_student_id, old_student_id):
        # Carpeta del grupo
        group_folder = f"data/{self.group_id}"
        # borrar el archivo QR antiguo id_qr.png
        os.remove(f"{group_folder}/{old_student_id}_qr.png")
        # Crear un nuevo QR con el nuevo id
        self.create_qr_code(new_student_id, f"{group_folder}/{new_student_id}_qr.png")
        