"""Tests for orders router (CSV import and get/list operations)."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_auth_headers

client = TestClient(app)


@pytest.fixture
def auth_token():
	"""Get authentication token for orders tests."""
	headers = make_auth_headers(client, username="test_orders_user")
	return headers["Authorization"].removeprefix("Bearer ")


@pytest.fixture(autouse=True)
def cleanup_orders(auth_token):
	"""Clean up orders before and after each test."""
	yield
	# Delete all orders after each test
	headers = {"Authorization": f"Bearer {auth_token}"}
	response = client.get("/api/orders/", headers=headers)
	if response.status_code == 200:
		for order in response.json().get("orders", []):
			client.delete(f"/api/orders/{order['id']}", headers=headers)


def test_import_csv_success(auth_token):
	"""Test successful CSV import."""
	csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,US0378331005,1000.00 EUR,10.0,Finalizada"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
		tmp.write(csv_content)
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			response = client.post(
				"/api/orders/import-csv",
				files={"file": ("orders.csv", f, "text/csv")},
				headers={"Authorization": f"Bearer {auth_token}"},
			)

		assert response.status_code == 200
		data = response.json()
		assert data["success"] is True
		assert data["imported_count"] == 2
		assert data["updated_count"] == 0
		assert len(data["errors"]) == 0
	finally:
		tmp_path.unlink(missing_ok=True)


def post_csv_import(auth_token: str, csv_content: str, endpoint: str = "/api/orders/import-csv"):
	"""Post CSV content to an order import endpoint."""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
		tmp.write(csv_content)
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			return client.post(
				endpoint,
				files={"file": ("orders.csv", f, "text/csv")},
				headers={"Authorization": f"Bearer {auth_token}"},
			)
	finally:
		tmp_path.unlink(missing_ok=True)


def test_import_csv_skips_exact_reimport(auth_token):
	"""Test importing the same CSV twice skips already-present orders."""
	csv_content = """Fecha de la orden,ISIN,Importe estimado,Numero de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,US0378331005,1000.00 EUR,10.0,Finalizada"""

	first_response = post_csv_import(auth_token, csv_content)
	assert first_response.status_code == 200
	first_data = first_response.json()
	assert first_data["imported_count"] == 2
	assert first_data["skipped_count"] == 0

	orders_before = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"}).json()["orders"]

	second_response = post_csv_import(auth_token, csv_content)
	assert second_response.status_code == 200
	second_data = second_response.json()
	assert second_data["imported_count"] == 0
	assert second_data["updated_count"] == 0
	assert second_data["skipped_count"] == 2

	orders_after = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"}).json()["orders"]
	assert len(orders_after) == 2
	assert {order["id"] for order in orders_after} == {order["id"] for order in orders_before}
	assert {order["created_at"] for order in orders_after} == {order["created_at"] for order in orders_before}


def test_import_csv_with_one_new_row_only_adds_new_order(auth_token):
	"""Test reimporting a CSV with one additional row only adds the new row."""
	initial_csv = """Fecha de la orden,ISIN,Importe estimado,Numero de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,US0378331005,1000.00 EUR,10.0,Finalizada"""
	expanded_csv = """Fecha de la orden,ISIN,Importe estimado,Numero de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,US0378331005,1000.00 EUR,10.0,Finalizada
