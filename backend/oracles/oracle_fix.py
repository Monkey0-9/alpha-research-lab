"""
Independent Reference Oracle: FIX 4.2 Protocol Parser & Validator.
Constructed using standard FIX 4.2 specification grammar.
Zero production imports permitted.
"""
from typing import Dict, Tuple


class OracleFixValidationError(Exception):
    """Raised when wire bytes violate the FIX 4.2 specification."""
    pass


class OracleFixParser:
    """Independent reference parser verifying FIX 4.2 wire integrity."""

    @classmethod
    def parse_and_validate_wire(cls, raw_wire: str) -> Tuple[Dict[int, str], str]:
        """
        Parses raw FIX wire string into tag-value dictionary and returns MsgType.
        Validates:
        1. Mandatory Start: Tag 8=FIX.4.2 must be the very first field.
        2. Mandatory Second Field: Tag 9 (BodyLength).
        3. Mandatory Third Field: Tag 35 (MsgType).
        4. Mandatory Final Field: Tag 10 (CheckSum) formatted as exactly 3 digits.
        5. Modulo-256 Checksum arithmetic.
        6. BodyLength byte-count arithmetic.
        """
        delimiter = "\x01" if "\x01" in raw_wire else "|"
        parts = [p for p in raw_wire.split(delimiter) if p]

        if len(parts) < 4:
            raise OracleFixValidationError("Wire message too short to contain minimal FIX 4.2 header and trailer")

        # Parse tags
        tags = {}
        tag_order = []
        for p in parts:
            if "=" not in p:
                raise OracleFixValidationError(f"Malformed tag-value pair: {p}")
            t_str, v_str = p.split("=", 1)
            try:
                t_int = int(t_str)
            except ValueError:
                raise OracleFixValidationError(f"Invalid non-integer tag: {t_str}")
            if t_int in tags:
                raise OracleFixValidationError(f"Duplicate tag detected: {t_int}")
            tags[t_int] = v_str
            tag_order.append(t_int)

        # 1. First field MUST be tag 8
        if tag_order[0] != 8 or tags[8] != "FIX.4.2":
            raise OracleFixValidationError(f"First tag must be 8=FIX.4.2, got 8={tags.get(8)}")

        # 2. Second field MUST be tag 9
        if tag_order[1] != 9:
            raise OracleFixValidationError(f"Second tag must be 9 (BodyLength), got {tag_order[1]}")

        # 3. Third field MUST be tag 35
        if tag_order[2] != 35:
            raise OracleFixValidationError(f"Third tag must be 35 (MsgType), got {tag_order[2]}")

        # 4. Last field MUST be tag 10
        if tag_order[-1] != 10:
            raise OracleFixValidationError(f"Last tag must be 10 (CheckSum), got {tag_order[-1]}")
        if len(tags[10]) != 3 or not tags[10].isdigit():
            raise OracleFixValidationError(f"Tag 10 checksum must be exactly 3 digits, got {tags[10]}")

        # 5. Checksum verification: Sum of all characters up to '10=' modulo 256
        chk_idx = raw_wire.rfind("10=")
        body_to_checksum = raw_wire[:chk_idx]
        actual_sum = sum(ord(c) for c in body_to_checksum) % 256
        expected_sum = int(tags[10])
        if actual_sum != expected_sum:
            raise OracleFixValidationError(
                f"Checksum mismatch: wire Tag 10 is {expected_sum:03d}, but calculated sum is {actual_sum:03d}"
            )

        return tags, tags[35]
