from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QCheckBox, QColorDialog, QGroupBox, QComboBox,
                           QScrollArea, QFrame, QRadioButton, QButtonGroup,
                           QGridLayout, QShortcut, QStatusBar)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QKeySequence, QPainterPath, QIcon, QDoubleValidator, QIntValidator, QPolygon
import sys
import math
import subprocess

# Install dependencies
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow', 'PyQt5'])

class ShapeEditor(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(800, 600)
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.drawing = False
        self.shape_type = "Rechthoek"
        self.shape_color = QColor("#723744")  # Update default kleur
        self.start_point = QPoint()
        self.current_rect = None
        self.shapes = []  # List of (shape_type, rect, color)
        self.dimensions_label = QLabel(self)
        self.dimensions_label.setStyleSheet("""
            QLabel { 
                background-color: rgba(255, 255, 255, 0.8);
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        self.pixels_per_cm = 37.8  # Ongeveer pixels per cm
        self.setMouseTracking(True)  # Enable mouse tracking voor dimensies update
        self.preview_mode = False  # Voor hover preview
        self.hover_point = QPoint()
        self.line_thickness = 2  # Default line thickness

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.current_rect = QRect(self.start_point, self.start_point)
            self.update_dimensions_label(self.current_rect)

    def mouseMoveEvent(self, event):
        self.hover_point = event.pos()
        if self.drawing:
            self.current_rect = QRect(self.start_point, event.pos()).normalized()
            self.update_dimensions_label(self.current_rect)
            # Voeg vloeiende beweging toe tijdens tekenen
            self.update()
        else:
            # Toon preview alleen als we niet tekenen
            if not self.shapes:  # Alleen preview als er geen vorm is
                self.preview_mode = True
                self.update()

    def leaveEvent(self, event):
        # Reset preview wanneer muis het gebied verlaat
        self.preview_mode = False
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.current_rect and self.current_rect.width() > 0 and self.current_rect.height() > 0:
                self.shapes = [(self.shape_type, self.current_rect, self.shape_color)]  # Alleen de laatste vorm bewaren
                self.update()
            self.current_rect = None
            self.dimensions_label.hide()

    def update_dimensions_label(self, rect):
        if rect:
            width_cm = rect.width() / self.pixels_per_cm
            height_cm = rect.height() / self.pixels_per_cm
            self.dimensions_label.setText(f"{width_cm:.1f} x {height_cm:.1f} cm")
            # Plaats label boven de vorm
            self.dimensions_label.adjustSize()
            label_x = rect.x()
            label_y = rect.y() - self.dimensions_label.height() - 5
            if label_y < 0:
                label_y = rect.bottom() + 5
            self.dimensions_label.move(label_x, label_y)
            self.dimensions_label.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)
        
        # Grid tekenen met verbeterde stijl
        self.draw_enhanced_grid(painter)
        
        # Preview van vorm onder muis als we niet tekenen
        if self.preview_mode and not self.shapes and not self.drawing:
            preview_size = 100  # Grotere preview
            preview_rect = QRect(
                self.hover_point.x() - preview_size//2,
                self.hover_point.y() - preview_size//2,
                preview_size, preview_size
            )
            # Teken semi-transparante preview met stippellijn
            painter.setOpacity(0.4)
            pen = QPen(self.shape_color, self.line_thickness, Qt.DashLine)
            pen.setDashPattern([5, 5])  # Maak een mooiere stippellijn
            painter.setPen(pen)
            self.draw_shape(painter, self.shape_type, preview_rect)
            
            # Teken hulppunten voor de driehoek
            if self.shape_type == "Driehoek":
                painter.setOpacity(0.6)
                point_size = 6
                points = [
                    QPoint(int(preview_rect.left() + preview_rect.width()/2), preview_rect.top()),
                    QPoint(preview_rect.left(), preview_rect.bottom()),
                    QPoint(preview_rect.right(), preview_rect.bottom())
                ]
                for point in points:
                    painter.fillRect(
                        point.x() - point_size//2,
                        point.y() - point_size//2,
                        point_size, point_size,
                        self.shape_color
                    )
            
            painter.setOpacity(1.0)

        # Teken opgeslagen vormen
        for shape_type, rect, color in self.shapes:
            # Teken schaduw
            shadow_offset = 2
            shadow_rect = QRect(rect)
            shadow_rect.translate(shadow_offset, shadow_offset)
            painter.setPen(QPen(QColor(100, 100, 100, 50), self.line_thickness))
            self.draw_shape(painter, shape_type, shadow_rect)
            
            # Teken hoofdvorm
            painter.setPen(QPen(color, self.line_thickness, Qt.SolidLine))
            self.draw_shape(painter, shape_type, rect)

        # Teken huidige vorm tijdens tekenen
        if self.drawing and self.current_rect:
            painter.setPen(QPen(self.shape_color, self.line_thickness))
            self.draw_shape(painter, self.shape_type, self.current_rect)
            
            # Teken hulplijnen met verbeterde stijl
            painter.setPen(QPen(QColor(100, 100, 255, 150), 1, Qt.DashLine))
            self.draw_guide_lines(painter)

    def draw_shape(self, painter, shape_type, rect):
        if shape_type == "Rechthoek":
            # Teken rechthoek met afgeronde hoeken
            painter.drawRoundedRect(rect, 5, 5)
        elif shape_type == "Cirkel":
            # Teken perfecte cirkel
            painter.drawEllipse(rect)
        elif shape_type == "Driehoek":
            # Verbeterde driehoek met vloeiende lijnen en correcte type conversie
            points = [
                QPoint(int(rect.left() + rect.width()/2), rect.top()),  # Top midden
                QPoint(rect.left(), rect.bottom()),                     # Links onder
                QPoint(rect.right(), rect.bottom())                     # Rechts onder
            ]
            # Teken driehoek met vloeiende lijnen
            polygon = QPolygon(points)
            painter.drawPolygon(polygon)

    def draw_enhanced_grid(self, painter):
        cm_spacing = int(self.pixels_per_cm)
        
        # Fijner raster
        painter.setPen(QPen(QColor(240, 240, 240), 1, Qt.SolidLine))
        for x in range(0, self.width(), cm_spacing // 4):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), cm_spacing // 4):
            painter.drawLine(0, y, self.width(), y)
            
        # Middel raster
        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.SolidLine))
        for x in range(0, self.width(), cm_spacing // 2):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), cm_spacing // 2):
            painter.drawLine(0, y, self.width(), y)
            
        # Hoofdraster met verbeterde markeringen
        painter.setPen(QPen(QColor(180, 180, 180), 1, Qt.SolidLine))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        for x in range(0, self.width(), cm_spacing):
            painter.drawLine(x, 0, x, self.height())
            # Markeringen met achtergrond
            text = f"{x/self.pixels_per_cm:.0f}"
            text_rect = painter.boundingRect(x + 2, 2, 20, 20, Qt.AlignLeft, text)
            painter.fillRect(text_rect, QColor(255, 255, 255, 200))
            painter.drawText(text_rect, Qt.AlignCenter, text)
            
        for y in range(0, self.height(), cm_spacing):
            painter.drawLine(0, y, self.width(), y)
            if y > 0:
                text = f"{y/self.pixels_per_cm:.0f}"
                text_rect = painter.boundingRect(2, y + 2, 20, 20, Qt.AlignLeft, text)
                painter.fillRect(text_rect, QColor(255, 255, 255, 200))
                painter.drawText(text_rect, Qt.AlignCenter, text)

    def draw_guide_lines(self, painter):
        if not self.current_rect:
            return
            
        # Horizontale hulplijnen
        painter.drawLine(0, self.current_rect.top(), self.width(), self.current_rect.top())
        painter.drawLine(0, self.current_rect.bottom(), self.width(), self.current_rect.bottom())
        # Verticale hulplijnen
        painter.drawLine(self.current_rect.left(), 0, self.current_rect.left(), self.height())
        painter.drawLine(self.current_rect.right(), 0, self.current_rect.right(), self.height())
        
        # Teken afmetingen langs de hulplijnen
        width_cm = self.current_rect.width() / self.pixels_per_cm
        height_cm = self.current_rect.height() / self.pixels_per_cm
        
        # Breedte label
        width_text = f"{width_cm:.1f} cm"
        painter.drawText(
            self.current_rect.center().x() - 20,
            self.current_rect.top() - 5,
            width_text
        )
        
        # Hoogte label
        height_text = f"{height_cm:.1f} cm"
        painter.drawText(
            self.current_rect.right() + 5,
            self.current_rect.center().y(),
            height_text
        )

    def clear(self):
        self.shapes = []
        self.update()

    def set_shape_type(self, shape_type):
        self.shape_type = shape_type

    def set_shape_color(self, color):
        if isinstance(color, QColor):
            self.shape_color = color
        else:
            self.shape_color = QColor(color)  # Convert Qt.GlobalColor to QColor

    def get_image(self):
        return self.image

    def set_dimensions(self, width, height):
        self.setFixedSize(int(width), int(height))
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.update()

    def get_current_shape(self):
        if self.shapes:
            return self.shapes[0]  # Return de laatste (en enige) vorm
        return None

    def set_line_thickness(self, thickness):
        self.line_thickness = thickness

class LabelDesigner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label Designer")
        self.setGeometry(100, 100, 1000, 800)
        
        # Initialiseer layout inputs eerst
        self.columns_input = QLineEdit("3")
        self.rows_input = QLineEdit("4")
        self.shape_margin = QLineEdit("0.2")
        
        # Validators toevoegen
        self.columns_input.setValidator(QIntValidator(1, 20))
        self.rows_input.setValidator(QIntValidator(1, 20))
        self.shape_margin.setValidator(QDoubleValidator(0.0, 5.0, 2))
        
        # Rest van de initialisatie
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Mode selectie
        mode_group = QGroupBox("Mode Selectie")
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(20)
        mode_layout.setContentsMargins(10, 15, 10, 15)
        self.mode_group = QButtonGroup()
        
        self.label_mode = QRadioButton("Label Mode")
        self.shape_mode = QRadioButton("Vorm Mode")
        self.mode_group.addButton(self.label_mode)
        self.mode_group.addButton(self.shape_mode)
        mode_layout.addWidget(self.label_mode)
        mode_layout.addWidget(self.shape_mode)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Label instellingen widget
        self.label_settings_widget = QWidget()
        label_settings_layout = QVBoxLayout(self.label_settings_widget)
        
        # Label instellingen
        settings_group = QGroupBox("Label Instellingen")
        settings_layout = QVBoxLayout()
        
        # Label afmetingen
        dimensions_group = QGroupBox("Afmetingen")
        dimensions_layout = QGridLayout()
        dimensions_layout.setSpacing(10)
        dimensions_layout.setContentsMargins(10, 15, 10, 15)
        
        self.label_width = QLineEdit("5")
        self.label_height = QLineEdit("3")
        self.margin = QLineEdit("0.2")
        self.outer_margin = QLineEdit("1.0")
        
        dimensions_layout.addWidget(QLabel("Label breedte (cm):"), 0, 0)
        dimensions_layout.addWidget(self.label_width, 0, 1)
        dimensions_layout.addWidget(QLabel("Label hoogte (cm):"), 1, 0)
        dimensions_layout.addWidget(self.label_height, 1, 1)
        dimensions_layout.addWidget(QLabel("Marge tussen labels (cm):"), 2, 0)
        dimensions_layout.addWidget(self.margin, 2, 1)
        dimensions_layout.addWidget(QLabel("Buitenmarge (cm):"), 3, 0)
        dimensions_layout.addWidget(self.outer_margin, 3, 1)
        
        dimensions_group.setLayout(dimensions_layout)
        settings_layout.addWidget(dimensions_group)

        # Label tekst
        text_group = QGroupBox("Label Tekst")
        text_layout = QHBoxLayout()
        self.label_text = QLineEdit()
        text_layout.addWidget(QLabel("Tekst:"))
        text_layout.addWidget(self.label_text)
        text_group.setLayout(text_layout)
        settings_layout.addWidget(text_group)
        
        settings_group.setLayout(settings_layout)
        label_settings_layout.addWidget(settings_group)

        # Vorm editor widget
        self.shape_editor_widget = QWidget()
        shape_editor_layout = QVBoxLayout(self.shape_editor_widget)
        
        # Vorm instellingen
        shape_settings = QGroupBox("Vorm Instellingen")
        shape_settings_layout = QGridLayout()
        shape_settings_layout.setSpacing(10)
        shape_settings_layout.setContentsMargins(10, 15, 10, 15)
        
        # Layout instellingen toggle
        self.manual_layout_checkbox = QCheckBox("Handmatige layout instellingen")
        self.manual_layout_checkbox.setToolTip("Vink aan om het aantal rijen en kolommen handmatig in te stellen")
        shape_editor_layout.insertWidget(0, self.manual_layout_checkbox)
        
        # Margin instellingen apart van handmatige layout
        margin_group = QGroupBox("Marge Instellingen")
        margin_layout = QGridLayout()
        margin_layout.addWidget(QLabel("Marge tussen vormen (cm):"), 0, 0)
        margin_layout.addWidget(self.shape_margin, 0, 1)
        margin_group.setLayout(margin_layout)
        shape_editor_layout.insertWidget(1, margin_group)  # Voeg toe voor layout_group
        
        # Layout instellingen groep (alleen kolommen en rijen)
        self.layout_group = QGroupBox("Layout Instellingen")
        layout_settings = QGridLayout()
        layout_settings.addWidget(QLabel("Aantal kolommen:"), 0, 0)
        layout_settings.addWidget(self.columns_input, 0, 1)
        layout_settings.addWidget(QLabel("Aantal rijen:"), 1, 0)
        layout_settings.addWidget(self.rows_input, 1, 1)
        
        self.layout_group.setLayout(layout_settings)
        shape_editor_layout.insertWidget(2, self.layout_group)  # Na margin_group
        
        # Vorm afmetingen (hergebruik van label afmetingen)
        self.shape_width = QLineEdit("5")
        self.shape_height = QLineEdit("3")
        shape_settings_layout.addWidget(QLabel("Vorm breedte (cm):"), 0, 0)
        shape_settings_layout.addWidget(self.shape_width, 0, 1)
        shape_settings_layout.addWidget(QLabel("Vorm hoogte (cm):"), 1, 0)
        shape_settings_layout.addWidget(self.shape_height, 1, 1)
        
        # Vorm type en kleur
        self.shape_selector = QComboBox()
        self.shape_selector.addItems(["Rechthoek", "Cirkel", "Driehoek"])
        self.shape_color_button = QPushButton("Vorm kleur")
        self.clear_button = QPushButton("Wis alles")
        
        shape_settings_layout.addWidget(QLabel("Vorm type:"), 2, 0)
        shape_settings_layout.addWidget(self.shape_selector, 2, 1)
        shape_settings_layout.addWidget(self.shape_color_button, 3, 0)
        shape_settings_layout.addWidget(self.clear_button, 3, 1)

        # Add a new QLineEdit for line thickness in the shape settings
        self.line_thickness = QLineEdit("2")
        shape_settings_layout.addWidget(QLabel("Lijn dikte (px):"), 4, 0)
        shape_settings_layout.addWidget(self.line_thickness, 4, 1)
        
        shape_settings.setLayout(shape_settings_layout)
        shape_editor_layout.addWidget(shape_settings)
        
        # Shape editor canvas met scroll area
        scroll_area = QScrollArea()
        self.shape_editor = ShapeEditor()
        self.shape_editor.setMinimumSize(800, 600)
        scroll_area.setWidget(self.shape_editor)
        scroll_area.setWidgetResizable(True)
        shape_editor_layout.addWidget(scroll_area)

        # Add both widgets to main layout
        layout.addWidget(self.label_settings_widget)
        layout.addWidget(self.shape_editor_widget)
        
        # Generate knop
        self.generate_button = QPushButton("Genereer Labels")
        layout.addWidget(self.generate_button)

        # Connecties
        self.label_mode.toggled.connect(self.update_mode)
        self.shape_mode.toggled.connect(self.update_mode)
        self.shape_selector.currentTextChanged.connect(self.shape_editor.set_shape_type)
        self.shape_color_button.clicked.connect(self.choose_shape_color)
        self.clear_button.clicked.connect(self.shape_editor.clear)
        self.generate_button.clicked.connect(self.generate_labels)
        self.shape_width.textChanged.connect(self.update_shape_preview)
        self.shape_height.textChanged.connect(self.update_shape_preview)

        # Connect the line thickness QLineEdit to the set_line_thickness method
        self.line_thickness.textChanged.connect(self.update_line_thickness)

        # Connecties voor nieuwe validaties
        self.shape_margin.textChanged.connect(self.update_margins)
        self.columns_input.textChanged.connect(self.validate_and_update_inputs)
        self.rows_input.textChanged.connect(self.validate_and_update_inputs)
        
        # Maak de tekstvelden wat breder voor betere leesbaarheid
        self.columns_input.setMinimumWidth(60)
        self.rows_input.setMinimumWidth(60)
        self.shape_margin.setMinimumWidth(60)
        
        # Voorkom negatieve waardes in de marges
        self.shape_margin.setValidator(QDoubleValidator(0.0, 5.0, 2))
        self.shape_margin.setText("0.2")  # Standaard waarde
        
        # Update initiële waardes
        self.validate_and_update_inputs()

        # Start in label mode
        self.label_mode.setChecked(True)
        self.update_mode()

        # Styling voor de UI
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-height: 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QLabel {
                color: #424242;
                font-size: 12px;
            }
            QRadioButton {
                spacing: 8px;
                color: #424242;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #2196F3;
                border: 2px solid #2196F3;
                border-radius: 9px;
            }
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #f5f5f5;
                color: #424242;
            }
        """)

        # Styling voor de checkbox
        self.manual_layout_checkbox.setStyleSheet("""
            QCheckBox {
                color: #424242;
                spacing: 8px;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QCheckBox::indicator:hover {
                border-color: #2196F3;
            }
        """)

        # Verbeterde tooltips voor layout instellingen
        self.manual_layout_checkbox.setToolTip(
            "Vink aan om het aantal rijen en kolommen handmatig in te stellen.\n"
            "Indien uitgevinkt wordt de optimale indeling automatisch berekend."
        )

        # Extra functionaliteiten toevoegen
        self.add_keyboard_shortcuts()
        self.setup_status_bar()

        # Voeg tooltips toe aan alle belangrijke elementen
        self.label_width.setToolTip("De breedte van het label in centimeters")
        self.label_height.setToolTip("De hoogte van het label in centimeters")
        self.margin.setToolTip("De ruimte tussen labels in centimeters")
        self.outer_margin.setToolTip("De marge rondom alle labels in centimeters")
        self.label_text.setToolTip("De tekst die op elk label wordt afgedrukt")
        self.shape_selector.setToolTip("Kies het type vorm dat u wilt tekenen")
        self.shape_color_button.setToolTip("Klik om de kleur van de vorm aan te passen")
        self.line_thickness.setToolTip("De dikte van de lijnen in pixels")
        self.clear_button.setToolTip("Wis de huidige vorm (Ctrl+D)")
        self.generate_button.setToolTip("Genereer het A4 vel met vormen of labels (Ctrl+G)")

        # Voeg placeholders toe aan tekstvelden
        self.label_text.setPlaceholderText("Voer label tekst in...")
        self.line_thickness.setPlaceholderText("2")

        # Maak de knoppen meer beschrijvend
        self.generate_button.setIcon(QIcon.fromTheme("document-save"))
        self.clear_button.setIcon(QIcon.fromTheme("edit-clear"))
        
        # Voeg wat extra validatie toe aan de invoervelden
        self.label_width.setValidator(QDoubleValidator(0.1, 21.0, 1))
        self.label_height.setValidator(QDoubleValidator(0.1, 29.7, 1))
        self.margin.setValidator(QDoubleValidator(0.0, 5.0, 2))
        self.outer_margin.setValidator(QDoubleValidator(0.0, 5.0, 2))
        self.line_thickness.setValidator(QIntValidator(1, 10))

        # Update status bar met meer informatie
        def update_status(text):
            self.statusBar.showMessage(f"Huidige modus: {text}")
        
        self.label_mode.toggled.connect(lambda: update_status("Label Mode"))
        self.shape_mode.toggled.connect(lambda: update_status("Vorm Mode"))

        # Voeg preview update toe wanneer layout settings veranderen
        self.manual_layout_checkbox.toggled.connect(self.update_layout_preview)
        self.columns_input.textChanged.connect(self.update_layout_preview)
        self.rows_input.textChanged.connect(self.update_layout_preview)
        self.shape_margin.textChanged.connect(self.update_layout_preview)

    def add_keyboard_shortcuts(self):
        # Sneltoetsen toevoegen
        self.generate_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        self.generate_shortcut.activated.connect(self.generate_labels)
        
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.clear_shortcut.activated.connect(self.shape_editor.clear)

    def setup_status_bar(self):
        # Status balk toevoegen
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Gereed")

    def update_mode(self):
        is_label_mode = self.label_mode.isChecked()
        self.label_settings_widget.setVisible(is_label_mode)
        self.shape_editor_widget.setVisible(not is_label_mode)
        self.generate_button.setText("Genereer Labels" if is_label_mode else "Genereer Vorm Labels")

    def validate_and_update_inputs(self):
        if not self.manual_layout_checkbox.isChecked():
            return  # Skip validatie in automatische modus
            
        try:
            DPI = 300
            A4_WIDTH_CM = 21
            A4_HEIGHT_CM = 29.7
            MARGIN_CM = float(self.shape_margin.text() or 0.2)

            current_shape = self.shape_editor.get_current_shape()
            if not current_shape:
                return

            _, rect, _ = current_shape
            shape_width_cm = rect.width() / self.shape_editor.pixels_per_cm
            shape_height_cm = rect.height() / self.shape_editor.pixels_per_cm

            # Bereken maximum mogelijke kolommen en rijen
            max_cols = int((A4_WIDTH_CM - 2) / (shape_width_cm + MARGIN_CM))
            max_rows = int((A4_HEIGHT_CM - 2) / (shape_height_cm + MARGIN_CM))

            # Update de validators
            self.columns_input.setValidator(QIntValidator(1, max_cols))
            self.rows_input.setValidator(QIntValidator(1, max_rows))

            # Update de tooltips met maximale waarden
            self.columns_input.setToolTip(f"Aantal kolommen (max: {max_cols})")
            self.rows_input.setToolTip(f"Aantal rijen (max: {max_rows})")

            # Corrigeer huidige waarden indien nodig
            try:
                cols = min(int(self.columns_input.text()), max_cols)
                rows = min(int(self.rows_input.text()), max_rows)
                self.columns_input.setText(str(cols))
                self.rows_input.setText(str(rows))
            except ValueError:
                self.columns_input.setText(str(min(3, max_cols)))
                self.rows_input.setText(str(min(4, max_rows)))

        except ValueError:
            # Fallback naar veilige waarden
            self.columns_input.setText("3")
            self.rows_input.setText("4")

    def update_shape_preview(self):
        try:
            width = float(self.shape_width.text()) * 37.8  # ongeveer pixels per cm
            height = float(self.shape_height.text()) * 37.8
            self.shape_editor.set_dimensions(width, height)
            
            # Update layout preview met de nieuwe vorm dimensies
            if not self.manual_layout_checkbox.isChecked():
                # Bereken optimale layout
                A4_WIDTH_CM = 21
                A4_HEIGHT_CM = 29.7
                MARGIN_CM = float(self.shape_margin.text() or 0.2)
                
                # Bereken hoeveel vormen er passen
                usable_width_cm = A4_WIDTH_CM - 2  # 1 cm marge aan elke kant
                usable_height_cm = A4_HEIGHT_CM - 2
                shape_width_cm = float(self.shape_width.text())
                shape_height_cm = float(self.shape_height.text())
                
                cols = max(1, int(usable_width_cm / (shape_width_cm + MARGIN_CM)))
                rows = max(1, int(usable_height_cm / (shape_height_cm + MARGIN_CM)))
                
                # Update de UI
                self.columns_input.setText(str(cols))
                self.rows_input.setText(str(rows))
                self.update_layout_preview()
                
        except ValueError:
            pass

    def update_margins(self):
        """Update de layout wanneer de marges veranderen"""
        self.validate_and_update_inputs()

    def choose_shape_color(self):
        color = QColorDialog.getColor(initial=self.shape_editor.shape_color)
        if color.isValid():
            self.shape_editor.set_shape_color(color)
            # Update kleur knop met gekozen kleur
            self.shape_color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    color: {('#000' if color.lightness() > 128 else '#fff')};
                }}
                QPushButton:hover {{
                    background-color: {color.darker(110).name()};
                }}
            """)

    def update_line_thickness(self):
        try:
            thickness = int(self.line_thickness.text())
            self.shape_editor.set_line_thickness(thickness)
        except ValueError:
            pass

    def generate_labels(self):
        self.statusBar.showMessage("Bezig met genereren...")
        if self.label_mode.isChecked():
            self.generate_label_sheet()
        else:
            self.export_shape()
        self.statusBar.showMessage("Genereren voltooid!", 3000)  # Toon 3 seconden

    def generate_label_sheet(self):
        # Instellingen
        DPI = 300
        A4_WIDTH_CM = 21
        A4_HEIGHT_CM = 29.7

        # Font instellen
        try:
            main_font = ImageFont.truetype("arial.ttf", 40)
            title_font = ImageFont.truetype("arial.ttf", 180)  # Nog groter naar 180
            count_font = ImageFont.truetype("arial.ttf", 200)  # Nog groter naar 200
            watermark_font = ImageFont.truetype("arial.ttf", 50)  # Groter watermark
        except:
            main_font = title_font = count_font = watermark_font = ImageFont.load_default()

        # Define watermark_font at the beginning of the generate_label_sheet method
        watermark_font = ImageFont.truetype("arial.ttf", 20)

        # Label instellingen van UI
        LABEL_WIDTH_CM = float(self.label_width.text())
        LABEL_HEIGHT_CM = float(self.label_height.text())
        MARGIN_CM = float(self.margin.text())
        OUTER_MARGIN_CM = float(self.outer_margin.text())

        # Omrekenen naar pixels
        A4_WIDTH = int(A4_WIDTH_CM * DPI / 2.54)
        A4_HEIGHT = int(A4_HEIGHT_CM * DPI / 2.54)
        LABEL_WIDTH = int(LABEL_WIDTH_CM * DPI / 2.54)
        LABEL_HEIGHT = int(LABEL_HEIGHT_CM * DPI / 2.54)
        MARGIN = int(MARGIN_CM * DPI / 2.54)
        OUTER_MARGIN = int(OUTER_MARGIN_CM * DPI / 2.54)

        # Berekenen hoeveel labels er op passen met buitenmarges
        usable_width = A4_WIDTH - (2 * OUTER_MARGIN)
        usable_height = A4_HEIGHT - (2 * OUTER_MARGIN)
        
        cols = (usable_width + MARGIN) // (LABEL_WIDTH + MARGIN)
        rows = (usable_height + MARGIN) // (LABEL_HEIGHT + MARGIN)

        # Herbereken marges voor gelijke verdeling
        total_label_width = cols * LABEL_WIDTH + (cols - 1) * MARGIN
        total_label_height = rows * LABEL_HEIGHT + (rows - 1) * MARGIN
        
        h_start = (A4_WIDTH - total_label_width) // 2
        v_start = (A4_HEIGHT - total_label_height) // 2

        # Afbeelding maken
        image = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        # "Machine Coating" tekst schuin bovenin
        title_text = "Machine Coating"
        # Bereken tekstgrootte voor title
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        
        # Maak een nieuwe afbeelding voor de gedraaide tekst met extra ruimte
        txt = Image.new('RGBA', (title_width + 300, title_height + 300), (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        # Voeg meerdere schaduwlagen toe voor meer diepte
        shadow_offsets = [(6,6), (4,4), (2,2)]
        for offset in shadow_offsets:
            d.text((150 + offset[0], 150 + offset[1]), title_text, font=title_font, fill=(0, 0, 0, 80))
        # Hoofdtekst met donkerder zwart
        d.text((150, 150), title_text, font=title_font, fill=(0, 0, 0))
        # Roteer de tekst en plak deze hoger op de pagina
        txt = txt.rotate(15, expand=1)
        image.paste(txt, (A4_WIDTH//2 - txt.width//2, 30), txt)  # Iets hoger geplaatst

        # Labels tekenen
        for row in range(rows):
            for col in range(cols):
                x0 = h_start + col * (LABEL_WIDTH + MARGIN)
                y0 = v_start + row * (LABEL_HEIGHT + MARGIN)
                x1 = x0 + LABEL_WIDTH
                y1 = y0 + LABEL_HEIGHT
                draw.rectangle([x0, y0, x1, y1], outline="black")

                # Label tekst toevoegen (indien ingevuld)
                if self.label_text.text():
                    text = self.label_text.text()
                    # Bereken tekstgrootte
                    text_bbox = draw.textbbox((0, 0), text, font=main_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    # Centreer de tekst in het label
                    text_x = x0 + (LABEL_WIDTH - text_width) // 2
                    text_y = y0 + (LABEL_HEIGHT - text_height) // 2
                    draw.text((text_x, text_y), text, font=main_font, fill="black")

        # Verbeterd aantal labels met schaduw
        total_labels = rows * cols
        label_count_text = f"{total_labels}"
        count_bbox = draw.textbbox((0, 0), label_count_text, font=count_font)
        count_width = count_bbox[2] - count_bbox[0]
        
        # Teken meerdere schaduwlagen voor het aantal
        shadow_positions = [(5,5), (3,3), (2,2)]
        for offset in shadow_positions:
            draw.text((A4_WIDTH - count_width - 40 + offset[0], A4_HEIGHT - 160 + offset[1]), 
                     label_count_text, font=count_font, fill=(0, 0, 0, 60))
        
        # Hoofdtekst van het aantal
        draw.text((A4_WIDTH - count_width - 40, A4_HEIGHT - 160), 
                 label_count_text, font=count_font, fill=(0, 0, 0))

        # Afmetingen watermerk
        dimensions_text = f"Label afmetingen: {LABEL_WIDTH_CM:.1f} x {LABEL_HEIGHT_CM:.1f} cm"
        draw.text((A4_WIDTH/2, A4_HEIGHT-40), dimensions_text,
                 font=watermark_font, fill="gray", anchor="mb")

        # Afbeelding opslaan
        image.save("a4_labels.png")

    def validate_layout(self, total_width, total_height, A4_WIDTH, A4_HEIGHT):
        """Controleert of de layout past op het A4 vel"""
        if total_width > A4_WIDTH:
            self.statusBar.showMessage("Waarschuwing: De vormen zijn te breed voor het A4 vel!", 5000)
            return False
        if total_height > A4_HEIGHT:
            self.statusBar.showMessage("Waarschuwing: De vormen zijn te hoog voor het A4 vel!", 5000)
            return False
        return True

    def export_shape(self):
        # Instellingen
        DPI = 300
        A4_WIDTH_CM = 21
        A4_HEIGHT_CM = 29.7
        MARGIN_CM = float(self.shape_margin.text()) if self.shape_margin.text() else 0.2
        OUTER_MARGIN_CM = float(self.outer_margin.text()) if self.outer_margin.text() else 1.0

        # Vorm afmetingen (van getekende vorm)
        current_shape = self.shape_editor.get_current_shape()
        if not current_shape:
            print("Teken eerst een vorm")
            return

        shape_type, rect, color = current_shape
        SHAPE_WIDTH_CM = rect.width() / self.shape_editor.pixels_per_cm
        SHAPE_HEIGHT_CM = rect.height() / self.shape_editor.pixels_per_cm

        try:
            # Font instellen met fallbacks
            try:
                title_font = ImageFont.truetype("arial.ttf", 180)  # Match met generate_label_sheet
                count_font = ImageFont.truetype("arial.ttf", 200)  # Match met generate_label_sheet
                watermark_font = ImageFont.truetype("arial.ttf", 50)  # Match met generate_label_sheet
            except:
                try:
                    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 180)
                    count_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 200)
                    watermark_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
                except:
                    title_font = count_font = watermark_font = ImageFont.load_default()

            # Gebruik handmatige of automatische layout
            if self.manual_layout_checkbox.isChecked():
                try:
                    cols = int(self.columns_input.text())
                    rows = int(self.rows_input.text())
                except ValueError:
                    self.statusBar.showMessage("Ongeldige rij- of kolomwaarden, gebruik automatische berekening", 3000)
                    cols = max(1, (usable_width + MARGIN) // (SHAPE_WIDTH + MARGIN))
                    rows = max(1, (usable_height + MARGIN) // (SHAPE_HEIGHT + MARGIN))
            else:
                # Bereken optimaal aantal kolommen en rijen
                usable_width = A4_WIDTH - (2 * OUTER_MARGIN)
                usable_height = A4_HEIGHT - (2 * OUTER_MARGIN)
                
                # Bereken hoeveel vormen er op een rij/kolom passen
                cols = max(1, (usable_width + MARGIN) // (SHAPE_WIDTH + MARGIN))
                rows = max(1, (usable_height + MARGIN) // (SHAPE_HEIGHT + MARGIN))

                # Update de UI met de berekende waarden
                self.columns_input.setText(str(cols))
                self.rows_input.setText(str(rows))

            # Omrekenen naar pixels
            A4_WIDTH = int(A4_WIDTH_CM * DPI / 2.54)
            A4_HEIGHT = int(A4_HEIGHT_CM * DPI / 2.54)
            SHAPE_WIDTH = int(SHAPE_WIDTH_CM * DPI / 2.54)
            SHAPE_HEIGHT = int(SHAPE_HEIGHT_CM * DPI / 2.54)
            MARGIN = int(MARGIN_CM * DPI / 2.54)
            OUTER_MARGIN = int(OUTER_MARGIN_CM * DPI / 2.54)

            # Bereken layout met vaste vorm dimensies
            total_width = cols * SHAPE_WIDTH + (cols - 1) * MARGIN
            total_height = rows * SHAPE_HEIGHT + (rows - 1) * MARGIN
            
            h_start = (A4_WIDTH - total_width) // 2
            v_start = (A4_HEIGHT - total_height) // 2

            # Controleer of de layout past op het A4 vel
            if not self.validate_layout(total_width, total_height, A4_WIDTH, A4_HEIGHT):
                print("De gekozen layout past niet op het A4 vel")
                return

            # Ga door met exporteren als de validatie succesvol is
            image = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
            draw = ImageDraw.Draw(image)

            # Teken grid lijnen voor referentie
            grid_color = (240, 240, 240)
            for x in range(h_start, h_start + total_width + 1, SHAPE_WIDTH + MARGIN):
                draw.line([(x, v_start), (x, v_start + total_height)], fill=grid_color)
            for y in range(v_start, v_start + total_height + 1, SHAPE_HEIGHT + MARGIN):
                draw.line([(h_start, y), (h_start + total_width, y)], fill=grid_color)

            # Teken vormen op elke positie
            for row in range(rows):
                for col in range(cols):
                    x = h_start + col * (SHAPE_WIDTH + MARGIN)
                    y = v_start + row * (SHAPE_HEIGHT + MARGIN)
                    
                    # Gebruik de default kleur #723744 als er geen kleur is geselecteerd
                    if isinstance(color, QColor):
                        shape_color = color.getRgb()[:3]
                    else:
                        shape_color = QColor("#723744").getRgb()[:3]
                    
                    if shape_type == "Rechthoek":
                        # Gebruik de lijndikte van de editor
                        for i in range(self.shape_editor.line_thickness):
                            offset = i - self.shape_editor.line_thickness // 2
                            draw.rectangle([
                                x + offset, y + offset, 
                                x + SHAPE_WIDTH - offset, y + SHAPE_HEIGHT - offset
                            ], outline=shape_color)
                    elif shape_type == "Cirkel":
                        # Teken cirkel met juiste lijndikte
                        for i in range(self.shape_editor.line_thickness):
                            offset = i - self.shape_editor.line_thickness // 2
                            draw.ellipse([
                                x + offset, y + offset, 
                                x + SHAPE_WIDTH - offset, y + SHAPE_HEIGHT - offset
                            ], outline=shape_color)
                    elif shape_type == "Driehoek":
                        # Verbeterde driehoek met exacte afmetingen en lijndikte
                        for i in range(self.shape_editor.line_thickness):
                            offset = i - self.shape_editor.line_thickness // 2
                            points = [
                                (int(x + SHAPE_WIDTH/2), y + offset),           # Top midden
                                (x + offset, y + SHAPE_HEIGHT - offset),        # Links onder
                                (x + SHAPE_WIDTH - offset, y + SHAPE_HEIGHT - offset)  # Rechts onder
                            ]
                            draw.polygon(points, outline=shape_color)

            # "Machine Coating" tekst schuin bovenin
            title_text = "Machine Coating"
            # Bereken tekstgrootte voor title
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            # Maak een nieuwe afbeelding voor de gedraaide tekst met meer ruimte
            txt = Image.new('RGBA', (title_width + 300, title_height + 300), (255, 255, 255, 0))
            d = ImageDraw.Draw(txt)
            
            # Voeg meerdere schaduwlagen toe voor meer diepte
            shadow_offsets = [(6,6), (4,4), (2,2)]
            for offset in shadow_offsets:
                d.text((150 + offset[0], 150 + offset[1]), title_text, 
                      font=title_font, fill=(0, 0, 0, 80))
            # Hoofdtekst met donkerder zwart
            d.text((150, 150), title_text, font=title_font, fill=(0, 0, 0))
            
            # Roteer en plaats hoger op de pagina
            txt = txt.rotate(15, expand=1, fillcolor=(255, 255, 255, 0))
            image.paste(txt, (A4_WIDTH//2 - txt.width//2, 30), txt)

            # Verbeterd aantal met meerdere schaduwlagen
            total_shapes = rows * cols
            count_text = f"{total_shapes}"
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_height = count_bbox[3] - count_bbox[1]

            # Teken meerdere schaduwlagen voor het aantal
            shadow_positions = [(5,5), (3,3), (2,2)]
            for offset in shadow_positions:
                draw.text(
                    (A4_WIDTH - count_width - 40 + offset[0], A4_HEIGHT - 160 + offset[1]),
                    count_text,
                    font=count_font,
                    fill=(0, 0, 0, 60)
                )
            
            # Hoofdtekst van het aantal
            draw.text(
                (A4_WIDTH - count_width - 40, A4_HEIGHT - 160),
                count_text,
                font=count_font,
                fill=(0, 0, 0)
            )

            # Voeg een subtiel watermerk toe
            dimensions_text = f"Vorm afmetingen: {SHAPE_WIDTH_CM:.1f} x {SHAPE_HEIGHT_CM:.1f} cm"
            watermark_color = (150, 150, 150, 180)  # Semi-transparant
            draw.text(
                (A4_WIDTH/2, A4_HEIGHT-35),
                dimensions_text,
                font=watermark_font,
                fill=watermark_color,
                anchor="mb"
            )

            # Afbeelding opslaan met hoge kwaliteit
            image.save("a4_shapes.png", quality=95, dpi=(DPI, DPI))
            print(f"Vormen geëxporteerd als a4_shapes.png met {total_shapes} vormen")

        except Exception as e:
            print(f"Fout bij exporteren: {str(e)}")

    def update_layout_preview(self):
        """Update de status balk met layout informatie"""
        try:
            if self.manual_layout_checkbox.isChecked():
                cols = int(self.columns_input.text() or "0")
                rows = int(self.rows_input.text() or "0")
                total = cols * rows
                self.statusBar.showMessage(
                    f"Handmatige layout: {cols} kolommen × {rows} rijen = {total} vormen"
                )
            else:
                self.statusBar.showMessage(
                    "Automatische layout: optimale verdeling wordt berekend tijdens genereren"
                )
        except ValueError:
            self.statusBar.showMessage(
                "Ongeldige waarden voor rijen of kolommen"
            )

def main():
    app = QApplication(sys.argv)
    window = LabelDesigner()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
