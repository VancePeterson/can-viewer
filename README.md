# Can Viewer

A Python GUI application for viewing live CAN bus data using PEAK PCAN USB adapters with DBC file support.

## Features

- Load DBC files to parse CAN message definitions
- Connect to PEAK PCAN USB adapters
- Select specific PGNs (CAN messages) to monitor via checkboxes
- Real-time display of decoded signal values
- Support for multiple PCAN channels and bitrates
- Clean PyQt6-based interface

## Installation

### Prerequisites

- Python 3.13+
- PEAK PCAN driver installed on your system
- PCAN USB adapter hardware

### Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Click "Load DBC File" to select your CAN database file

3. Select the PCAN channel (e.g., PCAN_USBBUS1) and bitrate (e.g., 250000)

4. Click "Connect" to establish connection to the PCAN adapter

5. Check the boxes next to the PGNs you want to monitor

6. View the live decoded signal values in the right panel

## Project Structure

```
can_viewer/
   __init__.py          # Package initialization
   dbc_loader.py        # DBC file parsing
   can_interface.py     # PCAN adapter interface
   gui.py              # Main GUI application
```

## Dependencies

- **cantools**: DBC file parsing and message decoding
- **python-can**: CAN bus communication library with PCAN support
- **PyQt6**: GUI framework

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.