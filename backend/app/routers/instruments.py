"""Router for instrument metadata management."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.routers.auth import get_current_user
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("/{isin}")
async def get_instrument(isin: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""
	Get instrument metadata by ISIN.

	Returns instrument information including name, type, and allocations.
	"""
	storage = StorageService()
	instruments = storage.load_instruments()

	# Find instrument by ISIN
	instrument = next((inst for inst in instruments if inst.get("isin") == isin), None)

	if not instrument:
		raise HTTPException(status_code=404, detail=f"Instrument {isin} not found")

	return instrument


@router.put("/{isin}")
async def update_instrument_metadata(isin: str, metadata: dict[str, Any], current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""
	Update instrument metadata (manual override for geo/sector allocations).

	Allows users to manually set:
	- geo_allocation: dict of country codes to percentages
	- sector_allocation: dict of sector names to percentages
	- name: instrument name
	- type: instrument type (fund, etf, crypto, bond)
	"""
	storage = StorageService()
	instruments = storage.load_instruments()

	# Find existing instrument
	existing_idx = next((i for i, inst in enumerate(instruments) if inst.get("isin") == isin), None)

	if existing_idx is not None:
		# Update existing instrument
		instruments[existing_idx].update(metadata)
		updated = instruments[existing_idx]
	else:
		# Create new instrument entry
		new_instrument = {"isin": isin, **metadata}
		instruments.append(new_instrument)
		updated = new_instrument

	# Save updated instruments
	storage.save_instruments(instruments)

	return updated


@router.get("/")
async def list_instruments(current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
	"""
	List all instruments with metadata.
	"""
	storage = StorageService()
	instruments = storage.load_instruments()
	return instruments
