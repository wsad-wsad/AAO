import os
import subprocess
from typing import Any, Dict, List

import dotenv
import phonenumbers
import requests
from langchain.tools import tool
from phonenumbers import carrier, geocoder, timezone
from wappalyzer import analyze

dotenv.load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
NETLAS_API_KEY = os.environ.get("NETLAS_API_KEY")


@tool
def google_search(query: str):
    """
    Search Netlas.io for a specific IP address or domain.
        Args:
            query: The target IP or domain name (e.g., '1.1.1.1' or 'example.com').
    """
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx=54bb47303e8c84f42&q={query}"
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error Google: {e}")
        return None


@tool
def netlas_search(query: str):
    """
    Execute a search query against the Netlas.io database to find internet-connected devices.
    """
    try:
        url = f"https://app.netlas.io/api/host/{query}"

        headers = {
            "Authorization": f"Bearer {NETLAS_API_KEY}",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error Netlas: {e}")
        return None


@tool
def holehe_search(target: str):
    """
    Enter your email to find out if you are registered on any site.
    """
    try:
        result = subprocess.run(
            ["holehe", target], capture_output=True, text=True, check=True
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@tool
def phone_lookup(phone_number: str) -> Dict[str, Any]:
    """
    Perform an in-depth OSINT analysis of a phone number using ALL available
    phonenumbers library features (FIXED VERSION).
    """
    try:
        # 1. PARSE
        parsed = phonenumbers.parse(phone_number, None)

        # 2. VALIDATION
        is_valid = phonenumbers.is_valid_number(parsed)
        is_possible = phonenumbers.is_possible_number(parsed)

        validation_reason = None
        if not is_possible:
            # is_possible_number_with_reason mengembalikan enum reason
            reason_obj = phonenumbers.is_possible_number_with_reason(parsed)
            validation_reason = str(reason_obj).replace("ValidationResult.", "")

        # 3. CORE DATA
        region_code = phonenumbers.region_code_for_number(parsed)

        # Country Code Source
        cc_source = None
        if parsed.country_code_source is not None:
            # Di Python Enum, kita pakai .name langsung
            cc_source = parsed.country_code_source

        national_sig_num = phonenumbers.national_significant_number(parsed)

        # 4. FORMATTING
        fmt_e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        fmt_intl = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        fmt_nat = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL
        )
        fmt_rfc = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.RFC3966
        )

        # 5. OSINT EXTRACTORS
        geo_desc = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en")
        tz_data = list(timezone.time_zones_for_number(parsed))

        # 6. NUMBER TYPE (PERBAIKAN DI SINI)
        # num_type adalah objek Enum, jadi kita ambil .name saja
        num_type = phonenumbers.phonenumberutil.number_type(parsed)
        type_desc = num_type  # <--- ini yang benar, tanpa DESCRIPTORS

        # 7. RAW METADATA
        italian_leading_zero = parsed.italian_leading_zero
        pref_dom_carrier = parsed.preferred_domestic_carrier_code

        result = {
            "input": phone_number,
            "validation": {
                "is_valid": is_valid,
                "is_possible": is_possible,
                "reason_if_invalid": validation_reason,
            },
            "structure": {
                "country_code": parsed.country_code,
                "region_code": region_code,
                "national_number": str(parsed.national_number),
                "national_significant_number": national_sig_num,
                "country_code_source": cc_source,
                "italian_leading_zero": italian_leading_zero,
                "preferred_domestic_carrier_code": pref_dom_carrier,
            },
            "osint_data": {
                "location": geo_desc,
                "carrier": carrier_name,
                "timezone": tz_data,
                "type": type_desc,
            },
            "formats": {
                "E164": fmt_e164,
                "International": fmt_intl,
                "National": fmt_nat,
                "RFC3966": fmt_rfc,
            },
        }

        if not is_valid and "INVALID_COUNTRY_CODE" in (validation_reason or ""):
            result["error_note"] = "Kode negara tidak dikenali atau salah."

        return result

    except Exception as e:
        return {
            "status": "error",
            "exception_type": type(e).__name__,
            "message": str(e),
            "input": phone_number,
        }


def search_web(username: str, noFalsePositives: bool) -> List[str]:
    try:
        url = f"http://main_go:8000/search-user"
        response = requests.get(
            url, params={"username": username, "noFalsePositives": noFalsePositives}
        )

        return response.json()

    except Exception as e:
        print(f"Error user search: {e}")
        return []


@tool
def wappalyzer(target: str):
    """
    Enter a url to perform a tech stack analysis of what the target is using.
    """
    try:
        results = analyze(
            url="target",
            scan_type="full",
        )
        print(results)
        return results
    except Exception as e:
        return f"error: {str(e)}"
