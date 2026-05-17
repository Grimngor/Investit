"""Tests for Gmail-backed MyInvestor order imports."""

import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.gmail_import_service import GmailImportService
from app.utils.myinvestor_email_parser import MyInvestorEmailParser
from tests.conftest import make_auth_headers

client = TestClient(app)


MYINVESTOR_HTML = """
<html><body>
<title>CONFIRMACIÓN DE OPERACIÓN DE VALORES</title>
<p>VANGUARD EMERG MARKETS STOCK EUR ACC</p>
<font>Código ISIN: IE0031786696</font>
<table>
<tr><td>SUSCRIPCION I.I.C.</td><td>147716341/390</td></tr>
<tr><td><strong>Fecha Operación</strong></td><td><strong>Fecha Valor</strong></td></tr>
<tr><td>07/05/2026</td><td>08/05/2026</td></tr>
<tr>
  <td><strong>Número de títulos/Participaciones</strong></td>
  <td><strong>Precio Bruto</strong></td>
  <td><strong>Importe Bruto</strong></td>
</tr>
<tr><td>2.15</td><td>301.3995&nbsp;EUR</td><td>648.00&nbsp;EUR</td></tr>
<tr>
  <td><strong>Retención Origen</strong></td>
  <td><strong>Retención Destino</strong></td>
  <td><strong>Importe Efectivo Neto</strong></td>
  <td><strong>Tipo de Cambio</strong></td>
</tr>
<tr><td>0.00&nbsp;EUR</td><td>0.00&nbsp;EUR</td><td>648.00&nbsp;EUR</td><td>1.00&nbsp;EUR</td></tr>
</table>
</body></html>
"""


def gmail_message(message_id: str = "gmail-1") -> dict:
	"""Build a Gmail API message payload for tests."""
	body = base64.urlsafe_b64encode(MYINVESTOR_HTML.encode("utf-8")).decode("ascii").rstrip("=")
	return {
		"id": message_id,
		"threadId": "thread-1",
		"payload": {
			"mimeType": "text/html",
			"headers": [
				{"name": "From", "value": "notificaciones@myinvestor.es"},
				{
					"name": "Subject",
					"value": "** MYINVESTOR **CONFIRMACIÓN DE OPERACIÓN DE VALORES # SUSCRIPCION # 648.00 EUR",
				},
				{"name": "Date", "value": "Thu, 7 May 2026 02:51:09 +0200"},
			],
			"body": {"data": body},
		},
	}


class FakeGmailImportService(GmailImportService):
	"""Gmail import service with network calls replaced by fixtures."""

	def __init__(self) -> None:
		"""Initialize the fake service."""
		super().__init__()
		self.requested_max_messages: list[int] = []

	async def access_token(self, username: str) -> str:
		"""Return a fake token."""
		return "fake-token"

	async def list_message_ids(self, access_token: str, query: str, max_messages: int) -> list[str]:
		"""Return fixture message IDs."""
		self.requested_max_messages.append(max_messages)
		return ["gmail-1"]

	async def get_message(self, access_token: str, message_id: str) -> dict:
		"""Return a fixture Gmail message."""
		return gmail_message(message_id)


def test_myinvestor_parser_extracts_order_fields() -> None:
	"""Test parsing a MyInvestor confirmation email body."""
	parser = MyInvestorEmailParser()
	parsed = parser.parse_message(
		gmail_message_id="gmail-1",
		gmail_thread_id="thread-1",
		email_date="Thu, 7 May 2026 02:51:09 +0200",
		email_from="notificaciones@myinvestor.es",
		email_subject="CONFIRMACIÓN DE OPERACIÓN DE VALORES",
		message_text=parser.html_to_text(MYINVESTOR_HTML),
	)

	assert parsed.order["date"] == "2026-05-07"
	assert parsed.value_date == "2026-05-08"
	assert parsed.order["isin"] == "IE0031786696"
	assert parsed.order["order_type"] == "buy"
	assert parsed.order["amount_eur"] == pytest.approx(648.0)
	assert parsed.order["shares"] == pytest.approx(2.15)
	assert parsed.order["price_per_share"] == pytest.approx(301.3995)
	assert parsed.amount_net == pytest.approx(648.0)


@pytest.mark.asyncio
async def test_gmail_scan_and_import_selected_message() -> None:
	"""Test scanning Gmail previews and importing a selected message."""
	headers = make_auth_headers(client, username="gmail_user")
	service = FakeGmailImportService()

	scan = await service.scan("gmail_user")
	assert scan.new_count == 1
	assert service.requested_max_messages == [100]
	assert scan.orders[0].gmail_message_id == "gmail-1"
	assert scan.orders[0].order["isin"] == "IE0031786696"

	result = await service.import_messages("gmail_user", ["gmail-1"])
	assert result["imported_count"] == 1
	assert result["skipped_count"] == 0

	orders_response = client.get("/api/orders/", headers=headers)
	assert orders_response.status_code == 200
	orders = orders_response.json()["orders"]
	assert len(orders) == 1
	assert orders[0]["isin"] == "IE0031786696"

	second_result = await service.import_messages("gmail_user", ["gmail-1"])
	assert second_result["imported_count"] == 0
	assert second_result["skipped_count"] == 1

	await service.scan("gmail_user")
	assert service.requested_max_messages[-1] == 20
