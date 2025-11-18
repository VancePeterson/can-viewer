"""DBC file loader and parser."""

import cantools
from pathlib import Path
from typing import Optional


class DBCLoader:
    """Loads and manages DBC files for CAN message definitions."""

    def __init__(self):
        self.db: Optional[cantools.database.Database] = None
        self.file_path: Optional[Path] = None

    def load_file(self, file_path: str) -> bool:
        """Load a DBC file.

        Args:
            file_path: Path to the DBC file

        Returns:
            True if successful, False otherwise
        """
        try:
            self.file_path = Path(file_path)
            self.db = cantools.database.load_file(str(self.file_path), strict=False)
            return True
        except Exception as e:
            print(f"Error loading DBC file: {e}")
            return False

    def get_messages(self) -> list:
        """Get all messages (PGNs) from the loaded DBC file.

        Returns:
            List of message objects from the DBC file
        """
        if self.db is None:
            return []
        return self.db.messages

    def get_message_by_id(self, message_id: int):
        """Get a specific message by its CAN ID.

        Args:
            message_id: The CAN message ID

        Returns:
            Message object or None if not found
        """
        if self.db is None:
            return None
        try:
            return self.db.get_message_by_frame_id(message_id)
        except KeyError:
            return None

    def decode_message(self, message_id: int, data: bytes) -> Optional[dict]:
        """Decode a CAN message using the DBC definition.

        Args:
            message_id: The CAN message ID
            data: Raw CAN data bytes

        Returns:
            Dictionary of decoded signal values or None if decoding fails
        """
        if self.db is None:
            return None
        try:
            message = self.db.get_message_by_frame_id(message_id)
            return message.decode(data)
        except (KeyError, Exception) as e:
            print(f"Error decoding message 0x{message_id:X}: {e}")
            return None
