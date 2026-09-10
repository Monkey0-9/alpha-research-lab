"""
Institutional FIX 4.2 Protocol Conformance Suite.
Verifies compliance with standard FIX 4.2 wire grammar and session protocol:
1. Malformed BeginString rejection.
2. Malformed BodyLength rejection.
3. Corrupted CheckSum fail-closed detection.
4. Duplicate tag rejection.
5. Missing mandatory header tag validation.
6. Sequence gap detection and ResendRequest (35=2) replay generation.
7. TestRequest (35=1) -> Heartbeat (35=0) echoing tag 112.
8. Session Logon / Logout lifecycle state transition.
"""
import pytest
from backend.core.fix_engine import FixMessage, FixMsgType, FixSession


def test_fix_conformance_malformed_begin_string():
    session = FixSession("CLIENT", "EXCHANGE")
    valid_order = session.build_new_order_single("CL-1", "AAPL", "1", 100.0, price=150.0)
    wire = valid_order.to_wire()

    # Tamper with BeginString
    bad_begin = wire.replace("8=FIX.4.2", "8=FIX.4.4")
    with pytest.raises(ValueError, match="Invalid BeginString"):
        FixMessage.from_wire(bad_begin)


def test_fix_conformance_malformed_body_length():
    session = FixSession("CLIENT", "EXCHANGE")
    order = session.build_new_order_single("CL-2", "MSFT", "1", 50.0, price=300.0)
    wire = order.to_wire()

    # Tamper with Tag 9 (BodyLength) by adding 10
    actual_len = int(order.to_wire().split("\x01")[1].split("=")[1])
    bad_body = wire.replace(f"9={actual_len}", f"9={actual_len + 10}")

    with pytest.raises(ValueError, match="BodyLength mismatch"):
        FixMessage.from_wire(bad_body)


def test_fix_conformance_duplicate_tags():
    # Construct wire message with duplicate Tag 11
    wire = "8=FIX.4.2|9=45|35=D|49=CLIENT|56=EXCHANGE|34=1|11=ORDER1|11=ORDER2|10=180|"
    with pytest.raises(ValueError, match="Duplicate tag detected: 11"):
        FixMessage.from_wire(wire)


def test_fix_conformance_missing_mandatory_header_tags():
    # Missing Tag 35 (MsgType)
    wire_no_35 = "8=FIX.4.2|9=30|49=CLIENT|56=EXCHANGE|34=1|10=120|"
    with pytest.raises(ValueError, match="Missing mandatory header tags"):
        FixMessage.from_wire(wire_no_35)

    # Missing Tag 34 (MsgSeqNum)
    wire_no_34 = "8=FIX.4.2|9=30|35=0|49=CLIENT|56=EXCHANGE|10=120|"
    with pytest.raises(ValueError, match="Missing mandatory header tags"):
        FixMessage.from_wire(wire_no_34)


def test_fix_conformance_checksum_corruption():
    session = FixSession("CLIENT", "EXCHANGE")
    order = session.build_new_order_single("CL-3", "NVDA", "1", 200.0, price=120.0)
    wire = order.to_wire()

    # Corrupt last 3 digits
    corrupted_wire = wire[:-4] + "000\x01"
    with pytest.raises(ValueError, match="CheckSum mismatch"):
        FixMessage.from_wire(corrupted_wire)


def test_fix_conformance_sequence_gap_and_resend_request():
    session = FixSession("CLIENT", "EXCHANGE")
    # Session expected sequence number is 1

    # Inbound message arrives with seq_num = 5 (gap of 1, 2, 3, 4)
    gap_order = FixMessage(
        msg_type=FixMsgType.EXECUTION_REPORT,
        sender_comp_id="EXCHANGE",
        target_comp_id="CLIENT",
        msg_seq_num=5
    )
    gap_order.set(11, "CL-GAP")
    gap_order.set(151, "100")
    wire = gap_order.to_wire()

    msg, resend_req = session.receive_message(wire)
    assert msg.msg_seq_num == 5
    assert resend_req is not None
    assert resend_req.msg_type == FixMsgType.RESEND_REQUEST
    # BeginSeqNo must request from expected in_seq_num 1
    assert resend_req.get(7) == "1"
    # EndSeqNo 0 indicates resend up to current
    assert resend_req.get(16) == "0"


def test_fix_conformance_test_request_echo():
    session = FixSession("CLIENT", "EXCHANGE")
    test_req = FixMessage(
        msg_type=FixMsgType.TEST_REQUEST,
        sender_comp_id="EXCHANGE",
        target_comp_id="CLIENT",
        msg_seq_num=1
    )
    test_req.set(112, "HEARTBEAT_CHALLENGE_999")
    wire = test_req.to_wire()

    msg, response = session.receive_message(wire)
    assert response is not None
    assert response.msg_type == FixMsgType.HEARTBEAT
    assert response.get(112) == "HEARTBEAT_CHALLENGE_999"


def test_fix_conformance_session_logon_and_logout_lifecycle():
    session = FixSession("CLIENT", "EXCHANGE")
    assert not session.is_connected

    # 1. Inbound Logon connects session
    logon_msg = FixMessage(FixMsgType.LOGON, "EXCHANGE", "CLIENT", 1)
    session.receive_message(logon_msg.to_wire())
    assert session.is_connected

    # 2. Inbound Logout disconnects session
    logout_msg = FixMessage(FixMsgType.LOGOUT, "EXCHANGE", "CLIENT", 2)
    session.receive_message(logout_msg.to_wire())
    assert not session.is_connected