21/03/2024,LU0274208692,1200.00 EUR,12.0,Finalizada"""

	first_response = post_csv_import(auth_token, initial_csv)
	assert first_response.status_code == 200

	second_response = post_csv_import(auth_token, expanded_csv)
	assert second_response.status_code == 200
	data = second_response.json()
	assert data["imported_count"] == 1
	assert data["skipped_count"] == 2

	orders = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"}).json()
	assert orders["total"] == 3


def test_preview_import_csv_marks_already_present_orders(auth_token):
	"""Test CSV preview classifies existing and new rows."""
	initial_csv = """Fecha de la orden,ISIN,Importe estimado,Numero de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada"""
	preview_csv = """Fecha de la orden,ISIN,Importe estimado,Numero de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,US0378331005,1000.00 EUR,10.0,Finalizada"""

	import_response = post_csv_import(auth_token, initial_csv)
	assert import_response.status_code == 200
	existing_order = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"}).json()["orders"][0]

	preview_response = post_csv_import(auth_token, preview_csv, "/api/orders/import-csv/preview")
	assert preview_response.status_code == 200
	data = preview_response.json()
	assert data["new_count"] == 1
	assert data["skipped_count"] == 1
	assert [order["import_status"] for order in data["orders"]] == ["already_present", "new"]
	assert data["orders"][0]["existing_order_id"] == existing_order["id"]
	assert data["orders"][1]["existing_order_id"] is None


def test_import_csv_with_errors(auth_token):
	"""Test CSV import with validation errors."""
	csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
invalid_date,IE00B4L5Y983,500.00 EUR,5.0,Finalizada
20/02/2024,INVALID_ISIN,1000.00 EUR,10.0,Finalizada"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
		tmp.write(csv_content)
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			response = client.post(
				"/api/orders/import-csv",
				files={"file": ("orders.csv", f, "text/csv")},
				headers={"Authorization": f"Bearer {auth_token}"},
			)

		assert response.status_code == 200
		data = response.json()
		assert len(data["errors"]) > 0
	finally:
		tmp_path.unlink(missing_ok=True)


def test_import_csv_not_csv_file(auth_token):
	"""Test CSV import with non-CSV file."""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
		tmp.write("not a csv")
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			response = client.post(
				"/api/orders/import-csv",
				files={"file": ("orders.txt", f, "text/plain")},
				headers={"Authorization": f"Bearer {auth_token}"},
			)

		assert response.status_code == 400
		assert "CSV" in response.json()["detail"]
	finally:
		tmp_path.unlink(missing_ok=True)


def test_import_csv_unauthorized():
	"""Test CSV import without authentication."""
	csv_content = "Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado"

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
		tmp.write(csv_content)
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			response = client.post("/api/orders/import-csv", files={"file": ("orders.csv", f, "text/csv")})

		assert response.status_code == 401
	finally:
		tmp_path.unlink(missing_ok=True)


def test_get_orders_empty(auth_token):
	"""Test getting orders when none exist."""
	response = client.get(
		"/api/orders/",
		headers={"Authorization": f"Bearer {auth_token}"},
	)

	assert response.status_code == 200
	data = response.json()
	assert "orders" in data
	assert isinstance(data["orders"], list)
	assert data["total"] == 0


def test_get_orders_after_import(auth_token):
	"""Test getting orders after CSV import."""
	csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
		tmp.write(csv_content)
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			client.post(
				"/api/orders/import-csv",
				files={"file": ("orders.csv", f, "text/csv")},
				headers={"Authorization": f"Bearer {auth_token}"},
			)
	finally:
		tmp_path.unlink(missing_ok=True)

	response = client.get(
		"/api/orders/",
		headers={"Authorization": f"Bearer {auth_token}"},
	)

	assert response.status_code == 200
	data = response.json()
	assert data["total"] == 1
	assert len(data["orders"]) == 1
	assert data["orders"][0]["isin"] == "IE00B4L5Y983"


def test_get_order_by_id(auth_token):
	"""Test getting specific order by ID."""
	csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE00B4L5Y983,500.00 EUR,5.0,Finalizada"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
		tmp.write(csv_content)
		tmp_path = Path(tmp.name)

	try:
		with open(tmp_path, "rb") as f:
			client.post(
				"/api/orders/import-csv",
				files={"file": ("orders.csv", f, "text/csv")},
				headers={"Authorization": f"Bearer {auth_token}"},
			)
	finally:
		tmp_path.unlink(missing_ok=True)

	orders_response = client.get("/api/orders/", headers={"Authorization": f"Bearer {auth_token}"})
	data = orders_response.json()
	assert data["total"] > 0

	order_id = data["orders"][0]["id"]
	response = client.get(
		f"/api/orders/{order_id}",
		headers={"Authorization": f"Bearer {auth_token}"},
	)

	assert response.status_code == 200
	assert response.json()["isin"] == "IE00B4L5Y983"


def test_get_order_not_found(auth_token):
	"""Test getting non-existent order."""
	response = client.get("/api/orders/999", headers={"Authorization": f"Bearer {auth_token}"})
	assert response.status_code == 404
