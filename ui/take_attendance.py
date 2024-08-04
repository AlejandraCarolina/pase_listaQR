import cv2
import numpy as np
import csv
import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from pyzbar.pyzbar import decode
from datetime import datetime
import face_recognition

class AttendanceWindow(QDialog):
    def __init__(self, group_id):
        super().__init__()
        self.group_id = group_id
        self.setWindowTitle(f"Pasar Lista - {group_id}")
        self.setGeometry(0, 0, 1920, 1080)  # Tamaño inicial de la ventana (puede ajustarse)
        self.showFullScreen()  # Hacer la ventana de pantalla completa
        
        self.init_ui()
        self.camera = None
        self.current_date = datetime.now().strftime("%d/%m/%Y")  # Fecha actual

    def init_ui(self):
        layout = QVBoxLayout()
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        self.start_button = QPushButton("Iniciar Cámara")
        self.start_button.clicked.connect(self.start_camera)
        layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Detener Cámara")
        self.stop_button.clicked.connect(self.stop_camera)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)
        
        # Ajustar QLabel al tamaño de la ventana y centrarlo
        self.image_label.setGeometry(self.rect())  # Ajustar QLabel al tamaño de la ventana
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrar el QLabel en la ventana

    def start_camera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            QMessageBox.critical(self, "Error", "No se puede acceder a la cámara.")
            return
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def stop_camera(self):
        if self.camera:
            self.timer.stop()
            self.camera.release()
            self.camera = None

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.detect_faces(frame)
        qr_codes = self.detect_qr_codes(frame)

        detected = False
        if len(faces) > 0 and len(qr_codes) > 0:
            face = faces[0]
            qr_code = qr_codes[0]
            
            x, y, w, h = face
            cv2.rectangle(frame_rgb, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            (x, y, w, h) = qr_code.rect
            cv2.rectangle(frame_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)
            qr_data = qr_code.data.decode('utf-8')
            cv2.putText(frame_rgb, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            detected = self.process_attendance(qr_data, frame_rgb, x, y, w, h)
        
        qimg = QImage(frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.shape[1] * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # Ajustar el tamaño del pixmap al tamaño del QLabel y centrar
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def detect_faces(self, frame):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return faces

    def detect_qr_codes(self, frame):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        qr_codes = decode(gray_frame)
        return qr_codes

    def process_attendance(self, qr_data, frame_rgb, x, y, w, h):
        # Buscar el alumno en el CSV
        csv_file_path = f"data/{self.group_id}/{self.group_id}.csv"
        if not os.path.isfile(csv_file_path):
            self.show_message("Error", f"Archivo CSV no encontrado para el grupo {self.group_id}.")
            return False
        
        student_found = False
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            header = rows[0]
            date_index = header.index(self.current_date)
            for row in rows[1:]:
                if row[0] == qr_data:
                    student_found = True
                    if row[date_index] == '1':
                        self.show_message("Asistencia", "El alumno ya tiene asistencia registrada para hoy.")
                        return False
                    
                    # Verificar rostro
                    if self.verify_face(qr_data, frame_rgb, x, y, w, h):
                        row[date_index] = '1'
                        self.update_csv(csv_file_path, rows)
                        self.show_message("Asistencia Registrada", "La asistencia del alumno ha sido registrada correctamente.")
                        return True
                    else:
                        self.show_message("Error de Identificación", "No se verificó la identidad del alumno.")
                        return False

        if not student_found:
            self.show_message("No Encontrado", "Matrícula no encontrada en el CSV.")
        return False

    def verify_face(self, qr_data, frame_rgb, x, y, w, h):
        # Cargar las fotos del alumno
        student_folder = f"data/{self.group_id}/{qr_data}"
        if not os.path.isdir(student_folder):
            self.show_message("Error", f"Carpeta del alumno no encontrada: {student_folder}")
            return False
        
        known_faces = []
        for filename in os.listdir(student_folder):
            if filename.endswith('.jpg') or filename.endswith('.png'):
                image_path = os.path.join(student_folder, filename)
                image = face_recognition.load_image_file(image_path)
                known_faces.append(face_recognition.face_encodings(image)[0])
        
        if len(known_faces) == 0:
            self.show_message("Error", f"No se encontraron fotos del alumno en la carpeta {student_folder}.")
            return False
        
        # Detectar el rostro en el frame
        rgb_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Verificar si el rostro detectado coincide con las fotos del alumno
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_faces, face_encoding)
            if True in matches:
                return True
        
        return False

    def update_csv(self, csv_file_path, rows):
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    window = AttendanceWindow("Pase de Lista")
    window.show()
    app.exec()
