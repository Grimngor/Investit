"""Geographic data and mapping services."""

from typing import Dict, List, Optional


# Country code to region mapping
COUNTRY_REGIONS: Dict[str, str] = {
    # North America
    "US": "North America",
    "CA": "North America",
    "MX": "North America",
    # Europe
    "GB": "Europe",
    "DE": "Europe",
    "FR": "Europe",
    "IT": "Europe",
    "ES": "Europe",
    "NL": "Europe",
    "CH": "Europe",
    "SE": "Europe",
    "NO": "Europe",
    "DK": "Europe",
    "FI": "Europe",
    "IE": "Europe",
    "AT": "Europe",
    "BE": "Europe",
    "PT": "Europe",
    "PL": "Europe",
    # Asia Pacific
    "JP": "Asia Pacific",
    "CN": "Asia Pacific",
    "HK": "Asia Pacific",
    "SG": "Asia Pacific",
    "KR": "Asia Pacific",
    "AU": "Asia Pacific",
    "NZ": "Asia Pacific",
    "IN": "Asia Pacific",
    "TW": "Asia Pacific",
    "TH": "Asia Pacific",
    "MY": "Asia Pacific",
    "ID": "Asia Pacific",
    # Emerging Markets
    "BR": "Emerging Markets",
    "ZA": "Emerging Markets",
    "RU": "Emerging Markets",
    "TR": "Emerging Markets",
    "SA": "Emerging Markets",
    "AE": "Emerging Markets",
}


def get_region_for_country(country_code: str) -> str:
    """Get region name for a country code."""
    return COUNTRY_REGIONS.get(country_code, "Other")


def get_country_name(country_code: str) -> str:
    """Get country name from country code."""
    country_names = {
        "US": "United States",
        "GB": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
        "JP": "Japan",
        "CN": "China",
        "CA": "Canada",
        # Add more as needed
    }
    return country_names.get(country_code, country_code)
