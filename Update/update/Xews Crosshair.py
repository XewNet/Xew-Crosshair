import sys
import os
from PyQt5.QtCore import Qt, QSize, QPoint, QLoggingCategory
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QGridLayout, QScrollArea, QSizePolicy, QFileDialog, QSlider
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QSpacerItem
import requests
import zipfile
import shutil
import subprocess

REMOTE_VERSION_URL = "https://github.com/XewNet/Xew-Crosshair/raw/refs/heads/main/version.txt"
REMOTE_UPDATE_URL = "https://github.com/XewNet/Xew-Crosshair/raw/refs/heads/main/update.zip"
LOCAL_VERSION_FILE = "version.txt"
UPDATE_ZIP = "update.zip"
UPDATE_DIR = "update_temp/"
OLD_EXE = "Xews Crosshair"  # Name of the current .exe
NEW_EXE = "Xews Crosshair"  # Name of the new .exe inside the .zip

def fetch_remote_version():
    """Fetch the version from the server."""
    try:
        print("Fetching remote version...")
        response = requests.get(REMOTE_VERSION_URL, timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"Error fetching remote version: {e}")
        return None

def download_update():
    """Download the update.zip file from the server."""
    try:
        print("Downloading update...")
        response = requests.get(REMOTE_UPDATE_URL, stream=True, timeout=10)
        response.raise_for_status()
        with open(UPDATE_ZIP, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Update downloaded successfully!")
    except Exception as e:
        print(f"Error downloading update: {e}")

def apply_update():
    """Extract and replace the old script with the new one."""
    try:
        print("Applying update...")
        if not os.path.exists(UPDATE_DIR):
            os.makedirs(UPDATE_DIR)

        # Extract the update.zip file
        with zipfile.ZipFile(UPDATE_ZIP, "r") as zip_ref:
            zip_ref.extractall(UPDATE_DIR)

        # Auto-detect .py file in the extracted folder
        new_exe_path = None
        for file in os.listdir(UPDATE_DIR):
            if file.endswith(".py"):
                new_exe_path = os.path.join(UPDATE_DIR, file)
                break

        if new_exe_path:
            print(f"Found new script: {new_exe_path}")

            # Delete the old script
            if os.path.exists(OLD_EXE):
                os.remove(OLD_EXE)

            # Rename the new script to match the old script's name
            shutil.move(new_exe_path, OLD_EXE)
            print(f"Renamed {new_exe_path} to {OLD_EXE}")

        else:
            print("No .py file found in update package!")

        # Clean up temporary files
        try:
            shutil.rmtree(UPDATE_DIR)
            print("Temporary files cleaned up successfully!")
        except PermissionError as e:
            print(f"Error cleaning up temporary files: {e}")
        except Exception as e:
            print(f"Unexpected error during cleanup: {e}")
        
        os.remove(UPDATE_ZIP)  # Remove the ZIP file itself

        print("Update applied successfully!")

        # Launch the new script
        print("Launching new version...")
        subprocess.Popen(["python", OLD_EXE])  # Start the new script
    except Exception as e:
        print(f"Error applying update: {e}")

def main():
    # Read local version
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            local_version = f.read().strip()
    except FileNotFoundError:
        print("Local version file not found. Assuming version 0.0.0.")
        local_version = "0.0.0"

    print(f"Local version: {local_version}")

    # Fetch remote version
    remote_version = fetch_remote_version()
    if not remote_version:
        print("Failed to retrieve remote version. Exiting updater.")
        return

    print(f"Remote version: {remote_version}")

    # Compare versions
    if remote_version > local_version:
        print("New version available! Starting update...")
        download_update()
        apply_update()

        # Update local version file
        with open(LOCAL_VERSION_FILE, "w") as f:
            f.write(remote_version)
        print("Update completed successfully!")
    else:
        print("No updates available. You're up-to-date!")



class CrosshairOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.Tool)
        self.crosshair_label = QLabel(self)
        self.crosshair_pixmap = None
        self.original_pixmap = None  # Store the original pixmap
        self.last_position = None    # Track the last position
        
    def set_crosshair(self, icon_path, size=None):
        """Set the crosshair image, optionally scaling it to a specific size."""
        # Store the original, unmodified pixmap
        self.original_pixmap = QPixmap(icon_path)
        
        if not self.original_pixmap.isNull():
            # Create a copy for display use
            self.crosshair_pixmap = QPixmap(self.original_pixmap)
            
            max_size = QSize(100, 100)  # Max size of the crosshair
            self.crosshair_pixmap = self.crosshair_pixmap.scaled(
                max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            if size:
                # If a size is provided, scale the crosshair
                self.crosshair_pixmap = self.crosshair_pixmap.scaled(
                    size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

            self.setFixedSize(self.crosshair_pixmap.size())
            self.crosshair_label.setPixmap(self.crosshair_pixmap)
            self.crosshair_label.setFixedSize(self.crosshair_pixmap.size())
            self.update()  # Redraw the overlay

    def paintEvent(self, event):
        """Handle the drawing of the crosshair image."""
        if self.crosshair_pixmap:
            painter = QPainter(self)
            # The crosshair is displayed through the label, so nothing else needs to be done here
    
    def resizeEvent(self, event):
        """Handle resizing events."""
        if self.crosshair_pixmap:
            # Ensure the label always fills the entire widget
            self.crosshair_label.setGeometry(0, 0, self.width(), self.height())
    
    def changeSize(self, size):
        """Resize the crosshair without changing its position."""
        if self.original_pixmap:
            # Store current position
            current_pos = self.pos()
            
            # Create a new scaled pixmap
            new_pixmap = self.original_pixmap.scaled(
                size, size,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Update the crosshair pixmap
            self.crosshair_pixmap = new_pixmap
            
            # Update the label
            self.crosshair_label.setPixmap(new_pixmap)
            self.crosshair_label.setFixedSize(new_pixmap.size())
            
            # Resize the overlay
            self.setFixedSize(new_pixmap.size())
            
            # Explicitly restore position
            self.move(current_pos)
            
            # Save this position
            self.last_position = current_pos

class StyledWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xew Crosshair v.1.1")
        self.setGeometry(100, 100, 900, 500)  # Slightly bigger to give padding/border look

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # Grey margin around the app

        self.child_window = MyWindow()
        layout.addWidget(self.child_window)

        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))  # Grey border/background

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xew Crosshair v.1.1")
        self.setGeometry(100, 100, 800, 400)
        self.current_overlay = None

        # Main layout with a horizontal layout (for sidebar + stacked widget)
        main_layout = QHBoxLayout()

        # Create stacked widget to switch between pages
        self.stacked_widget = QStackedWidget()

        # Create pages
        self.crosshair_page = self.show_crosshairs()
        self.settings_page = self.show_settings()
        self.misc_page = self.show_misc()

        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.crosshair_page)
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.misc_page)

        # Create a vertical layout for buttons (side bar)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(20)

        buttons = [
            ("Crosshairs", lambda: self.stacked_widget.setCurrentIndex(0)),
            ("Crosshair Settings", lambda: self.stacked_widget.setCurrentIndex(1)),
            ("Misc", lambda: self.stacked_widget.setCurrentIndex(2)),
        ]

        for text, action in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(60)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-size: 16px;
                    padding: 10px;
                    border: 2px solid #444;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.4);
                }
            """)
            btn.clicked.connect(action)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Create a separator (vertical line)
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Add the sidebar, separator, and stacked widget to the main layout (horizontal)
        # Sidebar container with grey background
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setStyleSheet("""
            background-color: #2e2e2e;
        """)
        main_layout.addWidget(sidebar_widget, stretch=1)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.stacked_widget, stretch=4)

        # Set the main layout for the window
        self.setLayout(main_layout)

    def show_crosshairs(self):
        """Create and return the Crosshairs widget"""
        page = Crosshairs(self)
        return page


    def show_settings(self):
        """Create and return the Crosshair Settings widget"""
        page = Crosshair_settings(self)
        return page

    def show_misc(self):
        """Create and return the Misc widget"""
        page = Misc()
        return page

class StyledPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))  # or any shade of grey you want
        pixmap = QPixmap("Assets/Background.png")
        painter.drawPixmap(self.rect(), pixmap)

    def button_style(self):
        return """
        QPushButton {
            background-color: rgba(0, 0, 0, 100);
            color: white;
            border: 2px solid white;
            border-radius: 5px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.5);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 0.4);
        }
        """
    
    def slider_style(self):
        return """
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #2e2e2e;
                margin: 2px 0;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: #00bfff;
                border: 1px solid #1e1e1e;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSlider::sub-page:horizontal {
                background: #00bfff;
                border: 1px solid #1e1e1e;
                height: 8px;
                border-radius: 4px;
            }

            QSlider::add-page:horizontal {
                background: #555;
                border: 1px solid #1e1e1e;
                height: 8px;
                border-radius: 4px;
            }
        """

class Crosshairs(StyledPage):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        layout = QVBoxLayout()

        # Create and style the front label
        Front_label = QLabel("Crosshairs")
        Front_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        Front_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(Front_label)

        # Create a layout for the crosshair icon buttons (buttons will be arranged in a grid)
        icon_layout = QGridLayout()

        # Crosshair types and their icon paths
        self.crosshair_icons = [
            ("Type 1", "Assets/crosshair_pack/blue_default_dot.png", self.select_crosshair),
            ("Type 2", "Assets/crosshair_pack/blue_default.png", self.select_crosshair),
            ("Type 3", "Assets/crosshair_pack/blue_dot.png", self.select_crosshair),
            ("Type 4", "Assets/crosshair_pack/blue_ring.png", self.select_crosshair),
            ("Type 5", "Assets/crosshair_pack/green_default_dot.png", self.select_crosshair),
            ("Type 6", "Assets/crosshair_pack/green_default.png", self.select_crosshair),
            ("Type 7", "Assets/crosshair_pack/green_dot.png", self.select_crosshair),
            ("Type 8", "Assets/crosshair_pack/green_ring.png", self.select_crosshair),
            ("Type 9", "Assets/crosshair_pack/lightblue_default_dot.png", self.select_crosshair),
            ("Type 10", "Assets/crosshair_pack/lightblue_default.png", self.select_crosshair),
            ("Type 11", "Assets/crosshair_pack/lightblue_dot.png", self.select_crosshair),
            ("Type 12", "Assets/crosshair_pack/lightblue_ring.png", self.select_crosshair),
            ("Type 13", "Assets/crosshair_pack/pink_dot.png", self.select_crosshair),
            ("Type 14", "Assets/crosshair_pack/pink_ring.png", self.select_crosshair),
            ("Type 15", "Assets/crosshair_pack/red_default_dot.png", self.select_crosshair),
            ("Type 16", "Assets/crosshair_pack/red_default.png", self.select_crosshair),
            ("Type 17", "Assets/crosshair_pack/red_defaultlarge_dot.png", self.select_crosshair),
            ("Type 18", "Assets/crosshair_pack/red_dot.png", self.select_crosshair),
            ("Type 19", "Assets/crosshair_pack/red_ring.png", self.select_crosshair),
            ("Type 20", "Assets/crosshair_pack/white_default_dot.png", self.select_crosshair),
            ("Type 21", "Assets/crosshair_pack/white_default.png", self.select_crosshair),
            ("Type 22", "Assets/crosshair_pack/white.png", self.select_crosshair),
            ("Type 23", "Assets/crosshair_pack/yellow_dot.png", self.select_crosshair),
            ("Type 24", "Assets/crosshair_pack/yellow_ring.png", self.select_crosshair),
        ]

        # Add icon buttons to the grid layout
        row = 0
        col = 0
        for label, icon_path, _ in self.crosshair_icons:
            btn = QPushButton()
            btn.setStyleSheet(self.button_style())
            icon = QIcon(icon_path)
            btn.setIcon(icon)
            btn.setIconSize(QSize(80, 80))
            btn.setFixedSize(60, 60)
            btn.clicked.connect(lambda checked, path=icon_path: self.select_crosshair(path))  # ✅ FIX
            icon_layout.addWidget(btn, row, col)


            # Move to next column, if the row is full, move to the next row
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Wrap the grid layout inside a scroll area for scrolling functionality
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.create_scroll_area_content(icon_layout))

        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def create_scroll_area_content(self, icon_layout):
        widget = QWidget()
        widget.setLayout(icon_layout)
        return widget

    def select_crosshair(self, path):
        self.show_crosshair_overlay(path)


    def show_crosshair_overlay(self, crosshair_path):
        if self.parent_window.current_overlay:
            self.parent_window.current_overlay.close()

        overlay = CrosshairOverlay()
        overlay.set_crosshair(crosshair_path)

        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - overlay.width()) // 2
        y = (screen_geometry.height() - overlay.height()) // 2
        overlay.move(x, y)
        overlay.show()

        self.parent_window.current_overlay = overlay  # Save reference



    def reset_cursor(self):
        QApplication.restoreOverrideCursor()

class Crosshair_settings(StyledPage):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Front Label
        Front_Label = QLabel("Crosshair Settings")
        Front_Label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        Front_Label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(Front_Label)

        # Container for Size Slider and Label (Centered)
        size_slider_container = QVBoxLayout()
        size_slider_container.setAlignment(Qt.AlignHCenter)

        # Size Label
        self.VLabel = QLabel("Size: 50")
        self.VLabel.setStyleSheet("font-size: 16px; color: white;")
        self.VLabel.setAlignment(Qt.AlignCenter)  # Align label to center
        size_slider_container.addWidget(self.VLabel)

        # Size Slider
        self.VSlider = QSlider(Qt.Horizontal)
        self.VSlider.setMinimum(0)
        self.VSlider.setMaximum(100)
        self.VSlider.setValue(50)  # Default size
        self.VSlider.setFixedWidth(300)
        self.VSlider.setStyleSheet(self.slider_style())
        self.VSlider.valueChanged.connect(self.update_size)
        size_slider_container.addWidget(self.VSlider)

        layout.addLayout(size_slider_container)

        # Container for X Position Slider and Label (Centered)
        x_slider_container = QVBoxLayout()
        x_slider_container.setAlignment(Qt.AlignHCenter)

        # X Position Label
        self.XLabel = QLabel("X Position: 50")
        self.XLabel.setStyleSheet("font-size: 16px; color: white;")
        self.XLabel.setAlignment(Qt.AlignCenter)
        x_slider_container.addWidget(self.XLabel)

        # X Position Slider
        self.XSlider = QSlider(Qt.Horizontal)
        self.XSlider.setMinimum(0)
        self.XSlider.setMaximum(100)
        self.XSlider.setValue(50)  # Default position
        self.XSlider.setFixedWidth(300)
        self.XSlider.setStyleSheet(self.slider_style())
        self.XSlider.valueChanged.connect(self.update_x_position)
        x_slider_container.addWidget(self.XSlider)

        layout.addLayout(x_slider_container)

        # Container for Y Position Slider and Label (Centered)
        y_slider_container = QVBoxLayout()
        y_slider_container.setAlignment(Qt.AlignHCenter)

        # Y Position Label
        self.YLabel = QLabel("Y Position: 50")
        self.YLabel.setStyleSheet("font-size: 16px; color: white;")
        self.YLabel.setAlignment(Qt.AlignCenter)
        y_slider_container.addWidget(self.YLabel)

        # Y Position Slider
        self.YSlider = QSlider(Qt.Horizontal)
        self.YSlider.setMinimum(0)
        self.YSlider.setMaximum(100)
        self.YSlider.setValue(50)  # Default position
        self.YSlider.setFixedWidth(300)
        self.YSlider.setStyleSheet(self.slider_style())
        self.YSlider.valueChanged.connect(self.update_y_position)
        y_slider_container.addWidget(self.YSlider)

        layout.addLayout(y_slider_container)

        self.setLayout(layout)

        # Placeholder crosshair object (to simulate)
        self.current_overlay = CrosshairOverlay()  # You need to implement this class
        self.current_overlay.show()  # Make sure the overlay is visible

    def slider_style(self):
        return "QSlider::handle:horizontal { background: #1e1e1e; border-radius: 5px; height: 15px; width: 15px; margin: -5px 0; }"

    def update_size(self, value):
        self.VLabel.setText(f"Size: {value}")
        if self.parent_window.current_overlay:
            overlay = self.parent_window.current_overlay

            # Ensure we're resizing based on the original pixmap to avoid distortion
            if not hasattr(overlay, 'original_pixmap') or overlay.original_pixmap is None:
                overlay.original_pixmap = overlay.crosshair_pixmap

            new_pixmap = overlay.original_pixmap.scaled(
                value, value,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            overlay.crosshair_pixmap = new_pixmap
            overlay.crosshair_label.setPixmap(new_pixmap)
            overlay.crosshair_label.setFixedSize(new_pixmap.size())
            overlay.setFixedSize(new_pixmap.size())

            # Now, forcefully move the crosshair back to the defined x and y values
            defined_x = self.XSlider.value()
            defined_y = self.YSlider.value()
            screen = QApplication.primaryScreen().geometry()
            
            new_x = int((screen.width() - overlay.width()) * (defined_x / 100.0))
            new_y = int((screen.height() - overlay.height()) * (defined_y / 100.0))
            
            overlay.move(new_x, new_y)

    def update_x_position(self, value):
        self.XLabel.setText(f"X Position: {value}")
        if self.parent_window.current_overlay:
            screen = QApplication.primaryScreen().geometry()
            x = int((screen.width() - self.parent_window.current_overlay.width()) * (value / 100.0))
            y = self.parent_window.current_overlay.y()
            self.parent_window.current_overlay.move(x, y)

    def update_y_position(self, value):
        self.YLabel.setText(f"Y Position: {value}")
        if self.parent_window.current_overlay:
            screen = QApplication.primaryScreen().geometry()
            y = int((screen.height() - self.parent_window.current_overlay.height()) * (value / 100.0))
            x = self.parent_window.current_overlay.x()
            self.parent_window.current_overlay.move(x, y)

    def slider_style(self):
        return """
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #2e2e2e;
                margin: 2px 0;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: #00bfff;
                border: 1px solid #1e1e1e;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSlider::sub-page:horizontal {
                background: #00bfff;
                border: 1px solid #1e1e1e;
                height: 8px;
                border-radius: 4px;
            }

            QSlider::add-page:horizontal {
                background: #555;
                border: 1px solid #1e1e1e;
                height: 8px;
                border-radius: 4px;
            }
        """

class Misc(StyledPage):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Front Label
        Front_Label = QLabel("Misc")
        Front_Label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        Front_Label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(Front_Label)

        # Spacer to position buttons right below the label
        spacer = QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addItem(spacer)

        # Discord Button
        self.discord_btn = QPushButton("", self)  # Empty text since we're using an icon
        self.discord_btn.setIcon(QIcon("Assets\\images.png"))  # Ensure the image is in the same directory
        self.discord_btn.setStyleSheet(self.button_style())
        self.discord_btn.setIconSize(self.discord_btn.sizeHint())  # Adjust size
        self.discord_btn.setMaximumWidth(65)  # Set max width for the button
        layout.addWidget(self.discord_btn, alignment=Qt.AlignHCenter)

        # GitHub Button
        self.github_btn = QPushButton("", self)  # Empty text since we're using an icon
        self.github_btn.setIcon(QIcon("Assets\\github.png"))  # Ensure the image is in the same directory
        self.github_btn.setStyleSheet(self.button_style())
        self.github_btn.setIconSize(self.github_btn.sizeHint())
        self.github_btn.setMaximumWidth(65)
        self.github_btn.setMaximumHeight(65)  # Set max height for the button
        layout.addWidget(self.github_btn, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

if __name__ == "__main__":
    main()
    app = QApplication(sys.argv)
    window = StyledWindow()
    window.show()
    sys.exit(app.exec_())