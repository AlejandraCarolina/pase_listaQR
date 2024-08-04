import os
import csv
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QLabel, QVBoxLayout, QCalendarWidget, QPushButton
from PyQt6.QtCore import QDate, Qt


class GroupManager(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crear Grupo")
        
        self.init_ui()
    
    def init_ui(self):
        self.layout = QFormLayout()
        
        # ID del grupo
        self.group_id_input = QLineEdit()
        self.layout.addRow("ID del Grupo:", self.group_id_input)
        
        # Fecha de inicio
        self.start_date_label = QLabel("Fecha de Inicio:")
        self.start_date_input = QLineEdit()
        self.start_date_input.setReadOnly(True)
        self.calendar_start = QCalendarWidget()
        self.calendar_start.setGridVisible(True)
        self.calendar_start.clicked.connect(self.select_start_date)
        self.calendar_start.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        
        # Configuración del calendario para no seleccionar fines de semana (sábado y domingo nomás)
        self.calendar_start.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar_start.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, self.get_weekday_format())
        self.calendar_start.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, self.get_weekday_format())
        
        self.layout.addRow(self.start_date_label, self.start_date_input)
        
        # Fecha de final
        self.end_date_label = QLabel("Fecha de Final:")
        self.end_date_input = QLineEdit()
        self.end_date_input.setReadOnly(True)
        self.calendar_end = QCalendarWidget()
        self.calendar_end.setGridVisible(True)
        self.calendar_end.clicked.connect(self.select_end_date)
        self.calendar_end.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        
        # Configuración del calendario para no seleccionar fines de semana
        self.calendar_end.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar_end.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, self.get_weekday_format())
        self.calendar_end.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, self.get_weekday_format())
        
        self.layout.addRow(self.end_date_label, self.end_date_input)
        
        # Botones de aceptar y cancelar
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.layout.addWidget(self.buttons)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.layout)
        main_layout.addWidget(self.calendar_start)
        main_layout.addWidget(self.calendar_end)
        
        self.setLayout(main_layout)
        
        # Inicialización de fechas
        self.start_date = None
        self.end_date = None
    
    # fincion para seleccionar la fecha de inicio y que no se pueda seleccionar una fecha anterior a la de inicio
    def select_start_date(self, date):
        self.start_date = date
        self.start_date_input.setText(date.toString("dd/MM/yyyy"))
        if self.end_date and self.end_date < self.start_date:
            # Ajustar la fecha final si es menor a la fecha de inicio
            self.end_date = self.start_date
            self.end_date_input.setText(self.end_date.toString("dd/MM/yyyy"))
        self.calendar_end.setMinimumDate(date)  # No permitir seleccionar fechas anteriores a la de inicio
    
    # funcion para seleccionar la fecha final y que no se pueda seleccionar una fecha anterior a la de inicio
    def select_end_date(self, date):
        if self.start_date and date < self.start_date:
            # No permitir seleccionar una fecha final anterior a la de inicio
            self.end_date_input.setText("Fecha final no válida")
            return
        self.end_date = date
        self.end_date_input.setText(date.toString("dd/MM/yyyy"))
    
    def accept(self):
        if not self.group_id_input.text() or not self.start_date or not self.end_date or self.end_date < self.start_date:
            # Validación simple
            if self.end_date < self.start_date:
                self.end_date_input.setText("Fecha final no válida")
            return
        super().accept()
        # Crear carpeta para el grupo
        group_id = self.group_id_input.text()
        folder_path = f"data/{group_id}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Crear archivo CSV para el grupo
        csv_file_path = os.path.join(folder_path, f"{group_id}.csv")
        # Aquí puedes agregar el código para inicializar el archivo CSV con las fechas
        self.initialize_csv(csv_file_path)

    def initialize_csv(self, file_path):
        import csv
        weekdays = get_weekdays(self.start_date.toPyDate(), self.end_date.toPyDate())
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            header = ["Matrícula", "Nombre"] + [date.strftime("%d/%m/%Y") for date in weekdays]
            writer.writerow(header)

    def get_weekday_format(self):
        from PyQt6.QtGui import QTextCharFormat
        format = QTextCharFormat()
        format.setForeground(Qt.GlobalColor.gray)
        return format

def get_weekdays(start_date, end_date):
    from datetime import timedelta
    weekdays = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Lunes a Viernes
            weekdays.append(current_date)
        current_date += timedelta(days=1)
    return weekdays
