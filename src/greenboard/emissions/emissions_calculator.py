"""
Universal Package Delivery Carbon Emissions Calculator

Modular system supporting UPS, USPS, FedEx, DHL and other carriers.
Includes accurate geocoding for distance calculation.
"""

import requests
import uuid
import base64
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import json
import time


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

EMISSION_FACTORS = {
    # Converted to metric (kg CO2e per tonne-km)
    'tonne_km': {
        'truck_average': 0.127,
        'truck_urban_delivery': 0.307,
        'truck_longhaul': 0.062,
        'rail': 0.022,
        'air_shorthaul': 0.82,
        'air_longhaul': 0.69,
        'ocean_container': 0.010,
        'ocean_bulk': 0.004,
        'last_mile': 0.200
    },
    'dimensional_factors': {
        'ups': 139,
        'fedex': 139,
        'dhl': 139,
        'usps': 166,
        'air_international': 166,
        'metric_air': 5000
    }
}

DEFAULT_DISTANCES = {
    'domestic_ground': 1200,
    'domestic_air': 1500,
    'international': 5000,
    'last_mile': 10
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Address:
    """Standardized address structure"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    def to_string(self) -> str:
        parts = []
        if self.street:
            parts.append(self.street)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(filter(None, parts))
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PackageInfo:
    """Standardized package information structure"""
    tracking_number: str
    weight_kg: float
    dimensions: Optional[Tuple[float, float, float]] = None
    origin: Optional[Address] = None
    destination: Optional[Address] = None
    service_code: Optional[str] = None
    service_description: Optional[str] = None
    carrier: str = 'unknown'
    pickup_date: Optional[str] = None
    
    def get_dimensional_weight_kg(self, carrier: str = 'ups') -> Optional[float]:
        if not self.dimensions:
            return None
        length, width, height = self.dimensions
        volume_cm3 = length * width * height
        return volume_cm3 / 5000
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.origin:
            data['origin'] = self.origin.to_dict()
        if self.destination:
            data['destination'] = self.destination.to_dict()
        return data


@dataclass
class EmissionResult:
    """Container for emission calculation results"""
    total_emissions_kg: float
    weight_used_kg: float
    is_dimensional: bool
    distance_km: float
    transport_mode: str
    emission_factor: float
    breakdown: List[Dict]
    package_info: PackageInfo
    
    def to_dict(self) -> dict:
        return {
            'total_emissions_kg': self.total_emissions_kg,
            'weight_used_kg': self.weight_used_kg,
            'is_dimensional': self.is_dimensional,
            'distance_km': self.distance_km,
            'transport_mode': self.transport_mode,
            'emission_factor': self.emission_factor,
            'breakdown': self.breakdown,
            'package_info': self.package_info.to_dict()
        }


# ============================================================================
# GEOCODING & DISTANCE CALCULATION
# ============================================================================

class DistanceCalculator:
    """Handles geocoding and distance calculations"""
    
    def __init__(self, user_agent: str = "wpi_greenboard"):
        self.geocoder = Nominatim(user_agent=user_agent)
        self.cache = {}
    
    def geocode_address(self, address: Address, max_retries: int = 3) -> Tuple[Optional[float], Optional[float]]:
        if address.latitude and address.longitude:
            return address.latitude, address.longitude
        
        addr_string = address.to_string()
        if addr_string in self.cache:
            return self.cache[addr_string]
        
        for attempt in range(max_retries):
            try:
                location = self.geocoder.geocode(addr_string, timeout=10)
                
                if location:
                    coords = (location.latitude, location.longitude)
                    self.cache[addr_string] = coords
                    print(f"  ✓ Geocoded: {address.city or address.postal_code} → {coords}")
                    return coords
                else:
                    # Try city + country (good for international with limited data)
                    if address.city and address.country:
                        fallback_string = f"{address.city}, {address.country}"
                        print(f"  🔍 Trying city+country: {fallback_string}")
                        location = self.geocoder.geocode(fallback_string, timeout=10)
                        if location:
                            coords = (location.latitude, location.longitude)
                            self.cache[addr_string] = coords
                            print(f"  ✓ Geocoded (city+country): {fallback_string} → {coords}")
                            return coords
                    
                    # Try postal code + country
                    if address.postal_code and address.country:
                        fallback_string = f"{address.postal_code}, {address.country}"
                        print(f"  🔍 Trying postal+country: {fallback_string}")
                        location = self.geocoder.geocode(fallback_string, timeout=10)
                        if location:
                            coords = (location.latitude, location.longitude)
                            self.cache[addr_string] = coords
                            print(f"  ✓ Geocoded (postal+country): {fallback_string} → {coords}")
                            return coords
                
                print(f"  ⚠️ Could not geocode: {addr_string}")
                return None, None
                
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Geocoding attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
                else:
                    print(f"  ❌ Geocoding failed after {max_retries} attempts: {e}")
                    return None, None
        
        return None, None
    
    def calculate_distance(self, origin: Address, destination: Address, 
                          service_type: str = 'ground') -> float:
        print("\n📍 Calculating distance...")
        
        origin_coords = self.geocode_address(origin)
        dest_coords = self.geocode_address(destination)
        
        if origin_coords[0] and dest_coords[0]:
            distance = geodesic(origin_coords, dest_coords).kilometers
            print(f"  ✓ Calculated distance: {distance:.2f} km ({distance * 0.621371:.2f} miles)")
            return distance
        
        print("  ⚠️ Using estimated distance (geocoding unavailable)")
        
        if origin.country and destination.country and origin.country != destination.country:
            return DEFAULT_DISTANCES['international']
        
        if 'air' in service_type.lower():
            return DEFAULT_DISTANCES['domestic_air']
        else:
            return DEFAULT_DISTANCES['domestic_ground']


# ============================================================================
# CARRIER ADAPTER INTERFACE
# ============================================================================

class CarrierAdapter(ABC):
    """Abstract base class for carrier-specific adapters"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        pass
    
    @abstractmethod
    def get_tracking_data(self, token: str, tracking_number: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def parse_tracking_data(self, tracking_data: Dict) -> Optional[PackageInfo]:
        pass
    
    @abstractmethod
    def get_transport_mode(self, service_code: str) -> str:
        pass


# ============================================================================
# UPS ADAPTER
# ============================================================================

class UPSAdapter(CarrierAdapter):
    """UPS-specific implementation"""
    
    SERVICE_TO_MODE = {
        '01': 'air_shorthaul',
        '02': 'air_shorthaul',
        '03': 'truck_average',
        '07': 'air_longhaul',
        '08': 'air_longhaul',
        '11': 'truck_average',
        '12': 'truck_average',
        '13': 'air_shorthaul',
        '14': 'air_shorthaul',
        '54': 'air_longhaul',
        '554': 'air_longhaul',  # UPS Express
        '59': 'air_shorthaul',
        '65': 'ocean_container',
        '93': 'truck_average',
        'default': 'truck_average'
    }
    
    def __init__(self, production: bool = False):
        self.production = production
        self.base_url = "https://onlinetools.ups.com" 
    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        token_url = f"{self.base_url}/security/v1/oauth/token"
        payload = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(
                token_url,
                data=payload,
                auth=(credentials['client_id'], credentials['client_secret'])
            )
            response.raise_for_status()
            print("✅ UPS: Successfully authenticated")
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"❌ UPS authentication error: {e}")
            return None
    
    def get_tracking_data(self, token: str, tracking_number: str) -> Optional[Dict]:
        track_url = f"{self.base_url}/api/track/v1/details/{tracking_number}"
        headers = {
            "Authorization": f"Bearer {token}",
            "transId": str(uuid.uuid4()),
            "transactionSrc": "wpi_greenboard"
        }
        
        try:
            response = requests.get(track_url, headers=headers)
            response.raise_for_status()
            print(f"✅ UPS: Retrieved tracking data for {tracking_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ UPS tracking error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def parse_tracking_data(self, tracking_data: Dict) -> Optional[PackageInfo]:
        try:
            # Navigate to package level
            if 'trackResponse' in tracking_data:
                shipment = tracking_data['trackResponse']['shipment'][0]
                package = shipment.get('package', [{}])[0]
            elif 'TrackResponse' in tracking_data:
                shipment = tracking_data['TrackResponse']['Shipment']
                package = shipment.get('Package', [{}])[0]
            else:
                print(f"❌ Unknown UPS response structure")
                return None
            
            # Extract weight
            weight_kg = None
            weight_lb = None
            
            if 'weight' in package:
                weight_data = package['weight']
                unit = weight_data.get('unitOfMeasurement', 'LBS').upper()
                weight_value = float(weight_data.get('weight', 5.0))
                
                if unit == 'KGS':
                    weight_kg = weight_value
                else:  # LBS
                    weight_lb = weight_value
                    weight_kg = weight_lb * 0.453592
                    
            print(f"Parsed weight: {weight_kg:.2f} kg ({(weight_kg * 2.20462):.2f} lbs)")

            # Extract addresses
            addresses = package.get('packageAddress', [])
            origin = None
            destination = None
            
            for addr in addresses:
                addr_type = addr.get('type', '').upper()
                address_data = addr.get('address', {})
                
                parsed_addr = Address(
                    city=address_data.get('city'),
                    state=address_data.get('stateProvince') or address_data.get('stateProvinceCode'),
                    postal_code=address_data.get('postalCode'),
                    country=address_data.get('countryCode') or address_data.get('country', 'US')
                )
                
                if addr_type == 'ORIGIN':
                    origin = parsed_addr
                    print(f"  ✓ Origin: {origin.city}, {origin.country}")
                elif addr_type == 'DESTINATION':
                    destination = parsed_addr
                    print(f"  ✓ Destination: {destination.city}, {destination.country}")
            
            # Service information
            service = package.get('service', {})
            service_code = service.get('code', '03')
            service_desc = service.get('description', 'Ground')
            
            # Tracking number
            tracking_num = package.get('trackingNumber', 'Unknown')
            
            return PackageInfo(
                tracking_number=tracking_num,
                weight_kg=weight_kg,
                origin=origin,
                destination=destination,
                service_code=service_code,
                service_description=service_desc,
                carrier='UPS'
            )
            
        except Exception as e:
            print(f"❌ Error parsing UPS data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_transport_mode(self, service_code: str) -> str:
        return self.SERVICE_TO_MODE.get(service_code, self.SERVICE_TO_MODE['default'])


# ============================================================================
# USPS ADAPTER
# ============================================================================

class USPSAdapter(CarrierAdapter):
    """USPS-specific implementation using API v3"""
    
    SERVICE_TO_MODE = {
        'PRIORITY': 'air_shorthaul',
        'PRIORITY_EXPRESS': 'air_shorthaul',
        'FIRST_CLASS': 'truck_average',
        'PARCEL_SELECT': 'truck_average',
        'MEDIA_MAIL': 'truck_average',
        'PRIORITY_MAIL_EXPRESS_INTERNATIONAL': 'air_longhaul',
        'PRIORITY_MAIL_INTERNATIONAL': 'air_longhaul',
        'default': 'truck_average'
    }
    
    def __init__(self, production: bool = False):
        self.production = production
        self.base_url = "https://apis.usps.com"
    
    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        token_url = f"{self.base_url}/oauth2/v3/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": credentials['client_id'],
            "client_secret": credentials['client_secret']
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(token_url, json=payload, headers=headers)
            response.raise_for_status()
            print("✅ USPS: Successfully authenticated")
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"❌ USPS authentication error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def get_tracking_data(self, token: str, tracking_number: str) -> Optional[Dict]:
        track_url = f"{self.base_url}/tracking/v3/tracking/{tracking_number}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {"expand": "detail"}
        
        try:
            response = requests.get(track_url, headers=headers, params=params)
            response.raise_for_status()
            print(f"✅ USPS: Retrieved tracking data for {tracking_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ USPS tracking error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def parse_tracking_data(self, tracking_data: Dict) -> Optional[PackageInfo]:
        try:
            if 'trackResults' in tracking_data:
                track_info = tracking_data['trackResults'][0]
            elif 'TrackResults' in tracking_data:
                track_info = tracking_data['TrackResults']['TrackInfo']
            else:
                print(f"❌ Unknown USPS response structure")
                return None
            
            # Weight (often not provided by USPS)
            weight_kg = 2.27  # Default ~5 lbs
            if 'weight' in track_info:
                weight_kg = float(track_info['weight']) * 0.453592
            
            print(f"  ⚠️ USPS weight: {weight_kg:.2f} kg (estimated)")
            
            # Addresses
            origin = None
            destination = None
            
            if 'originCity' in track_info:
                origin = Address(
                    city=track_info.get('originCity'),
                    state=track_info.get('originState'),
                    postal_code=track_info.get('originZIP'),
                    country='US'
                )
            
            if 'destinationCity' in track_info:
                destination = Address(
                    city=track_info.get('destinationCity'),
                    state=track_info.get('destinationState'),
                    postal_code=track_info.get('destinationZIP'),
                    country='US'
                )
            
            service_type = track_info.get('class', 'PRIORITY').upper().replace(' ', '_')
            service_desc = track_info.get('classDescription', 'Priority Mail')
            tracking_num = track_info.get('trackingNumber', 'Unknown')
            
            print(f"  ✓ Service: {service_desc}")
            
            return PackageInfo(
                tracking_number=tracking_num,
                weight_kg=weight_kg,
                origin=origin,
                destination=destination,
                service_code=service_type,
                service_description=service_desc,
                carrier='USPS'
            )
            
        except Exception as e:
            print(f"❌ Error parsing USPS data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_transport_mode(self, service_code: str) -> str:
        return self.SERVICE_TO_MODE.get(service_code.upper(), self.SERVICE_TO_MODE['default'])


# ============================================================================
# FEDEX ADAPTER
# ============================================================================

class FedExAdapter(CarrierAdapter):
    """FedEx-specific implementation"""
    
    SERVICE_TO_MODE = {
        'FEDEX_GROUND': 'truck_average',
        'GROUND_HOME_DELIVERY': 'truck_average',
        'FEDEX_EXPRESS_SAVER': 'air_shorthaul',
        'FEDEX_2_DAY': 'air_shorthaul',
        'FEDEX_2_DAY_AM': 'air_shorthaul',
        'STANDARD_OVERNIGHT': 'air_shorthaul',
        'PRIORITY_OVERNIGHT': 'air_shorthaul',
        'FIRST_OVERNIGHT': 'air_shorthaul',
        'INTERNATIONAL_ECONOMY': 'air_longhaul',
        'INTERNATIONAL_PRIORITY': 'air_longhaul',
        'INTERNATIONAL_FIRST': 'air_longhaul',
        'SMART_POST': 'truck_average',
        'default': 'truck_average'
    }
    
    def __init__(self, production: bool = False):
        self.production = production
        self.base_url = ("https://apis.fedex.com" if production 
                        else "https://apis-sandbox.fedex.com")
    
    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        token_url = f"{self.base_url}/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": credentials['client_id'],
            "client_secret": credentials['client_secret']
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = requests.post(token_url, data=payload, headers=headers)
            response.raise_for_status()
            print("✅ FedEx: Successfully authenticated")
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"❌ FedEx authentication error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def get_tracking_data(self, token: str, tracking_number: str) -> Optional[Dict]:
        track_url = f"{self.base_url}/track/v1/trackingnumbers"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-locale": "en_US"
        }
        
        payload = {
            "includeDetailedScans": True,
            "trackingInfo": [{
                "trackingNumberInfo": {
                    "trackingNumber": tracking_number
                }
            }]
        }
        
        try:
            response = requests.post(track_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ FedEx: Retrieved tracking data for {tracking_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ FedEx tracking error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def parse_tracking_data(self, tracking_data: Dict) -> Optional[PackageInfo]:
        try:
            if 'output' not in tracking_data:
                print("❌ No output in FedEx response")
                return None
            
            complete_track_results = tracking_data['output']['completeTrackResults'][0]
            track_results = complete_track_results['trackResults'][0]
            
            # Weight
            weight_kg = 2.27  # Default
            if 'packageDetails' in track_results:
                package_details = track_results['packageDetails']
                if 'packageWeight' in package_details:
                    weight_info = package_details['packageWeight'][0]
                    weight_value = float(weight_info.get('value', 5.0))
                    unit = weight_info.get('unit', 'LB')
                    
                    if unit == 'KG':
                        weight_kg = weight_value
                    else:
                        weight_kg = weight_value * 0.453592
            
            print(f"  ✓ Weight: {weight_kg:.2f} kg")
            
            # Addresses
            origin = None
            destination = None
            
            if 'shipperInformation' in track_results:
                shipper = track_results['shipperInformation']
                if 'address' in shipper:
                    addr = shipper['address']
                    origin = Address(
                        city=addr.get('city'),
                        state=addr.get('stateOrProvinceCode'),
                        postal_code=addr.get('postalCode'),
                        country=addr.get('countryCode', 'US')
                    )
            
            if 'recipientInformation' in track_results:
                recipient = track_results['recipientInformation']
                if 'address' in recipient:
                    addr = recipient['address']
                    destination = Address(
                        city=addr.get('city'),
                        state=addr.get('stateOrProvinceCode'),
                        postal_code=addr.get('postalCode'),
                        country=addr.get('countryCode', 'US')
                    )
            
            service_detail = track_results.get('serviceDetail', {})
            service_code = service_detail.get('type', 'FEDEX_GROUND')
            service_desc = service_detail.get('description', 'FedEx Ground')
            tracking_num = track_results.get('trackingNumber', 'Unknown')
            
            print(f"  ✓ Service: {service_desc}")
            
            return PackageInfo(
                tracking_number=tracking_num,
                weight_kg=weight_kg,
                origin=origin,
                destination=destination,
                service_code=service_code,
                service_description=service_desc,
                carrier='FedEx'
            )
            
        except Exception as e:
            print(f"❌ Error parsing FedEx data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_transport_mode(self, service_code: str) -> str:
        return self.SERVICE_TO_MODE.get(service_code.upper(), self.SERVICE_TO_MODE['default'])


# ============================================================================
# DHL ADAPTER
# ============================================================================

class DHLAdapter(CarrierAdapter):
    """DHL-specific implementation"""
    
    SERVICE_TO_MODE = {
        'EXPRESS_WORLDWIDE': 'air_longhaul',
        'EXPRESS_12:00': 'air_longhaul',
        'EXPRESS_9:00': 'air_longhaul',
        'EXPRESS_EASY': 'air_longhaul',
        'ECONOMY_SELECT': 'air_longhaul',
        'GROUND': 'truck_average',
        'default': 'air_longhaul'
    }
    
    def __init__(self, production: bool = False):
        self.production = production
        self.base_url = "https://api.dhl.com" 
    
    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        token_url = f"{self.base_url}/auth/v4/accesstoken"
        
        # Create base64 encoded auth string
        auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }
        
        params = {
            "grant_type": "client_credentials",
            "response_type": "access_token"
        }
        
        try:
            response = requests.post(token_url, headers=headers, params=params)
            response.raise_for_status()
            print("✅ DHL: Successfully authenticated")
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"❌ DHL authentication error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def get_tracking_data(self, token: str, tracking_number: str) -> Optional[Dict]:
        track_url = f"{self.base_url}/track/shipments"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {"trackingNumber": tracking_number}
        
        try:
            response = requests.get(track_url, headers=headers, params=params)
            response.raise_for_status()
            print(f"✅ DHL: Retrieved tracking data for {tracking_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ DHL tracking error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return None
    
    def parse_tracking_data(self, tracking_data: Dict) -> Optional[PackageInfo]:
        try:
            if 'shipments' not in tracking_data:
                print("❌ No shipments in DHL response")
                return None
            
            shipment = tracking_data['shipments'][0]
            
            # Weight
            weight_kg = 2.27  # Default
            if 'details' in shipment and 'weight' in shipment['details']:
                weight_info = shipment['details']['weight']
                weight_value = float(weight_info.get('value', 5.0))
                unit = weight_info.get('unitText', 'kg')
                
                if unit.lower() == 'lb':
                    weight_kg = weight_value * 0.453592
                else:
                    weight_kg = weight_value
            
            print(f"  ✓ Weight: {weight_kg:.2f} kg")
            
            # Addresses
            origin = None
            destination = None
            
            if 'origin' in shipment:
                origin_info = shipment['origin']
                if 'address' in origin_info:
                    addr = origin_info['address']
                    origin = Address(
                        city=addr.get('cityName'),
                        state=addr.get('provinceCode'),
                        postal_code=addr.get('postalCode'),
                        country=addr.get('countryCode', 'US')
                    )
            
            if 'destination' in shipment:
                dest_info = shipment['destination']
                if 'address' in dest_info:
                    addr = dest_info['address']
                    destination = Address(
                        city=addr.get('cityName'),
                        state=addr.get('provinceCode'),
                        postal_code=addr.get('postalCode'),
                        country=addr.get('countryCode', 'US')
                    )
            
            service_code = shipment.get('service', {}).get('code', 'EXPRESS_WORLDWIDE')
            service_desc = shipment.get('service', {}).get('name', 'Express Worldwide')
            tracking_num = shipment.get('id', 'Unknown')
            
            print(f"  ✓ Service: {service_desc}")
            
            return PackageInfo(
                tracking_number=tracking_num,
                weight_kg=weight_kg,
                origin=origin,
                destination=destination,
                service_code=service_code,
                service_description=service_desc,
                carrier='DHL'
            )
            
        except Exception as e:
            print(f"❌ Error parsing DHL data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_transport_mode(self, service_code: str) -> str:
        return self.SERVICE_TO_MODE.get(service_code.upper(), self.SERVICE_TO_MODE['default'])


# ============================================================================
# CARRIER FACTORY
# ============================================================================

class CarrierFactory:
    """Factory for creating carrier adapters"""
    
    _adapters = {
        'ups': UPSAdapter,
        'usps': USPSAdapter,
        'fedex': FedExAdapter,
        'dhl': DHLAdapter,
    }
    
    @classmethod
    def create_adapter(cls, carrier: str, **kwargs) -> CarrierAdapter:
        carrier_lower = carrier.lower()
        if carrier_lower not in cls._adapters:
            raise ValueError(
                f"Unsupported carrier: {carrier}. "
                f"Supported carriers: {', '.join(cls._adapters.keys())}"
            )
        return cls._adapters[carrier_lower](**kwargs)
    
    @classmethod
    def register_adapter(cls, carrier: str, adapter_class: type):
        """Register a custom carrier adapter"""
        cls._adapters[carrier.lower()] = adapter_class
    
    @classmethod
    def list_supported_carriers(cls) -> List[str]:
        """Get list of all supported carriers"""
        return list(cls._adapters.keys())


# ============================================================================
# EMISSIONS CALCULATOR
# ============================================================================

class EmissionsCalculator:
    """Core emissions calculation engine"""
    
    def __init__(self):
        self.distance_calculator = DistanceCalculator()
    
    def calculate_emissions(self, weight_kg: float, distance_km: float,
                          transport_mode: str = 'truck_average') -> float:
        """
        Calculate emissions for a given weight and distance.
        
        Args:
            weight_kg: Package weight in kilograms
            distance_km: Distance in kilometers
            transport_mode: Transport mode key from EMISSION_FACTORS
        
        Returns:
            Emissions in kg CO2e
        """
        weight_tonnes = weight_kg / 1000
        emission_factor = EMISSION_FACTORS['tonne_km'][transport_mode]
        tonne_km = weight_tonnes * distance_km
        emissions_kg = tonne_km * emission_factor
        return emissions_kg
    
    def calculate_from_package_info(self, package_info: PackageInfo) -> Optional[EmissionResult]:
        """
        Calculate complete emissions breakdown from package information.
        
        Args:
            package_info: PackageInfo object with tracking data
        
        Returns:
            EmissionResult with detailed breakdown
        """
        # Determine chargeable weight
        weight_kg = package_info.weight_kg
        is_dimensional = False
        
        if package_info.dimensions:
            dim_weight = package_info.get_dimensional_weight_kg(package_info.carrier)
            if dim_weight and dim_weight > weight_kg:
                weight_kg = dim_weight
                is_dimensional = True
                print(f"📦 Using dimensional weight: {weight_kg:.2f} kg")
        
        # Check for address information
        if not package_info.origin or not package_info.destination:
            print("⚠️ Missing address information")
            return None
        
        # Calculate distance
        distance_km = self.distance_calculator.calculate_distance(
            package_info.origin,
            package_info.destination,
            package_info.service_description or 'ground'
        )
        
        # Get transport mode
        adapter = CarrierFactory.create_adapter(package_info.carrier.lower())
        transport_mode = adapter.get_transport_mode(package_info.service_code or '')
        
        # Calculate main transit emissions
        emission_factor = EMISSION_FACTORS['tonne_km'][transport_mode]
        main_emissions = self.calculate_emissions(weight_kg, distance_km, transport_mode)
        
        breakdown = [{
            'segment': 'Main Transit',
            'mode': transport_mode,
            'distance_km': distance_km,
            'weight_kg': weight_kg,
            'emission_factor': emission_factor,
            'emissions_kg': main_emissions
        }]
        
        total_emissions = main_emissions
        
        # Add last-mile delivery if not already included
        if transport_mode != 'last_mile':
            last_mile_distance = DEFAULT_DISTANCES['last_mile']
            last_mile_emissions = self.calculate_emissions(
                weight_kg, last_mile_distance, 'last_mile'
            )
            total_emissions += last_mile_emissions
            
            breakdown.append({
                'segment': 'Last Mile Delivery',
                'mode': 'last_mile',
                'distance_km': last_mile_distance,
                'weight_kg': weight_kg,
                'emission_factor': EMISSION_FACTORS['tonne_km']['last_mile'],
                'emissions_kg': last_mile_emissions
            })
        
        return EmissionResult(
            total_emissions_kg=total_emissions,
            weight_used_kg=weight_kg,
            is_dimensional=is_dimensional,
            distance_km=distance_km,
            transport_mode=transport_mode,
            emission_factor=emission_factor,
            breakdown=breakdown,
            package_info=package_info
        )


# ============================================================================
# MAIN INTERFACE
# ============================================================================

def calculate_package_emissions(carrier: str, tracking_number: str,
                               credentials: Dict[str, str],
                               dimensions: Optional[Tuple[float, float, float]] = None,
                               **adapter_kwargs) -> Optional[EmissionResult]:
    """
    Universal function to calculate emissions for any supported carrier.
    
    Args:
        carrier: Carrier name (ups, usps, fedex, dhl)
        tracking_number: Package tracking number
        credentials: Authentication credentials (carrier-specific)
        dimensions: Optional package dimensions (L, W, H in cm)
        **adapter_kwargs: Additional carrier-specific arguments
    
    Returns:
        EmissionResult with calculation details or None if failed
    
    Example:
        result = calculate_package_emissions(
            carrier='ups',
            tracking_number='1Z999AA10123456784',
            credentials={
                'client_id': 'your_client_id',
                'client_secret': 'your_client_secret'
            },
            dimensions=(30, 20, 15)
        )
    """
    print(f"\n{'='*70}")
    print(f"🌱 WPI Greenboard - Package Emissions Calculator")
    print(f"Carrier: {carrier.upper()}")
    print(f"Tracking #: {tracking_number}")
    print(f"{'='*70}\n")
    
    # Create carrier adapter
    try:
        adapter = CarrierFactory.create_adapter(carrier, **adapter_kwargs)
    except ValueError as e:
        print(f"❌ {e}")
        return None
    
    # Step 1: Authentication
    print(f"🔐 Step 1: Authenticating with {carrier.upper()}...")
    token = adapter.authenticate(credentials)
    if not token:
        return None
    
    # Step 2: Fetch tracking data
    print(f"\n📦 Step 2: Fetching tracking data...")
    tracking_data = adapter.get_tracking_data(token, tracking_number)
    if not tracking_data:
        return None
    
    # Step 3: Parse package information
    print(f"\n📄 Step 3: Parsing package information...")
    package_info = adapter.parse_tracking_data(tracking_data)
    if not package_info:
        return None
    
    # Add dimensions if provided
    if dimensions:
        package_info.dimensions = dimensions
        print(f"  📏 Added dimensions: {dimensions[0]}x{dimensions[1]}x{dimensions[2]} cm")
    
    # Step 4: Calculate emissions
    print(f"\n🌍 Step 4: Calculating carbon emissions...")
    calculator = EmissionsCalculator()
    result = calculator.calculate_from_package_info(package_info)
    
    if not result:
        return None
    
    # Display final results
    print(f"\n{'='*70}")
    print(f"📊 CARBON EMISSIONS REPORT")
    print(f"{'='*70}\n")
    
    print(f"Package Details:")
    print(f"  • Tracking: {package_info.tracking_number}")
    print(f"  • Carrier: {package_info.carrier}")
    print(f"  • Service: {package_info.service_description}")
    print(f"  • Weight: {result.weight_used_kg:.2f} kg ({result.weight_used_kg * 2.20462:.2f} lbs)")
    if result.is_dimensional:
        print(f"    ⚠️  Dimensional weight applied")
    
    print(f"\nRoute Information:")
    if package_info.origin:
        origin_str = f"{package_info.origin.city}, {package_info.origin.state or package_info.origin.country}"
        print(f"  • From: {origin_str}")
    if package_info.destination:
        dest_str = f"{package_info.destination.city}, {package_info.destination.state or package_info.destination.country}"
        print(f"  • To: {dest_str}")
    print(f"  • Distance: {result.distance_km:.0f} km ({result.distance_km * 0.621371:.0f} miles)")
    print(f"  • Transport Mode: {result.transport_mode}")
    
    print(f"\nEmissions Breakdown:")
    for segment in result.breakdown:
        print(f"  • {segment['segment']}: {segment['emissions_kg']:.4f} kg CO2e")
        print(f"    ({segment['distance_km']:.0f} km @ {segment['emission_factor']:.3f} kg/tonne-km)")
    
    print(f"\n{'─'*70}")
    print(f"🌱 TOTAL EMISSIONS: {result.total_emissions_kg:.4f} kg CO2e")
    print(f"{'='*70}\n")
    
    # Environmental context
    trees_to_offset = result.total_emissions_kg / 21  # ~21 kg CO2 per tree per year
    miles_driven = result.total_emissions_kg / 0.404  # ~0.404 kg CO2 per mile
    
    print(f"Environmental Context:")
    print(f"  🌳 Trees needed (1 year): {trees_to_offset:.2f}")
    print(f"  🚗 Equivalent to driving: {miles_driven:.1f} miles")
    print(f"{'='*70}\n")
    
    return result


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_supported_carriers() -> List[str]:
    """Get list of all supported carriers"""
    return CarrierFactory.list_supported_carriers()


def save_emissions_report(result: EmissionResult, filename: str = 'emissions_report.json'):
    """
    Save emissions calculation results to a JSON file.
    
    Args:
        result: EmissionResult object
        filename: Output filename
    """
    output = {
        'tracking_number': result.package_info.tracking_number,
        'carrier': result.package_info.carrier,
        'service': result.package_info.service_description,
        'total_emissions_kg': result.total_emissions_kg,
        'weight_kg': result.weight_used_kg,
        'is_dimensional_weight': result.is_dimensional,
        'distance_km': result.distance_km,
        'transport_mode': result.transport_mode,
        'emission_factor': result.emission_factor,
        'breakdown': result.breakdown,
        'origin': result.package_info.origin.to_dict() if result.package_info.origin else None,
        'destination': result.package_info.destination.to_dict() if result.package_info.destination else None,
        'environmental_equivalents': {
            'trees_to_offset_1_year': result.total_emissions_kg / 21,
            'miles_driven_equivalent': result.total_emissions_kg / 0.404
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Report saved to {filename}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("🌱 WPI Greenboard - Universal Emissions Calculator\n")
    print(f"Supported carriers: {', '.join(get_supported_carriers())}\n")
    
    # Example 1: UPS Package
    print("Example 1: UPS International Express")
    print("-" * 70)
    
    ups_result = calculate_package_emissions(
        carrier='ups',
        tracking_number='1ZA81H440313373222',  # Your actual tracking number
        credentials={
           'client_id': 'HCTsyp8JsmGuiOYCkxpZAak9ZusNbA8Me9d1k5g7rmivxpoC',
           'client_secret': 'bbUGGCg1q66AuEeGV66EjhcbG6GNtOGYTb1r5vqAxssUaBsovaQIKPiTWHHpAGZV'
        },
        production=False  # Use test environment
    )
    
    if ups_result:
        save_emissions_report(ups_result, 'ups_emissions_report.json')
    
    # Example 2: FedEx Package (uncomment when you have credentials)
    print("\n\nExample 2: FedEx Ground")
    print("-" * 70)
    
    fedex_result = calculate_package_emissions(
        carrier='fedex',
        tracking_number='484078159554', # SK sample tracking number
        credentials={
            'client_id': 'YOUR_FEDEX_CLIENT_ID',
            'client_secret': 'YOUR_FEDEX_CLIENT_SECRET'
        },
        production=False
    )
    
    if fedex_result:
        save_emissions_report(fedex_result, 'fedex_emissions_report.json')
    
    # Example 3: USPS Package (uncomment when you have credentials)
    print("\n\nExample 3: USPS Priority Mail")
    print("-" * 70)
    
    usps_result = calculate_package_emissions(
        carrier='usps',
        tracking_number='9234690390475000528723',
        credentials={
            'client_id': 'vrBISZnb8yn4KTNm0SA0UAA4yqlDfGdEFHkfARJzWgizAzGq',
            'client_secret': '13b8Ius4epIhNbIlz2s9KIlAOT0JVkSqnBGjtD6q5rnW5TRHrchLZYBfwUAaM51Y'
        }
    )
    
    if usps_result:
        save_emissions_report(usps_result, 'usps_emissions_report.json')
    
    # Example 4: DHL Package (uncomment when you have credentials)
    print("\n\nExample 4: DHL Express Worldwide")
    print("-" * 70)
    
    dhl_result = calculate_package_emissions(
        carrier='dhl',
        tracking_number='1234567890',
        credentials={
            'client_id': 'YOUR_DHL_CONSUMER_KEY',
            'client_secret': 'YOUR_DHL_SECRET_KEY'
        },
        production=False
    )
    print(dhl_result)
    # 
    # if dhl_result:
    #     save_emissions_report(dhl_result, 'dhl_emissions_report.json')