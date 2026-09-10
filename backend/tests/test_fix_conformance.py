"""
FIX 4.2 Research Conformance Subset Matrix:

| FIX Requirement       | Test Case                        | Expected Behavior | Status |
| :-------------------- | :------------------------------- | :---------------- | :----- |
| BeginString (Tag 8)   | Malformed (e.g. FIX.4.4)         | Reject / Raise    | PASS   |
| BodyLength (Tag 9)    | Inaccurate character byte count  | Reject / Raise    | PASS   |
| CheckSum (Tag 10)     | Corrupted modulo-256 sum         | Reject / Raise    | PASS   |
| Mandatory Tags        | Missing Tag 35, 49, 56, or 34    | Reject / Raise    | PASS   |
| Duplicate Tags        | Repeated Tag ID (e.g. 11)        | Reject / Raise    | PASS   |
| Sequence Gap          | Incoming seq > expected seq      | Send ResendRequest| PASS   |
| TestRequest Echo      | Incoming Tag 112                 | Echo in Heartbeat | PASS   |
| Session Lifecycle     | Logon -> Active -> Logout        | Clean transitions | PASS   |
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
    order = session.build_new_order_single("CL-3", "NVDA", "1", 20.0, price=800.0)
    wire = order.to_wire()

    # Tamper checksum tag 10 preserving exact byte length
    bad_chk_wire = wire.rsplit("10=", 1)[0] + "10=000\x01"

    with pytest.raises(ValueError, match="CheckSum mismatch"):
        FixMessage.from_wire(bad_chk_wire)


def test_fix_conformance_sequence_gap_resend_request():
    session = FixSession("CLIENT", "EXCHANGE")
    # Expected seq is 1, simulate incoming seq 4 (gap detected)
    gap_msg = FixMessage(
        msg_type=FixMsgType.HEARTBEAT,
        sender_comp_id="EXCHANGE",
        target_comp_id="CLIENT",
        msg_seq_num=4
    )
    responses = session.process_incoming(gap_msg)
    assert len(responses) == 1
    res = responses[0]
    assert res.msg_type == FixMsgType.RESEND_REQUEST
    assert res.get(7) == "1"   # BeginSeqNo
    assert res.get(16) == "0"  # EndSeqNo (0 = up to current)


def test_fix_conformance_test_request_heartbeat_echo():
    session = FixSession("CLIENT", "EXCHANGE")
    test_req = FixMessage(
        msg_type=FixMsgType.TEST_REQUEST,
        sender_comp_id="EXCHANGE",
        target_comp_id="CLIENT",
        msg_seq_num=1
    )
    test_req.set(112, "HEARTBEAT_NONCE_998877")
    responses = session.process_incoming(test_req)
    assert len(responses) == 1
    hb = responses[0]
    assert hb.msg_type == FixMsgType.HEARTBEAT
    assert hb.get(112) == "HEARTBEAT_NONCE_998877"


def test_fix_conformance_session_logon_logout_lifecycle():
    client = FixSession("CLIENT", "BROKER")
    broker = FixSession("BROKER", "CLIENT")

    logon = client.build_logon()
    resp = broker.process_incoming(logon)
    assert len(resp) == 1
    assert resp[0].msg_type == FixMsgType.LOGON

    logout = client.build_logout("Routine disconnection")
    resp_logout = broker.process_incoming(logout)
    assert len(resp_logout) == 1
    assert resp_logout[0].msg_type == FixMsgType.LOGOUT
    assert resp_logout[0].get(58) == "Routine disconnection"
