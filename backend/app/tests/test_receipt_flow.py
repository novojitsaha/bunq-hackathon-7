from io import BytesIO


def test_fixture_upload_review_confirm_updates_dashboard(client):
    upload = client.post(
        "/api/receipts/upload",
        files={"file": ("junk-receipt.jpg", BytesIO(b"fake image"), "image/jpeg")},
    )
    assert upload.status_code == 200
    receipt = upload.json()
    assert receipt["status"] == "READY"
    assert receipt["items"]

    red_bull = next(item for item in receipt["items"] if item["normalized_name"] == "energy drink")
    patch = client.patch(
        f"/api/receipts/{receipt['id']}/items/{red_bull['id']}",
        json={"selected_for_user": False},
    )
    assert patch.status_code == 200
    assert patch.json()["selected_for_user"] is False

    confirm = client.post(f"/api/receipts/{receipt['id']}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["selected_calories"] > 0

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["calories"]["outside_schijf"] > 0
    assert body["last_purchases"][0]["receipt_id"] == receipt["id"]

