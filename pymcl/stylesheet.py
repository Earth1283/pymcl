STYLESHEET = """
QWidget {
    background-color: #1a1a1a;
    color: #f0f0f0;
    font-family: 'Segoe UI', Inter, sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #1a1a1a;
}
QFrame#central_widget_frame {
    border: none;
    border-radius: 16px;
    background-color: rgba(37, 37, 37, 0.85);
    padding: 10px;
}
QLabel {
    color: #e0e0e0;
    font-size: 13px;
    background: transparent;
}
QLabel#title_label {
    font-size: 36px;
    font-weight: 700;
    color: #ffffff;
    padding: 0px;
    background: transparent;
    letter-spacing: 1px;
}
QLabel#subtitle_label {
    font-size: 15px;
    color: #888;
    background: transparent;
    margin-top: 5px;
}
QLabel#section_label {
    font-size: 11px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    background: transparent;
}
QLineEdit {
    background-color: #1e1e1e;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    padding: 0 18px;
    font-size: 15px;
    color: #ffffff;
    min-height: 55px;
}
QLineEdit:focus {
    border: 2px solid #4a9eff;
    background-color: #242424;
}
QLineEdit:hover {
    border: 2px solid #505050;
}
QComboBox {
    background-color: #1e1e1e;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    padding: 0 18px;
    font-size: 15px;
    color: #ffffff;
    min-height: 55px;
}
QComboBox:focus {
    border: 2px solid #4a9eff;
    background-color: #242424;
}
QComboBox:hover {
    border: 2px solid #505050;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #888;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    selection-background-color: #4a9eff;
    selection-color: #ffffff;
    padding: 5px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 15px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #3a3a3a;
}
QPushButton {
    background-color: #4a9eff;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0 20px;
    font-size: 15px;
    font-weight: 600;
    min-height: 50px;
}
QPushButton:hover {
    background-color: #5badff;
}
QPushButton:pressed {
    background-color: #3a8eef;
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666;
}

QPushButton#secondary_button {
    background-color: #3c3c3c;
    color: #f0f0f0;
    border: none;
}
QPushButton#secondary_button:hover {
    background-color: #4a4a4a;
}
QPushButton#secondary_button:pressed {
    background-color: #303030;
}
QPushButton#danger_button {
    background-color: rgba(255, 80, 80, 0.2);
    color: #ff8080;
    border: 1px solid rgba(255, 80, 80, 0.5);
}
QPushButton#danger_button:hover {
    background-color: rgba(255, 80, 80, 0.3);
    border-color: rgba(255, 80, 80, 0.7);
}
QPushButton#danger_button:pressed {
    background-color: rgba(255, 80, 80, 0.4);
}
QProgressBar {
    border: none;
    border-radius: 8px;
    text-align: center;
    background-color: #1e1e1e;
    color: #ffffff;
    font-weight: 600;
    font-size: 13px;
    min-height: 32px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #4a9eff, stop:1 #5ab0ff);
    border-radius: 8px;
}
QLabel#status_label {
    color: #999;
    font-size: 13px;
    background: transparent;
    padding: 8px;
}

QCheckBox {
    spacing: 10px;
    font-size: 15px;
    font-weight: 600;
    color: #f0f0f0;
    background: transparent;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #505050;
    border-radius: 4px;
    background-color: #1e1e1e;
}
QCheckBox::indicator:hover {
    border-color: #606060;
}
QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white' width='18px' height='18px'%3E%3Cpath d='M0 0h24v24H0z' fill='none'/%3E%3Cpath d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/%3E%3C/svg%3E");
}

QListWidget {
    background-color: #1e1e1e;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    padding: 5px;
    font-size: 14px;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    color: #f0f0f0;
}
QListWidget::item:hover {
    background-color: #2a2a2a;
}
QListWidget::item:selected {
    background-color: #4a9eff;
    color: #ffffff;
}

QWidget#main_central_widget {
    background: transparent;
}

QWidget#left_title_container {
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 16px;
    padding: 10px;
}

QFrame#title_frame {
    background-color: transparent;
    border-radius: 12px;
    border: none;
}

QDialog {
    background-color: #252525;
}

QPushButton#nav_button, QPushButton#nav_button_active {
    background-color: transparent;
    border: 1px solid transparent;
    color: #aaa;
    font-size: 15px;
    font-weight: 600;
    text-align: left;
    padding: 12px 20px;
    border-radius: 8px;
    min-height: 40px;
}

QPushButton#nav_button:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #fff;
}

QPushButton#nav_button_active {
    background-color: rgba(74, 158, 255, 0.1);
    color: #6ab0ff;
    border: 1px solid rgba(74, 158, 255, 0.2);
}
QSlider::groove:horizontal {
    border: 1px solid #3a3a3a;
    height: 4px;
    background: #1e1e1e;
    margin: 2px 0;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #4a9eff;
    border: 1px solid #4a9eff;
    width: 18px;
    height: 18px;
    margin: -8px 0;
    border-radius: 9px;
}

QSlider::add-page:horizontal {
    background: #1e1e1e;
}

QSlider::sub-page:horizontal {
    background: #4a9eff;
}

QScrollArea#content_scroll_area {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #444;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #555;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #444;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #555;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

QMenuBar {
    background-color: #1a1a1a;
    color: #f0f0f0;
    spacing: 10px;
}
QMenuBar::item {
    padding: 5px 10px;
    background: transparent;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #3c3c3c;
}
QMenu {
    background-color: #2d2d2d;
    color: #f0f0f0;
    border: 1px solid #3c3c3c;
    padding: 5px;
}
QMenu::item {
    padding: 8px 25px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #4a9eff;
}
QMenu::separator {
    height: 1px;
    background: #3c3c3c;
    margin: 5px 0;
}

/* Mod Browser */
QWidget#floating_search_container {
    background-color: rgba(37, 37, 37, 0.95);
    border-bottom: 1px solid #3a3a3a;
}
QWidget#mod_card {
    background-color: #2a2a2a;
    border-radius: 8px;
    border: 1px solid #3a3a3a;
    padding: 15px;
}
QWidget#mod_card:hover {
    border-color: #4a9eff;
}
QLabel#mod_card_title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
}
QLabel#mod_card_downloads {
    font-size: 12px;
    color: #888;
}
QPushButton#download_badge {
    background-color: #4a9eff;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    padding: 5px 15px;
    font-size: 12px;
    font-weight: 600;
    min-height: 24px;
}
QPushButton#download_badge:hover {
    background-color: #5badff;
}
"""
