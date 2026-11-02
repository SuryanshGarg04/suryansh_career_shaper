import pytest
from fastapi import HTTPException
from app.models.shipment import Shipment
from app.services.fsm import ShipmentLifecycleFSM

def test_valid_fsm_transitions():
    shipment = Shipment(
        shipment_id="SHP_TEST_01",
        origin_hub_id="HUB_DEL",
        dest_hub_id="HUB_BOM",
        weight_kg=1200.0,
        status="CREATED"
    )

    # CREATED -> ASSIGNED
    ShipmentLifecycleFSM.transition(shipment, "ASSIGNED")
    assert shipment.status == "ASSIGNED"

    # ASSIGNED -> IN_TRANSIT
    ShipmentLifecycleFSM.transition(shipment, "IN_TRANSIT")
    assert shipment.status == "IN_TRANSIT"
    assert shipment.dispatched_at is not None

    # IN_TRANSIT -> OUT_FOR_DELIVERY
    ShipmentLifecycleFSM.transition(shipment, "OUT_FOR_DELIVERY")
    assert shipment.status == "OUT_FOR_DELIVERY"

    # OUT_FOR_DELIVERY -> DELIVERED
    ShipmentLifecycleFSM.transition(shipment, "DELIVERED")
    assert shipment.status == "DELIVERED"
    assert shipment.delivered_at is not None

def test_invalid_fsm_transition_raises_error():
    shipment = Shipment(
        shipment_id="SHP_TEST_02",
        origin_hub_id="HUB_DEL",
        dest_hub_id="HUB_BOM",
        weight_kg=1200.0,
        status="CREATED"
    )

    # Cannot jump directly from CREATED to DELIVERED
    with pytest.raises(HTTPException) as exc_info:
        ShipmentLifecycleFSM.transition(shipment, "DELIVERED")
    assert exc_info.value.status_code == 400
    assert "Illegal state transition" in exc_info.value.detail
