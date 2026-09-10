"""
Institutional Verification Tests for FIX 4.2 Engine and Microstructure Exchange Simulator.
Verifies:
1. Tag-value serialization and modulo-256 Checksum calculation.
2. Sequence number tracking and gap-fill ResendRequest generation.
3. Limit order book continuous double auction depth matching.
4. Partial fills, leaves quantity, and FIX 35=8 Execution Reports.
5. In-flight order cancellation via 35=F.
"""
import pytest
from backend.core.exchange_simulator import ExchangeSimulator
from backend.core.fix_engine import FixMessage, FixMsgType, FixSession


def test_fix_wire_serialization_and_checksum():
    msg = FixMessage(
        msg_type=FixMsgType.NEW_ORDER_SINGLE,
        sender_comp_id="QUANT_ALPHA",
        target_comp_id="CME_EXCHANGE",
        msg_seq_num=1
    )
    msg.set(11, "CL-1001")
    msg.set(55, "AAPL")
    msg.set(54, "1")  # Buy
    msg.set(38, "500")  # Qty
    msg.set(44, "150.25")  # Price

    wire = msg.to_wire()
    assert "8=FIX.4.2\x01" in wire
    assert "35=D\x01" in wire
    assert "11=CL-1001\x01" in wire
    assert "10=" in wire  # Tag 10 checksum present

    # Deserialize back from wire
    parsed = FixMessage.from_wire(wire)
    assert parsed.msg_type == FixMsgType.NEW_ORDER_SINGLE
    assert parsed.sender_comp_id == "QUANT_ALPHA"
    assert parsed.get(11) == "CL-1001"
    assert parsed.get(55) == "AAPL"
    assert parsed.get(44) == "150.25"


def test_fix_checksum_corruption_detection():
    msg = FixMessage(
        msg_type=FixMsgType.HEARTBEAT,
        sender_comp_id="NODE_A",
        target_comp_id="NODE_B",
        msg_seq_num=4
    )
    wire = msg.to_wire()

    # Corrupt body without updating checksum
    corrupted = wire.replace("NODE_A", "HACKER")
    with pytest.raises(ValueError, match="FIX CheckSum mismatch"):
        FixMessage.from_wire(corrupted)


def test_fix_session_sequence_gap_detection():
    session = FixSession(sender_comp_id="OMS_CLIENT", target_comp_id="EXCHANGE")

    # Inbound logon (seq 1)
    inbound_logon = FixMessage(
        msg_type=FixMsgType.LOGON,
        sender_comp_id="EXCHANGE",
        target_comp_id="OMS_CLIENT",
        msg_seq_num=1
    ).to_wire()

    parsed, resend = session.receive_message(inbound_logon)
    assert parsed.msg_type == FixMsgType.LOGON
    assert resend is None
    assert session.is_connected is True

    # Inbound message with sequence gap! Expected 2, but received seq 5
    gapped_msg = FixMessage(
        msg_type=FixMsgType.EXECUTION_REPORT,
        sender_comp_id="EXCHANGE",
        target_comp_id="OMS_CLIENT",
        msg_seq_num=5
    ).to_wire()

    _, resend_req = session.receive_message(gapped_msg)
    assert resend_req is not None
    assert resend_req.msg_type == FixMsgType.RESEND_REQUEST
    assert resend_req.get(7) == "2"  # BeginSeqNo = 2


def test_exchange_simulator_depth_matching():
    exchange = ExchangeSimulator()

    # Seed depth on AAPL:
    # Bids: 200 @ $149.90, 500 @ $149.80
    # Asks: 100 @ $150.10, 300 @ $150.20, 500 @ $150.30
    exchange.seed_liquidity(
        symbol="AAPL",
        bid_depth=[(149.90, 200.0), (149.80, 500.0)],
        ask_depth=[(150.10, 100.0), (150.20, 300.0), (150.30, 500.0)]
    )

    # Submit Market BUY order for 250 shares
    # Should consume all 100 @ 150.10 and 150 of 300 @ 150.20
    session = FixSession("OMS_CLIENT", "EXCHANGE_SIM")
    buy_order = session.build_new_order_single(
        cl_ord_id="CL-TEST-001",
        symbol="AAPL",
        side="1",  # Buy
        quantity=250.0,
        ord_type="1"  # Market
    )

    reports = exchange.process_new_order_single(buy_order)
    assert len(reports) == 1
    rep = reports[0]

    assert rep.msg_type == FixMsgType.EXECUTION_REPORT
    assert rep.get(39) == "2"  # Filled
    assert rep.get(14) == "250.0"  # CumQty
    assert rep.get(151) == "0.0"  # LeavesQty
    # Expected execution VWAP: (100 * 150.10 + 150 * 150.20) / 250 = (15010 + 22530) / 250 = 150.16
    assert rep.get(6) == "150.1600"


