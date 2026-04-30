"""Router for instrument metadata management."""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.models.user import User
from app.routers.auth import get_current_user
from app.services.background_jobs import background_jobs
from app.services.instrument_metadata_service import InstrumentMetadataService
from app.services.storage_service import StorageService, load_users

router = APIRouter(prefix="/api/instruments", tags=["instruments"])
logger = logging.getLogger(__name__)
INSTRUMENT_METADATA_JOB = "instrument_metadata_refresh"


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


async def _refresh_and_record(username: str, force: bool) -> None:
	"""Run metadata refresh and record job state."""
	background_jobs.start(username, INSTRUMENT_METADATA_JOB)
	try:
		result = await InstrumentMetadataService.refresh_for_user(username, force=force)
	except Exception as e:
		background_jobs.fail(username, INSTRUMENT_METADATA_JOB, str(e))
		raise
	else:
		background_jobs.complete(username, INSTRUMENT_METADATA_JOB, result)


def _queued_response(username: str, count: int, message: str) -> dict[str, Any]:
	"""Build a standard queued metadata response."""
	background_jobs.queue(username, INSTRUMENT_METADATA_JOB, count)
	return {
		"success": True,
		"queued": True,
		"in_progress": False,
		"job_type": INSTRUMENT_METADATA_JOB,
		"attempted": count,
		"updated": 0,
		"skipped": 0,
		"failures": [],
		"message": message,
	}


@router.post("/sync")
async def sync_instrument_metadata(
	background_tasks: BackgroundTasks,
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""Queue a refresh for missing instrument metadata."""
	users = load_users()
	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	if background_jobs.is_active(current_user.username, INSTRUMENT_METADATA_JOB):
		return {
			"success": True,
			"queued": False,
			"in_progress": True,
			"job_type": INSTRUMENT_METADATA_JOB,
			"attempted": 0,
			"updated": 0,
			"skipped": 0,
			"failures": [],
			"message": "Instrument metadata refresh already in progress",
		}

	unique_isins = InstrumentMetadataService.get_user_isins(current_user.username)
	if not unique_isins:
		return {
			"success": True,
			"queued": False,
			"in_progress": False,
			"job_type": INSTRUMENT_METADATA_JOB,
			"attempted": 0,
			"updated": 0,
			"skipped": 0,
			"failures": [],
		}

	if not InstrumentMetadataService.requires_provider(unique_isins):
		result = await InstrumentMetadataService.refresh_for_user(current_user.username, force=False)
		return {
			**result,
			"queued": False,
			"in_progress": False,
			"job_type": INSTRUMENT_METADATA_JOB,
			"attempted": result.get("total", 0),
			"failures": result.get("errors", []),
		}

	response = _queued_response(current_user.username, len(unique_isins), f"Refreshing metadata for {len(unique_isins)} instruments")
	background_tasks.add_task(_refresh_and_record, current_user.username, False)
	return response


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


@router.post("/refresh")
async def refresh_instrument_metadata(
	background_tasks: BackgroundTasks,
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""Queue a forced refresh of instrument metadata from providers."""
	users = load_users()
	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	if background_jobs.is_active(current_user.username, INSTRUMENT_METADATA_JOB):
		return {
			"success": True,
			"queued": False,
			"in_progress": True,
			"job_type": INSTRUMENT_METADATA_JOB,
			"message": "Instrument metadata refresh already in progress",
			"updated": 0,
			"total": 0,
			"errors": [],
		}

	unique_isins = InstrumentMetadataService.get_user_isins(current_user.username)
	if not unique_isins:
		return {
			"success": True,
			"queued": False,
			"in_progress": False,
			"job_type": INSTRUMENT_METADATA_JOB,
			"message": "No ISINs to refresh",
			"updated": 0,
			"total": 0,
			"errors": [],
		}

	if not InstrumentMetadataService.requires_provider(unique_isins):
		result = await InstrumentMetadataService.refresh_for_user(current_user.username, force=True)
		return {**result, "queued": False, "in_progress": False, "job_type": INSTRUMENT_METADATA_JOB}

	response = _queued_response(current_user.username, len(unique_isins), f"Refreshing metadata for {len(unique_isins)} instruments")
	response.update({"total": len(unique_isins), "errors": []})
	background_tasks.add_task(_refresh_and_record, current_user.username, True)
	return response
