"""PCAN USB CAN interface handler."""

import can
from typing import Optional, Callable
from threading import Thread, Event


class PCANInterface:
    """Manages PCAN USB CAN adapter communication."""

    def __init__(self):
        self.bus: Optional[can.Bus] = None
        self.is_connected = False
        self.receive_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.message_callback: Optional[Callable] = None

    def connect(self, channel: str = "PCAN_USBBUS1", bitrate: int = 250000) -> bool:
        """Connect to PCAN USB adapter.

        Args:
            channel: PCAN channel identifier (e.g., 'PCAN_USBBUS1')
            bitrate: CAN bus bitrate in bits/second

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.bus = can.Bus(
                interface="pcan",
                channel=channel,
                bitrate=bitrate
            )
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Error connecting to PCAN: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from PCAN adapter and stop receiving."""
        self.stop_receiving()
        if self.bus:
            self.bus.shutdown()
            self.bus = None
        self.is_connected = False

    def start_receiving(self, callback: Callable[[int, bytes], None]):
        """Start receiving CAN messages in a background thread.

        Args:
            callback: Function to call with (message_id, data) for each received message
        """
        if not self.is_connected or self.receive_thread is not None:
            return

        self.message_callback = callback
        self.stop_event.clear()
        self.receive_thread = Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def stop_receiving(self):
        """Stop receiving CAN messages."""
        if self.receive_thread:
            self.stop_event.set()
            self.receive_thread.join(timeout=2.0)
            self.receive_thread = None

    def _receive_loop(self):
        """Internal loop for receiving CAN messages."""
        while not self.stop_event.is_set() and self.bus:
            try:
                message = self.bus.recv(timeout=0.1)
                if message and self.message_callback:
                    # Convert bytearray to bytes if necessary
                    data = bytes(message.data) if isinstance(message.data, bytearray) else message.data
                    self.message_callback(message.arbitration_id, data)
            except Exception as e:
                print(f"Error receiving CAN message: {e}")

    def send_message(self, message_id: int, data: bytes) -> bool:
        """Send a CAN message.

        Args:
            message_id: CAN message ID
            data: Data bytes to send

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.bus:
            return False

        try:
            message = can.Message(
                arbitration_id=message_id,
                data=data,
                is_extended_id=message_id > 0x7FF
            )
            self.bus.send(message)
            return True
        except Exception as e:
            print(f"Error sending CAN message: {e}")
            return False
