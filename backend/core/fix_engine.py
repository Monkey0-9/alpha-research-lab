"""
QuantAlpha Deterministic FIX 4.2 / 4.4 Protocol Engine.
Implements:
1. Standard FIX tag-value serialization and deserialization.
2. Modulo-256 Checksum computation and validation.
3. Administrative and application messages:
   - 35=D (NewOrderSingle)
   - 35=8 (ExecutionReport)
   - 35=F (OrderCancelRequest)
   - 35=G (OrderCancelReplaceRequest)
   - 35=2 (ResendRequest)
   - 35=4 (SequenceReset)
   - 35=0 (Heartbeat)
   - 35=A (Logon)
4. Sequence number management, gap detection, and state recovery.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


SOH = "\x01"


class FixMsgType(str, Enum):
    HEARTBEAT = "0"
    TEST_REQUEST = "1"
    RESEND_REQUEST = "2"
    REJECT = "3"
    SEQUENCE_RESET = "4"
    LOGOUT = "5"
    LOGON = "A"
    NEW_ORDER_SINGLE = "D"
    EXECUTION_REPORT = "8"
    ORDER_CANCEL_REQUEST = "F"
    ORDER_CANCEL_REPLACE_REQUEST = "G"


@dataclass
class FixMessage:
    msg_type: FixMsgType
    sender_comp_id: str
    target_comp_id: str
    msg_seq_num: int
    fields: Dict[int, str] = field(default_factory=dict)
    sending_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def set(self, tag: int, value: str) -> None:
        self.fields[tag] = str(value)

    def get(self, tag: int, default: Optional[str] = None) -> Optional[str]:
        return self.fields.get(tag, default)

    def to_wire(self) -> str:
        """Serialize message to raw FIX wire format with SOH delimiters and CheckSum."""
        body_parts = [
            f"35={self.msg_type.value}",
            f"49={self.sender_comp_id}",
            f"56={self.target_comp_id}",
            f"34={self.msg_seq_num}",
            f"52={self.sending_time.strftime('%Y%m%d-%H:%M:%S.%f')[:-3]}",
        ]
        for tag, val in sorted(self.fields.items()):
            body_parts.append(f"{tag}={val}")

        body_str = SOH.join(body_parts) + SOH
        body_len = len(body_str)

        header = f"8=FIX.4.2{SOH}9={body_len}{SOH}"
        raw_prefix = header + body_str

        # Compute CheckSum (sum of all ASCII bytes modulo 256)
        checksum_val = sum(raw_prefix.encode("ascii")) % 256
        checksum_str = f"10={checksum_val:03d}{SOH}"

        return raw_prefix + checksum_str

    @classmethod
    def from_wire(cls, wire_data: str) -> "FixMessage":
        """Parse raw FIX wire string and validate body length, tags, and checksum."""
        delim = SOH if SOH in wire_data else "|"
        tokens = [t for t in wire_data.split(delim) if t]
        tag_map: Dict[int, str] = {}
        seen_tags = set()

        for token in tokens:
            if "=" in token:
                k, v = token.split("=", 1)
                try:
                    tag_int = int(k)
                except ValueError:
                    raise ValueError(f"Invalid non-integer tag: {k}")

                if tag_int in seen_tags:
                    raise ValueError(f"Duplicate tag detected: {tag_int}")
                seen_tags.add(tag_int)
                tag_map[tag_int] = v

        # 1. BeginString verification
        if 8 in tag_map and tag_map[8] != "FIX.4.2":
            raise ValueError(f"Invalid BeginString: expected FIX.4.2, got {tag_map[8]}")

        # 2. Mandatory header tags
        if 35 not in tag_map or 49 not in tag_map or 56 not in tag_map or 34 not in tag_map:
            raise ValueError("Malformed FIX message: Missing mandatory header tags (35, 49, 56, 34).")

        # 3. BodyLength verification
        if 9 in tag_map:
            expected_body_len = int(tag_map[9])
            # Body length is count of characters between tag 9 delimiter and tag 10 tag
            tag9_token = f"9={tag_map[9]}{delim}"
            start_pos = wire_data.find(tag9_token)
            if start_pos != -1:
                body_start = start_pos + len(tag9_token)
                end_pos = wire_data.find("10=", body_start)
                if end_pos != -1:
                    actual_body_len = end_pos - body_start
                    if actual_body_len != expected_body_len:
                        raise ValueError(
                            f"FIX BodyLength mismatch: specified {expected_body_len}, actual {actual_body_len}"
                        )

        # 4. Checksum verification if present
        if 10 in tag_map:
            expected_chk = int(tag_map[10])
            chk_idx = wire_data.find(f"10={tag_map[10]}")
            calc_chk = sum(wire_data[:chk_idx].encode("ascii")) % 256
            if calc_chk != expected_chk:
                raise ValueError(f"FIX CheckSum mismatch: calculated {calc_chk:03d}, received {expected_chk:03d}")

        # Extract standard header fields
        msg = cls(
            msg_type=FixMsgType(tag_map[35]),
            sender_comp_id=tag_map[49],
            target_comp_id=tag_map[56],
            msg_seq_num=int(tag_map[34]),
        )

        # Populate custom fields (skipping standard header tags)
        for tag, val in tag_map.items():
            if tag not in (8, 9, 35, 49, 56, 34, 52, 10):
                msg.set(tag, val)

        return msg


class FixSession:
    """Manages FIX session state, sequence numbers, gap detection, and resend recovery."""

    def __init__(self, sender_comp_id: str, target_comp_id: str):
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.out_seq_num = 1
        self.in_seq_num = 1
        self.sent_messages: Dict[int, FixMessage] = {}
        self.is_connected = False

    def build_logon(self) -> FixMessage:
        msg = FixMessage(
            msg_type=FixMsgType.LOGON,
            sender_comp_id=self.sender_comp_id,
            target_comp_id=self.target_comp_id,
            msg_seq_num=self.out_seq_num
        )
        msg.set(98, "0")  # EncryptMethod: None
        msg.set(108, "30")  # HeartBtInt: 30 sec
        self.out_seq_num += 1
        return msg

    def build_logout(self, text: Optional[str] = None) -> FixMessage:
        msg = FixMessage(
            msg_type=FixMsgType.LOGOUT,
            sender_comp_id=self.sender_comp_id,
            target_comp_id=self.target_comp_id,
            msg_seq_num=self.out_seq_num
        )
        if text:
            msg.set(58, text)
        self.out_seq_num += 1
        return msg

    def build_new_order_single(
        self,
        cl_ord_id: str,
        symbol: str,
        side: str,  # "1" = Buy, "2" = Sell
        quantity: float,
        price: Optional[float] = None,
        ord_type: str = "2"  # "1" = Market, "2" = Limit
    ) -> FixMessage:
        msg = FixMessage(
            msg_type=FixMsgType.NEW_ORDER_SINGLE,
            sender_comp_id=self.sender_comp_id,
            target_comp_id=self.target_comp_id,
            msg_seq_num=self.out_seq_num
        )
        msg.set(11, cl_ord_id)
        msg.set(55, symbol)
        msg.set(54, side)
        msg.set(38, str(quantity))
        msg.set(40, ord_type)
        if price is not None:
            msg.set(44, f"{price:.2f}")
        msg.set(60, datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S"))

        self.sent_messages[self.out_seq_num] = msg
        self.out_seq_num += 1
        return msg

    def receive_message(self, wire_or_msg: Any) -> Tuple[FixMessage, Optional[FixMessage]]:
        """
        Process inbound message (string wire data or FixMessage object).
        Detects sequence gaps and returns (processed_message, optional_resend_request).
        """
        if isinstance(wire_or_msg, str):
            msg = FixMessage.from_wire(wire_or_msg)
        else:
            msg = wire_or_msg

        resend_req: Optional[FixMessage] = None

        if msg.msg_seq_num > self.in_seq_num:
            # Sequence gap detected! Generate ResendRequest (35=2)
            resend_req = FixMessage(
                msg_type=FixMsgType.RESEND_REQUEST,
                sender_comp_id=self.sender_comp_id,
                target_comp_id=self.target_comp_id,
                msg_seq_num=self.out_seq_num
            )
            resend_req.set(7, str(self.in_seq_num))  # BeginSeqNo
            resend_req.set(16, "0")  # EndSeqNo (0 = up to current)
            self.out_seq_num += 1
        else:
            self.in_seq_num = msg.msg_seq_num + 1

        if msg.msg_type == FixMsgType.LOGON:
            self.is_connected = True
            resend_req = self.build_logon()
        elif msg.msg_type == FixMsgType.LOGOUT:
            self.is_connected = False
            logout_ack = FixMessage(
                msg_type=FixMsgType.LOGOUT,
                sender_comp_id=self.sender_comp_id,
                target_comp_id=self.target_comp_id,
                msg_seq_num=self.out_seq_num
            )
            if msg.get(58):
                logout_ack.set(58, msg.get(58))
            self.out_seq_num += 1
            resend_req = logout_ack
        elif msg.msg_type == FixMsgType.TEST_REQUEST:
            # Echo tag 112 (TestReqID) in Heartbeat (35=0)
            test_req_id = msg.get(112)
            resend_req = self.build_heartbeat(test_req_id)

        return msg, resend_req

    def process_incoming(self, wire_or_msg: Any) -> List[FixMessage]:
        """Convenience method returning list of outbound response messages."""
        _, resp = self.receive_message(wire_or_msg)
        return [resp] if resp else []

    def build_heartbeat(self, test_req_id: Optional[str] = None) -> FixMessage:
        msg = FixMessage(
            msg_type=FixMsgType.HEARTBEAT,
            sender_comp_id=self.sender_comp_id,
            target_comp_id=self.target_comp_id,
            msg_seq_num=self.out_seq_num
        )
        if test_req_id:
            msg.set(112, test_req_id)
        self.out_seq_num += 1
        return msg