def test_exchange_limit_order_partial_fill_and_cancel():
    exchange = ExchangeSimulator()
    exchange.seed_liquidity(
        symbol="MSFT",
        bid_depth=[],
        ask_depth=[(300.00, 100.0)]
    )

    session = FixSession("OMS_CLIENT", "EXCHANGE_SIM")
    # Limit BUY 300 shares @ $300.00
    # 100 shares should fill immediately; 200 shares should rest on the bid book
    limit_order = session.build_new_order_single(
        cl_ord_id="CL-LIMIT-001",
        symbol="MSFT",
        side="1",
        quantity=300.0,
        price=300.00,
        ord_type="2"
    )

    reports = exchange.process_new_order_single(limit_order)
    rep = reports[0]
    assert rep.get(39) == "1"  # PartiallyFilled
    assert rep.get(14) == "100.0"  # CumQty
    assert rep.get(151) == "200.0"  # LeavesQty

    # Now cancel the resting 200 shares
    cancel_req = FixMessage(
        msg_type=FixMsgType.ORDER_CANCEL_REQUEST,
        sender_comp_id="OMS_CLIENT",
        target_comp_id="EXCHANGE_SIM",
        msg_seq_num=session.out_seq_num
    )
    cancel_req.set(11, "CL-CANCEL-001")
    cancel_req.set(41, "CL-LIMIT-001")  # OrigClOrdID
    cancel_req.set(55, "MSFT")

    cancel_rep = exchange.process_order_cancel_request(cancel_req)
    assert cancel_rep.get(39) == "4"  # Cancelled
    assert cancel_rep.get(151) == "0.0"  # LeavesQty
    assert cancel_rep.get(14) == "100.0"  # CumQty remained 100


def test_fix_heartbeat_and_test_request():
    session = FixSession("CLIENT", "EXCHANGE")

    # Inbound TestRequest (35=1) with TestReqID = "PING_123"
    test_req = FixMessage(
        msg_type=FixMsgType.TEST_REQUEST,
        sender_comp_id="EXCHANGE",
        target_comp_id="CLIENT",
        msg_seq_num=1
    )
    test_req.set(112, "PING_123")

    msg, heartbeat = session.receive_message(test_req.to_wire())
    assert msg.msg_type == FixMsgType.TEST_REQUEST
    assert heartbeat is not None
    assert heartbeat.msg_type == FixMsgType.HEARTBEAT
    assert heartbeat.get(112) == "PING_123"  # Echoed TestReqID


def test_fix_logout_session_lifecycle():
    session = FixSession("CLIENT", "EXCHANGE")
    # Logon
    logon_wire = FixMessage(FixMsgType.LOGON, "EXCHANGE", "CLIENT", 1).to_wire()
    session.receive_message(logon_wire)
    assert session.is_connected is True

    # Logout
    logout_wire = FixMessage(FixMsgType.LOGOUT, "EXCHANGE", "CLIENT", 2).to_wire()
    session.receive_message(logout_wire)
    assert session.is_connected is False


def test_exchange_strict_price_time_fifo_priority():
    exchange = ExchangeSimulator()
    # Two orders at the EXACT same price level: $100.00
    # Order A arrives first (timestamp t1), Order B arrives second (timestamp t2 > t1)
    exchange.seed_liquidity(
        symbol="SPY",
        bid_depth=[],
        ask_depth=[(100.00, 100.0), (100.00, 200.0)]
    )

    # Inbound Market Buy for 100 shares
    session = FixSession("CLIENT", "EXCHANGE_SIM")
    market_buy = session.build_new_order_single("CL-MKT-01", "SPY", "1", 100.0, ord_type="1")
    rep = exchange.process_new_order_single(market_buy)[0]

    assert rep.get(39) == "2"  # Filled
    assert rep.get(14) == "100.0"
    # Order A was completely filled (100 shares consumed)
    # Order B remains on the book with 200 shares
    book = exchange.books["SPY"]
    assert len(book.asks) == 1
    assert book.asks[0].quantity == 200.0


def test_exchange_adverse_selection_multi_level_walk():
    exchange = ExchangeSimulator()
    # Thin book with 3 distinct price levels:
    # 50 @ $10.00, 50 @ $10.50, 100 @ $11.00
    exchange.seed_liquidity(
        symbol="THIN",
        bid_depth=[],
        ask_depth=[(10.00, 50.0), (10.50, 50.0), (11.00, 100.0)]
    )

    session = FixSession("CLIENT", "EXCHANGE_SIM")
    # Large market order for 200 shares walks the entire depth
    big_order = session.build_new_order_single("CL-BIG-01", "THIN", "1", 200.0, ord_type="1")
    rep = exchange.process_new_order_single(big_order)[0]

    assert rep.get(39) == "2"
    assert rep.get(14) == "200.0"
    # Expected VWAP: (50*10 + 50*10.50 + 100*11.00) / 200 = (500 + 525 + 1100) / 200 = 2125 / 200 = 10.6250
    assert rep.get(6) == "10.6250"
    assert len(exchange.books["THIN"].asks) == 0  # Book swept completely


def test_exchange_cancel_after_fill_race_condition():
    exchange = ExchangeSimulator()
    exchange.seed_liquidity("XYZ", bid_depth=[], ask_depth=[(50.0, 100.0)])

    session = FixSession("CLIENT", "EXCHANGE_SIM")
    order = session.build_new_order_single("CL-XYZ-1", "XYZ", "1", 100.0, price=50.0, ord_type="2")
    exchange.process_new_order_single(order)

    # Order is now completely FILLED (leaves = 0)
    # Now an in-flight cancel request arrives
    cancel_req = FixMessage(FixMsgType.ORDER_CANCEL_REQUEST, "CLIENT", "EXCHANGE_SIM", 2)
    cancel_req.set(11, "CANCEL-XYZ-1")
    cancel_req.set(41, "CL-XYZ-1")
    cancel_req.set(55, "XYZ")

    rep = exchange.process_order_cancel_request(cancel_req)
    assert rep.get(151) == "0.0"  # LeavesQty must remain 0 (cannot cancel already filled order)
