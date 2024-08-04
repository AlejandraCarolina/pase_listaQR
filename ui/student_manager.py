import os
import shutil
import csv
import qrcode
import cv2
from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPalette, QColor
import re

class StudentManager(QDialog):
    def __init__(self, group_id, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.setWindowTitle("Agregar Alumno")
        self.setGeometry(200, 200, 800, 600)
        self.photos = [None, None, None]  # Almacena las rutas de las fotos capturadas
        self.init_ui()
        self.camera = None
        self.timer = None
        self.current_photo_index = 0
    
    def init_ui(self):
        # Crear el layout del formulario
        layout = QVBoxLayout()
        
        # Campos para nombre y matrícula
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        form_layout.addRow(QLabel("Nombre:"), self.name_input)
        form_layout.addRow(QLabel("Matrícula:"), self.id_input)
        layout.addLayout(form_layout)
        
        # Botones para encender la cámara y capturar fotos
        self.camera_button = QPushButton("Encender Cámara")
        self.camera_button.clicked.connect(self.start_camera)
        layout.addWidget(self.camera_button)
        
        self.capture_button = QPushButton("Capturar Foto")
        self.capture_button.clicked.connect(self.capture_photo)
        self.capture_button.setEnabled(False)  # Deshabilitado hasta que la cámara esté encendida
        layout.addWidget(self.capture_button)
        
        # Etiqueta para mostrar la imagen de la cámara
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        
        # Botón para guardar el alumno
        self.save_button = QPushButton("Guardar Alumno")
        self.save_button.clicked.connect(self.save_student)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)

    def start_camera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            QMessageBox.critical(self, "Error", "No se puede acceder a la cámara.")
            return
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        self.capture_button.setEnabled(True)
        self.camera_button.setEnabled(False)  # Deshabilitar el botón de encender la cámara

    def capture_photo(self):
        if self.current_photo_index < 3:
            ret, frame = self.camera.read()
            if ret:
                file_path = f"photo_{self.current_photo_index + 1}.jpg"
                cv2.imwrite(file_path, frame)
                self.photos[self.current_photo_index] = file_path
                self.current_photo_index += 1
                QMessageBox.information(self, "Foto Capturada", f"Foto {self.current_photo_index} capturada con éxito.")
                if self.current_photo_index == 3:
                    QMessageBox.information(self, "Captura Completa", "Se han capturado las 3 fotos.")
                    self.capture_button.setEnabled(False)  # Deshabilitar después de capturar 3 fotos

    def update_frame(self):
        ret, frame = self.camera.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qimg = QImage(frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.shape[1] * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.image_label.setPixmap(pixmap)
            self.image_label.setScaledContents(True)

    def stop_camera(self):
        if self.camera:
            self.timer.stop()
            self.camera.release()
            self.camera = None
            self.camera_button.setEnabled(True)  # Volver a habilitar el botón de encender la cámara

    def save_student(self):
        name = self.name_input.text()
        student_id = self.id_input.text()
        
        if not name or not student_id:
            # Validar que el nombre y matrícula no estén vacíos
            self.show_error("El nombre y matrícula son obligatorios.")
            return
        
        if not re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+$', name):
            self.show_error("El nombre solo puede contener letras y espacios.")
            return
        
        if " " in student_id:
            self.show_error("La matrícula no puede contener espacios.")
            return
        
        if not self.is_unique_id(student_id):
            self.show_error("La matrícula ya está registrada.")
            return
        
        # Carpeta del grupo y del alumno
        group_folder = f"data/{self.group_id}"
        student_folder = os.path.join(group_folder, student_id)
        os.makedirs(student_folder, exist_ok=True)
        
        # Crear el código QR
        qr_file_path = os.path.join(group_folder, f"{student_id}_qr.png")
        self.create_qr_code(student_id, name, qr_file_path)
        
        # Guardar las fotos
        for i, photo_path in enumerate(self.photos):
            if photo_path:
                shutil.copy(photo_path, os.path.join(student_folder, f"foto_{i+1}.jpg"))
        
        # Agregar el alumno a la lista de asistencia en el CSV
        self.add_student_to_csv(student_id, name)
        
        # Detener la cámara
        self.stop_camera()
        # borrar las fotos temporales
        for photo_path in self.photos:
            if photo_path:
                os.remove(photo_path)
        self.accept()  # Cierra el diálogo y guarda los cambios
    
    def create_qr_code(self, student_id, name, file_path):
        qr_data = f"{student_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save(file_path)
    
    def add_student_to_csv(self, student_id, name):
        group_folder = f"data/{self.group_id}"
        csv_file_path = os.path.join(group_folder, f"{self.group_id}.csv")
        
        rows = []
        header_added = False
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                if not header_added:
                    header = rows[0]
                    new_row = [student_id, name] + ["0"] * (len(header) - 2)
                    rows.append(new_row)
            else:
                header = ["Matrícula", "Nombre"] + self.get_date_headers(csv_file_path)
                new_row = [student_id, name] + ["0"] * (len(header) - 2)
                rows.append(header)
                rows.append(new_row)
        
        with open(csv_file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    
    def get_date_headers(self, csv_file_path):
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header:
                return header[2:]
        return []
    
    def is_unique_id(self, student_id):
        group_folder = f"data/{self.group_id}"
        csv_file_path = os.path.join(group_folder, f"{self.group_id}.csv")
        
        if not os.path.exists(csv_file_path):
            return True
        
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == student_id:
                    return False
        return True
    
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)
