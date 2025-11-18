"""Main GUI application for PCAN Cellular viewer."""

import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem,
    QTextEdit, QSplitter, QGroupBox, QComboBox, QSpinBox, QCheckBox,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from pathlib import Path
from typing import Dict, Set, Optional

from .dbc_loader import DBCLoader
from .can_interface import PCANInterface


class CANSignalEmitter(QObject):
    """Qt signal emitter for CAN messages (thread-safe communication)."""
    message_received = pyqtSignal(int, bytes)


class MessageMetadata:
    """Store metadata about received CAN messages."""
    def __init__(self):
        self.last_timestamp: float = 0
        self.count: int = 0
        self.decoded_data: Optional[dict] = None


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.dbc_loader = DBCLoader()
        self.can_interface = PCANInterface()
        self.signal_emitter = CANSignalEmitter()
        self.selected_message_ids: Set[int] = set()
        self.message_metadata: Dict[int, MessageMetadata] = {}  # Store message data with metadata
        self.all_messages = []  # Store all messages for filtering

        self.init_ui()
        self.setup_connections()

        # Update timer for GUI refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_live_data_display)
        self.update_timer.setInterval(100)  # Update every 100ms

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("CAN Viewer")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # Splitter for message list and data display
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Message/PGN list with checkboxes
        message_list_group = self.create_message_list_panel()
        splitter.addWidget(message_list_group)

        # Right: Live data display
        data_display_group = self.create_data_display_panel()
        splitter.addWidget(data_display_group)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage("Ready - Load a DBC file to begin")

    def create_control_panel(self) -> QGroupBox:
        """Create the top control panel."""
        group = QGroupBox("Configuration")
        layout = QHBoxLayout()

        # DBC file selection
        self.dbc_label = QLabel("No DBC file loaded")
        self.dbc_button = QPushButton("Load DBC File")
        self.dbc_button.clicked.connect(self.load_dbc_file)

        layout.addWidget(QLabel("DBC File:"))
        layout.addWidget(self.dbc_label)
        layout.addWidget(self.dbc_button)

        # PCAN channel selection
        layout.addWidget(QLabel("PCAN Channel:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems([
            "PCAN_USBBUS1", "PCAN_USBBUS2", "PCAN_USBBUS3", "PCAN_USBBUS4",
            "PCAN_USBBUS5", "PCAN_USBBUS6", "PCAN_USBBUS7", "PCAN_USBBUS8"
        ])
        layout.addWidget(self.channel_combo)

        # Bitrate selection
        layout.addWidget(QLabel("Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems([
            "125000", "250000", "500000", "1000000"
        ])
        self.bitrate_combo.setCurrentText("250000")
        layout.addWidget(self.bitrate_combo)

        # Connect/Disconnect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setEnabled(False)
        layout.addWidget(self.connect_button)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_message_list_panel(self) -> QGroupBox:
        """Create the message list panel with checkboxes."""
        group = QGroupBox("Available Messages (PGNs)")
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter messages by ID or name...")
        self.search_box.textChanged.connect(self.filter_messages)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        self.message_list = QListWidget()
        self.message_list.itemChanged.connect(self.on_message_selection_changed)
        layout.addWidget(self.message_list)

        # Select all/none buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_messages)
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_messages)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(select_none_btn)
        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def create_data_display_panel(self) -> QGroupBox:
        """Create the live data display panel."""
        group = QGroupBox("Live Data")
        layout = QVBoxLayout()

        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setFontFamily("Courier New")
        layout.addWidget(self.data_display)

        # Clear button
        clear_btn = QPushButton("Clear Display")
        clear_btn.clicked.connect(self.data_display.clear)
        layout.addWidget(clear_btn)

        group.setLayout(layout)
        return group

    def setup_connections(self):
        """Setup signal/slot connections."""
        self.signal_emitter.message_received.connect(self.on_can_message_received)

    def load_dbc_file(self):
        """Open file dialog and load DBC file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DBC File",
            "",
            "DBC Files (*.dbc);;All Files (*)"
        )

        if file_path:
            if self.dbc_loader.load_file(file_path):
                self.dbc_label.setText(Path(file_path).name)
                self.populate_message_list()
                self.connect_button.setEnabled(True)
                self.statusBar().showMessage(f"Loaded {len(self.dbc_loader.get_messages())} messages from DBC file")
            else:
                self.statusBar().showMessage("Failed to load DBC file")

    def populate_message_list(self):
        """Populate the message list with messages from DBC file."""
        self.all_messages = self.dbc_loader.get_messages()
        self.filter_messages()

    def filter_messages(self):
        """Filter the message list based on search text."""
        search_text = self.search_box.text().lower() if hasattr(self, 'search_box') else ""

        # Temporarily disconnect the itemChanged signal to avoid triggering during repopulation
        self.message_list.itemChanged.disconnect(self.on_message_selection_changed)

        self.message_list.clear()

        for msg in self.all_messages:
            # Filter by message ID (hex) or name
            msg_id_str = f"0x{msg.frame_id:X}".lower()
            msg_name = msg.name.lower()

            if search_text in msg_id_str or search_text in msg_name:
                item = QListWidgetItem(f"0x{msg.frame_id:X} - {msg.name}")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

                # Preserve checked state if this message was previously selected
                if msg.frame_id in self.selected_message_ids:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)

                item.setData(Qt.ItemDataRole.UserRole, msg.frame_id)
                self.message_list.addItem(item)

        # Reconnect the signal
        self.message_list.itemChanged.connect(self.on_message_selection_changed)

    def select_all_messages(self):
        """Select all messages in the list."""
        for i in range(self.message_list.count()):
            item = self.message_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def select_no_messages(self):
        """Deselect all messages in the list."""
        for i in range(self.message_list.count()):
            item = self.message_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def on_message_selection_changed(self, item: QListWidgetItem):
        """Handle message checkbox state changes."""
        message_id = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            self.selected_message_ids.add(message_id)
        else:
            self.selected_message_ids.discard(message_id)

    def toggle_connection(self):
        """Connect or disconnect from PCAN adapter."""
        if not self.can_interface.is_connected:
            channel = self.channel_combo.currentText()
            bitrate = int(self.bitrate_combo.currentText())

            if self.can_interface.connect(channel, bitrate):
                self.connect_button.setText("Disconnect")
                self.dbc_button.setEnabled(False)
                self.channel_combo.setEnabled(False)
                self.bitrate_combo.setEnabled(False)
                self.can_interface.start_receiving(self.can_message_callback)
                self.update_timer.start()
                self.statusBar().showMessage(f"Connected to {channel} at {bitrate} bps")
            else:
                self.statusBar().showMessage("Failed to connect to PCAN adapter")
        else:
            self.can_interface.disconnect()
            self.update_timer.stop()
            self.connect_button.setText("Connect")
            self.dbc_button.setEnabled(True)
            self.channel_combo.setEnabled(True)
            self.bitrate_combo.setEnabled(True)
            self.statusBar().showMessage("Disconnected")

    def can_message_callback(self, message_id: int, data: bytes):
        """Callback for received CAN messages (called from CAN thread)."""
        # Emit signal to handle in GUI thread
        self.signal_emitter.message_received.emit(message_id, data)

    def on_can_message_received(self, message_id: int, data: bytes):
        """Handle received CAN message in GUI thread."""
        # Only process messages that are selected
        if message_id not in self.selected_message_ids:
            return

        # Create metadata entry if it doesn't exist
        if message_id not in self.message_metadata:
            self.message_metadata[message_id] = MessageMetadata()

        # Update metadata
        metadata = self.message_metadata[message_id]
        metadata.last_timestamp = time.time()
        metadata.count += 1

        # Decode the message
        decoded = self.dbc_loader.decode_message(message_id, data)
        if decoded:
            metadata.decoded_data = decoded

    def update_live_data_display(self):
        """Update the live data display with cached message data."""
        if not self.message_metadata:
            return

        current_time = time.time()
        output_lines = []

        for message_id in sorted(self.selected_message_ids):
            if message_id in self.message_metadata:
                metadata = self.message_metadata[message_id]
                msg = self.dbc_loader.get_message_by_id(message_id)

                if msg and metadata.decoded_data:
                    # Calculate time since last message
                    time_since = current_time - metadata.last_timestamp

                    # Header with message info
                    output_lines.append(f"=== 0x{message_id:X} - {msg.name} ===")
                    output_lines.append(f"  Count: {metadata.count} | Last: {time_since:.2f}s ago")

                    # Signal values
                    for signal_name, value in metadata.decoded_data.items():
                        output_lines.append(f"  {signal_name}: {value}")
                    output_lines.append("")

        self.data_display.setPlainText("\n".join(output_lines))

    def closeEvent(self, event):
        """Handle application close."""
        if self.can_interface.is_connected:
            self.can_interface.disconnect()
        event.accept()


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
