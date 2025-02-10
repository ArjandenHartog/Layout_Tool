from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QCheckBox, QColorDialog, QGroupBox, QComboBox,
                           QScrollArea, QFrame, QRadioButton, QButtonGroup,
                           QGridLayout, QShortcut, QStatusBar)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QKeySequence
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
        self.shape_color = QColor(Qt.black)  # Initialize with QColor object
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
        painter.setRenderHint(QPainter.Antialiasing)  # Voeg anti-aliasing toe
        painter.fillRect(self.rect(), Qt.white)
        
        # Grid tekenen met verbeterde stijl
        self.draw_enhanced_grid(painter)
        
        # Preview van vorm onder muis als er niet getekend wordt
        if not self.drawing and not self.shapes:
            preview_size = 50
            preview_rect = QRect(
                self.hover_point.x() - preview_size//2,
                self.hover_point.y() - preview_size//2,
                preview_size, preview_size
            )
            painter.setPen(QPen(self.shape_color, 1, Qt.DashLine))
            self.draw_shape(painter, self.shape_type, preview_rect)

        # Teken opgeslagen vormen
        for shape_type, rect, color in self.shapes:
            # Teken schaduw
            shadow_offset = 2
            shadow_rect = QRect(rect)
            shadow_rect.translate(shadow_offset, shadow_offset)
            painter.setPen(QPen(QColor(100, 100, 100, 50), 2))
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
            # Teken driehoek met gelijkmatige punten
            points = [
                rect.topLeft() + QPoint(rect.width()/2, 0),  # top middle
                rect.bottomLeft(),                           # bottom left
                rect.bottomRight()                           # bottom right
            ]
            # Teken driehoek met vloeiende lijnen
            for i in range(3):
                painter.drawLine(points[i], points[(i+1)%3])

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
        
        # Hoofdwidget en layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Mode selectie
        mode_group = QGroupBox("Mode Selectie")
        mode_layout = QHBoxLayout()
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

        # Start in label mode
        self.label_mode.setChecked(True)
        self.update_mode()

        # Styling voor de UI
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                background-color: white;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLabel {
                color: #333;
            }
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
        """)

        # Extra functionaliteiten toevoegen
        self.add_keyboard_shortcuts()
        self.setup_status_bar()

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

    def update_shape_preview(self):
        try:
            width = float(self.shape_width.text()) * 37.8  # ongeveer pixels per cm
            height = float(self.shape_height.text()) * 37.8
            self.shape_editor.set_dimensions(width, height)
        except ValueError:
            pass

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
            title_font = ImageFont.truetype("arial.ttf", 60)  # Grotere font voor "Machine Coating"
            count_font = ImageFont.truetype("arial.ttf", 80)  # Nog grotere font voor aantal labels
        except:
            main_font = title_font = count_font = ImageFont.load_default()

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
        
        # Maak een nieuwe afbeelding voor de gedraaide tekst
        txt = Image.new('RGBA', (title_width + 50, title_height + 50), (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        d.text((25, 25), title_text, font=title_font, fill="black")
        # Roteer de tekst en plak deze op de juiste positie
        txt = txt.rotate(15, expand=1)
        image.paste(txt, (A4_WIDTH//2 - txt.width//2, 100), txt)

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

        # Aantal labels (groot, rechtsonder)
        total_labels = rows * cols
        label_count_text = f"{total_labels}"
        # Bereken tekstgrootte voor aantal labels
        count_bbox = draw.textbbox((0, 0), label_count_text, font=count_font)
        count_width = count_bbox[2] - count_bbox[0]
        draw.text((A4_WIDTH - count_width - 40, A4_HEIGHT - 120), 
                 label_count_text, font=count_font, fill="black")

        # Afmetingen watermerk
        dimensions_text = f"Label afmetingen: {LABEL_WIDTH_CM:.1f} x {LABEL_HEIGHT_CM:.1f} cm"
        draw.text((A4_WIDTH/2, A4_HEIGHT-40), dimensions_text,
                 font=watermark_font, fill="gray", anchor="mb")

        # Afbeelding opslaan
        image.save("a4_labels.png")

    def export_shape(self):
        # Instellingen
        DPI = 300
        A4_WIDTH_CM = 21
        A4_HEIGHT_CM = 29.7
        MARGIN_CM = float(self.margin.text()) if self.margin.text() else 0.2
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
                title_font = ImageFont.truetype("arial.ttf", 60)
                count_font = ImageFont.truetype("arial.ttf", 80)
                watermark_font = ImageFont.truetype("arial.ttf", 30)
            except:
                try:
                    # Try DejaVu Sans as alternative
                    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
                    count_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 80)
                    watermark_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
                except:
                    title_font = count_font = watermark_font = ImageFont.load_default()

            # Omrekenen naar pixels
            A4_WIDTH = int(A4_WIDTH_CM * DPI / 2.54)
            A4_HEIGHT = int(A4_HEIGHT_CM * DPI / 2.54)
            SHAPE_WIDTH = int(SHAPE_WIDTH_CM * DPI / 2.54)
            SHAPE_HEIGHT = int(SHAPE_HEIGHT_CM * DPI / 2.54)
            MARGIN = int(MARGIN_CM * DPI / 2.54)
            OUTER_MARGIN = int(OUTER_MARGIN_CM * DPI / 2.54)

            # Bereken layout
            usable_width = A4_WIDTH - (2 * OUTER_MARGIN)
            usable_height = A4_HEIGHT - (2 * OUTER_MARGIN)
            
            cols = (usable_width + MARGIN) // (SHAPE_WIDTH + MARGIN)
            rows = (usable_height + MARGIN) // (SHAPE_HEIGHT + MARGIN)

            total_width = cols * SHAPE_WIDTH + (cols - 1) * MARGIN
            total_height = rows * SHAPE_HEIGHT + (rows - 1) * MARGIN
            
            h_start = (A4_WIDTH - total_width) // 2
            v_start = (A4_HEIGHT - total_height) // 2

            # Maak A4 afbeelding
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
                    
                    # Gebruik de geselecteerde kleur voor de vorm
                    if isinstance(color, QColor):
                        shape_color = color.getRgb()[:3]  # Convert QColor to RGB tuple
                    else:
                        shape_color = QColor(color).getRgb()[:3]  # Convert Qt.GlobalColor to RGB
                    
                    if shape_type == "Rechthoek":
                        draw.rectangle([x, y, x + SHAPE_WIDTH, y + SHAPE_HEIGHT], 
                                     outline=shape_color, width=2)
                    elif shape_type == "Cirkel":
                        draw.ellipse([x, y, x + SHAPE_WIDTH, y + SHAPE_HEIGHT], 
                                   outline=shape_color, width=2)
                    elif shape_type == "Driehoek":
                        # Verbeterde driehoek met exacte afmetingen
                        points = [
                            (x + SHAPE_WIDTH/2, y),  # top middle
                            (x, y + SHAPE_HEIGHT),    # bottom left
                            (x + SHAPE_WIDTH, y + SHAPE_HEIGHT)  # bottom right
                        ]
                        # Teken driehoek met vulling en rand
                        draw.polygon(points, outline=shape_color)

            # "Machine Coating" tekst schuin bovenin
            title_text = "Machine Coating"
            # Bereken tekstgrootte voor title
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            # Maak een nieuwe afbeelding voor de gedraaide tekst
            txt = Image.new('RGBA', (title_width + 150, title_height + 150), (255, 255, 255, 0))
            d = ImageDraw.Draw(txt)
            
            # Voeg schaduw effect toe aan de titel
            shadow_offset = 3
            d.text((75 + shadow_offset, 75 + shadow_offset), title_text, 
                  font=title_font, fill=(100, 100, 100, 128))  # Semi-transparante schaduw
            d.text((75, 75), title_text, font=title_font, fill=(50, 50, 50))
            
            # Roteer en voeg gloed effect toe
            txt = txt.rotate(15, expand=1, fillcolor=(255, 255, 255, 0))
            image.paste(txt, (A4_WIDTH//2 - txt.width//2, 30), txt)

            # Aantal vormen (groot, rechtsonder)
            total_shapes = rows * cols
            count_text = f"{total_shapes}"
            # Define count_width and count_height before using them in the export_shape method
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_height = count_bbox[3] - count_bbox[1]
            # Maak een mooie achtergrond voor het aantal
            count_bg_margin = 30
            bg_rect = [
                A4_WIDTH - count_width - count_bg_margin*2 - 40,
                A4_HEIGHT - count_height - count_bg_margin*2 - 40,
                A4_WIDTH - 40 + count_bg_margin,
                A4_HEIGHT - 40 + count_bg_margin
            ]
            # Teken een subtiele gradient achtergrond
            for i in range(count_bg_margin):
                alpha = 255 - (i * 255 // count_bg_margin)
                draw.rectangle([
                    bg_rect[0] - i,
                    bg_rect[1] - i,
                    bg_rect[2] + i,
                    bg_rect[3] + i
                ], fill=(245, 245, 245, alpha))

            # Teken aantal met verbeterd schaduw effect
            shadow_offset = 3
            for offset in range(1, shadow_offset + 1):
                alpha = 100 - (offset * 30)
                draw.text(
                    (A4_WIDTH - count_width - 40 + offset, A4_HEIGHT - 120 + offset),
                    count_text,
                    font=count_font,
                    fill=(100, 100, 100, alpha)
                )
            draw.text(
                (A4_WIDTH - count_width - 40, A4_HEIGHT - 120),
                count_text,
                font=count_font,
                fill=(50, 50, 50)
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

def main():
    app = QApplication(sys.argv)
    window = LabelDesigner()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
