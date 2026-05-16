"""Parser for MyInvestor order confirmation emails."""

import html
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from typing import Any


class MyInvestorEmailParseError(ValueError):
	"""Raised when a MyInvestor email cannot be parsed into an order."""


@dataclass(frozen=True)
class MyInvestorParsedOrder:
	"""Parsed MyInvestor email order and source metadata."""

	gmail_message_id: str
	gmail_thread_id: str
	email_date: str
	email_from: str
	email_subject: str
	order: dict[str, Any]
	operation_type: str
	value_date: str | None
	unit_price: float
	amount_gross: float
	amount_net: float | None
	raw_snippet: str


class MyInvestorEmailParser:
	"""Parse MyInvestor order confirmation emails into InvestIt order dictionaries."""

	TOLERANCE_EUR = 0.10
	ISIN_PATTERN = re.compile(r"\b[A-Z]{2}[A-Z0-9]{10}\b", re.IGNORECASE)
	DATE_PATTERN = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
	NUMBER_PATTERN = re.compile(r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b|\b\d+(?:[.,]\d+)?\b")

	def looks_like_order(self, subject: str, text: str) -> bool:
		"""Return True when subject and body look like a MyInvestor order confirmation."""
		combined = self._fold_text(f"{subject}\n{text}")
		has_confirmation = "CONFIRMACION DE OPERACION DE VALORES" in combined
		has_isin = "CODIGO ISIN" in combined or self.ISIN_PATTERN.search(combined) is not None
		has_operation = any(token in combined for token in ("SUSCRIPCION", "COMPRA", "REEMBOLSO", "VENTA"))
		has_amount = "IMPORTE BRUTO" in combined or "IMPORTE EFECTIVO NETO" in combined
		return has_confirmation or (has_isin and has_operation and has_amount)

	def parse_message(
		self,
		*,
		gmail_message_id: str,
		gmail_thread_id: str,
		email_date: str,
		email_from: str,
		email_subject: str,
		message_text: str,
	) -> MyInvestorParsedOrder:
		"""Parse a Gmail message body into a MyInvestor order."""
		clean = self.normalize_text(message_text)
		if not self.looks_like_order(email_subject, clean):
			raise MyInvestorEmailParseError("Email does not look like a MyInvestor order confirmation.")

		isin = self._extract_isin(clean)
		operation_type = self._extract_operation_type(clean)
		operation_date, value_date = self._extract_dates(clean)
		shares, unit_price, amount_gross = self._extract_shares_price_amount(clean)
		amount_net = self._extract_net_amount(clean)
		order_type = self._order_type_from_operation(operation_type)

		self._validate(
			isin=isin,
			operation_type=operation_type,
			operation_date=operation_date,
			shares=shares,
			unit_price=unit_price,
			amount_gross=amount_gross,
		)

		order = {
			"id": str(uuid.uuid4()),
			"date": self._date_to_iso(operation_date),
			"isin": isin.upper(),
			"amount_eur": amount_gross,
			"shares": shares,
			"price_per_share": unit_price,
			"price_currency": "EUR",
			"price_date": self._date_to_iso(operation_date),
			"order_type": order_type,
			"status": "Finalizada",
			"notes": f"Imported from MyInvestor Gmail message {gmail_message_id}",
			"created_at": datetime.now(UTC).isoformat(),
		}

		return MyInvestorParsedOrder(
			gmail_message_id=gmail_message_id,
			gmail_thread_id=gmail_thread_id,
			email_date=email_date,
			email_from=email_from,
			email_subject=email_subject,
			order=order,
			operation_type=operation_type,
			value_date=self._date_to_iso(value_date) if value_date else None,
			unit_price=unit_price,
			amount_gross=amount_gross,
			amount_net=amount_net,
			raw_snippet=clean[:1000],
		)

	def parse_eml_bytes(self, content: bytes, gmail_message_id: str = "eml-sample") -> MyInvestorParsedOrder:
		"""Parse a raw .eml payload into a MyInvestor order."""
		message = BytesParser(policy=policy.default).parsebytes(content)
		return self.parse_message(
			gmail_message_id=gmail_message_id,
			gmail_thread_id="",
			email_date=self._message_date(message),
			email_from=str(message.get("from", "")),
			email_subject=str(message.get("subject", "")),
			message_text=self.message_to_text(message),
		)

	def message_to_text(self, message: EmailMessage) -> str:
		"""Extract normalized visible text from an email message."""
		parts: list[str] = []
		if message.is_multipart():
			for part in message.walk():
				content_type = part.get_content_type()
				if content_type not in {"text/plain", "text/html"}:
					continue
				payload = part.get_content()
				parts.append(self.html_to_text(str(payload)) if content_type == "text/html" else str(payload))
		else:
			payload = message.get_content()
			if message.get_content_type() == "text/html":
				parts.append(self.html_to_text(str(payload)))
			else:
				parts.append(str(payload))
		return self.normalize_text("\n".join(parts))

	def html_to_text(self, html_content: str) -> str:
		"""Convert MyInvestor HTML email content into parser-friendly text."""
		text = str(html_content)
		text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
		text = re.sub(r"</\s*(td|th)\s*>", "\t", text, flags=re.IGNORECASE)
		text = re.sub(r"</\s*(tr|p|div|li|h[1-6])\s*>", "\n", text, flags=re.IGNORECASE)
		text = re.sub(r"<[^>]+>", " ", text)
		return self.normalize_text(html.unescape(text))

	def normalize_text(self, text: str) -> str:
		"""Normalize whitespace and common non-breaking characters."""
		return (
			str(text or "")
			.replace("\u00a0", " ")
			.replace("\r", "\n")
			.replace("\t", " ")
			.replace("�", "ó")
			.replace("Ã³", "ó")
			.replace("Ã“", "Ó")
			.replace("Ãº", "ú")
			.replace("Ãš", "Ú")
			.replace("Ã±", "ñ")
		)

	def _extract_isin(self, text: str) -> str:
		"""Extract the ISIN from normalized email text."""
		match = re.search(r"C[oó]digo\s+ISIN[:\s]*([A-Z]{2}[A-Z0-9]{10})", text, flags=re.IGNORECASE)
		if match:
			return match.group(1)
		match = self.ISIN_PATTERN.search(text)
		return match.group(0) if match else ""

	def _extract_operation_type(self, text: str) -> str:
		"""Extract the MyInvestor operation type."""
		match = re.search(
			r"(SUSCRIPCI[OÓ]N\s+I\.I\.C\.|SUSCRIPCION\s+I\.I\.C\.|SUSCRIPCI[OÓ]N|COMPRA|REEMBOLSO|VENTA)",
			text,
			flags=re.IGNORECASE,
		)
		return self.normalize_text(match.group(1)).upper() if match else ""

	def _extract_dates(self, text: str) -> tuple[str, str | None]:
		"""Extract operation date and optional value date."""
		block = self._block(text, r"Fecha\s+Operaci[oó]n", r"N[uúó]mero\s+de\s+t[iíó]tulos|Participaciones", 700)
		matches = self.DATE_PATTERN.findall(block)
		if not matches:
			matches = self.DATE_PATTERN.findall(text)
		return (matches[0] if matches else "", matches[1] if len(matches) > 1 else None)

	def _extract_shares_price_amount(self, text: str) -> tuple[float, float, float]:
		"""Extract shares, unit price, and gross amount."""
		block = self._block(
			text,
			r"N[uúó]mero\s+de\s+t[iíó]tulos/Participaciones|Participaciones",
			r"Comisiones|Gastos|Tasas|Retenci[oó]n",
			900,
		)
		tokens = [token for token in self.NUMBER_PATTERN.findall(block) if not self.DATE_PATTERN.fullmatch(token)]
		if len(tokens) >= 3:
			return (
				self.parse_number(tokens[0]),
				self.parse_number(tokens[1]),
				self.parse_number(tokens[2]),
			)

		return (
			self._number_near_label(text, r"N[uúó]mero\s+de\s+t[iíó]tulos/Participaciones|Participaciones"),
			self._number_near_label(text, r"Precio\s+Bruto"),
			self._number_near_label(text, r"Importe\s+Bruto"),
		)

	def _extract_net_amount(self, text: str) -> float | None:
		"""Extract net amount when the table structure is unambiguous."""
		block = self._block(text, r"Retenci[oó]n\s+Origen", r"El\s+Importe\s+Neto", 900)
		tokens = [self.parse_number(match.group(1)) for match in re.finditer(rf"({self.NUMBER_PATTERN.pattern})\s*EUR", block)]
		return tokens[2] if len(tokens) >= 3 else None

	def _validate(
		self,
		*,
		isin: str,
		operation_type: str,
		operation_date: str,
		shares: float,
		unit_price: float,
		amount_gross: float,
	) -> None:
		"""Validate the parsed order fields."""
		if not isin:
			raise MyInvestorEmailParseError("Missing ISIN.")
		if not operation_type:
			raise MyInvestorEmailParseError("Missing operation type.")
		if not operation_date or self._date_to_iso(operation_date) is None:
			raise MyInvestorEmailParseError("Missing or invalid operation date.")
		if not shares or shares <= 0:
			raise MyInvestorEmailParseError(f"Invalid shares/participations: {shares}.")
		if not unit_price or unit_price <= 0:
			raise MyInvestorEmailParseError(f"Invalid unit price: {unit_price}.")
		if not amount_gross or amount_gross <= 0:
			raise MyInvestorEmailParseError(f"Invalid gross amount: {amount_gross}.")

		calculated_amount = shares * unit_price
		if abs(calculated_amount - amount_gross) > self.TOLERANCE_EUR:
			raise MyInvestorEmailParseError(
				f"Validation failed: shares x price = {calculated_amount:.4f}, gross amount = {amount_gross:.4f}."
			)

	def _number_near_label(self, text: str, label_regex: str) -> float:
		"""Extract the first number near a label."""
		match = re.search(label_regex, text, flags=re.IGNORECASE)
		if not match:
			return float("nan")
		chunk = text[match.end() : match.end() + 300]
		number_match = self.NUMBER_PATTERN.search(chunk)
		return self.parse_number(number_match.group(0)) if number_match else float("nan")

	def _block(self, text: str, start_regex: str, end_regex: str, max_chars: int) -> str:
		"""Return a bounded text block between two labels."""
		start_match = re.search(start_regex, text, flags=re.IGNORECASE)
		if not start_match:
			return text[:max_chars]
		chunk = text[start_match.start() : start_match.start() + max_chars]
		end_match = re.search(end_regex, chunk, flags=re.IGNORECASE)
		return chunk[: end_match.start()] if end_match and end_match.start() > 0 else chunk

	def _order_type_from_operation(self, operation_type: str) -> str:
		"""Map a MyInvestor operation type to an InvestIt order type."""
		folded = self._fold_text(operation_type)
		return "sell" if any(token in folded for token in ("REEMBOLSO", "VENTA")) else "buy"

	def _date_to_iso(self, value: str | None) -> str | None:
		"""Convert DD/MM/YYYY to YYYY-MM-DD."""
		if not value:
			return None
		match = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", value.strip())
		if not match:
			return None
		return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"

	def _message_date(self, message: EmailMessage) -> str:
		"""Return the email date as ISO text when possible."""
		raw_date = message.get("date")
		if not raw_date:
			return ""
		try:
			return parsedate_to_datetime(raw_date).isoformat()
		except (TypeError, ValueError):
			return str(raw_date)

	def _fold_text(self, text: str) -> str:
		"""Return uppercase accent-free text for permissive matching."""
		normalized = unicodedata.normalize("NFKD", self.normalize_text(text))
		return "".join(char for char in normalized if not unicodedata.combining(char)).upper()

	def parse_number(self, raw: str) -> float:
		"""Parse Spanish or English formatted decimal text."""
		value = str(raw or "").replace("EUR", "").replace(" ", "").strip()
		has_comma = "," in value
		has_dot = "." in value
		if has_comma and has_dot:
			last_comma = value.rfind(",")
			last_dot = value.rfind(".")
			value = value.replace(".", "").replace(",", ".") if last_comma > last_dot else value.replace(",", "")
		elif has_comma:
			value = value.replace(",", ".")
		elif value.count(".") > 1:
			last_dot = value.rfind(".")
			value = value[:last_dot].replace(".", "") + "." + value[last_dot + 1 :]
		return float(value)
