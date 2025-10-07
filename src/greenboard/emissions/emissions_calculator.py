"""
Universal Package Delivery Carbon Emissions Calculator

Modular system supporting UPS, USPS, FedEx, DHL and other carriers.
Includes accurate geocoding for distance calculation.
"""

import requests
import uuid
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
            return None
    
    def parse_tracking_data(self, tracking_data: Dict) -> Optional[PackageInfo]:
        try:
            
            if 'trackResponse' in tracking_data:
                shipment = tracking_data['trackResponse']['shipment'][0]['package'][0]
            elif 'TrackResponse' in tracking_data:
                shipment = tracking_data['TrackResponse']['Shipment'][0]['Package'][0]
            else:
                raise KeyError("Unable to find shipment data")
            
            
            weight_kg = None
            weight_lb = None
            if 'PackageWeight' in shipment or 'packageWeight' in shipment or 'weight' in shipment:
                weight_data = shipment.get('PackageWeight') or shipment.get('packageWeight') or shipment.get('weight', {})
                if weight_data.get('unitOfMeasurement').lower() == 'lbs':
                    weight_lb = float(weight_data.get('Weight') or weight_data.get('weight', 0))
                if weight_data.get('unitOfMeasurement').lower() == 'kgs':
                    weight_kg = float(weight_data.get('Weight') or weight_data.get('weight', 0))
                if not weight_kg and weight_lb:
                    weight_kg = weight_lb * 0.453592
            print(f"Parsed weight: {weight_kg:.2f} kg")

            addresses = shipment.get('packageAddress') or shipment.get('Packageaddress', [])
            origin = None
            destination = None
            
            for addr in addresses:
                addr_type = (addr.get('Type', {}) or 
                           addr.get('type', {}))
                address_data = addr.get('Address') or addr.get('address', {})
                
                parsed_addr = Address(
                    street=address_data.get('AddressLine') or address_data.get('addressLine'),
                    city=address_data.get('City') or address_data.get('city'),
                    state=address_data.get('StateProvince') or address_data.get('stateProvince'),
                    postal_code=address_data.get('PostalCode') or address_data.get('postalCode'),
                    country=address_data.get('Country') or address_data.get('country', 'US')
                )
                
                if addr_type.lower() == 'origin':
                    origin = parsed_addr
                elif addr_type.lower() == 'destination':
                    destination = parsed_addr
            
            service = shipment.get('Service') or shipment.get('service', {})
            service_code = service.get('Code') or service.get('code', '03')
            service_desc = service.get('Description') or service.get('description', 'Ground')
            
            tracking_num = (shipment.get('TrackingNumber') or 
                          shipment.get('trackingNumber') or 
                          shipment.get('Package', {}).get('TrackingNumber', 'Unknown'))
            
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
            return None
    
    def get_transport_mode(self, service_code: str) -> str:
        return self.SERVICE_TO_MODE.get(service_code, self.SERVICE_TO_MODE['default'])


# ============================================================================
# CARRIER FACTORY
# ============================================================================

class CarrierFactory:
    """Factory for creating carrier adapters"""
    
    _adapters = {
        'ups': UPSAdapter,
    }
    
    @classmethod
    def create_adapter(cls, carrier: str, **kwargs) -> CarrierAdapter:
        carrier_lower = carrier.lower()
        if carrier_lower not in cls._adapters:
            raise ValueError(f"Unsupported carrier: {carrier}")
        return cls._adapters[carrier_lower](**kwargs)


# ============================================================================
# EMISSIONS CALCULATOR
# ============================================================================

class EmissionsCalculator:
    """Core emissions calculation engine"""
    
    def __init__(self):
        self.distance_calculator = DistanceCalculator()
    
    def calculate_emissions(self, weight_kg: float, distance_km: float,
                          transport_mode: str = 'truck_average') -> float:
        weight_tonnes = weight_kg / 1000
        emission_factor = EMISSION_FACTORS['tonne_km'][transport_mode]
        tonne_km = weight_tonnes * distance_km
        emissions_kg = tonne_km * emission_factor
        return emissions_kg
    
    def calculate_from_package_info(self, package_info: PackageInfo) -> Optional[EmissionResult]:
        weight_kg = package_info.weight_kg
        is_dimensional = False
        
        if package_info.dimensions:
            dim_weight = package_info.get_dimensional_weight_kg(package_info.carrier)
            if dim_weight and dim_weight > weight_kg:
                weight_kg = dim_weight
                is_dimensional = True
                print(f"📦 Using dimensional weight: {weight_kg:.2f} kg")
        
        if not package_info.origin or not package_info.destination:
            print("⚠️ Missing address information")
            return None
        
        distance_km = self.distance_calculator.calculate_distance(
            package_info.origin,
            package_info.destination,
            package_info.service_description or 'ground'
        )
        
        adapter = CarrierFactory.create_adapter(package_info.carrier.lower())
        transport_mode = adapter.get_transport_mode(package_info.service_code or '')
        
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
    Universal function to calculate emissions for any carrier.
    """
    print(f"\n{'='*70}")
    print(f"WPI Greenboard - Package Emissions Calculator")
    print(f"Carrier: {carrier.upper()}")
    print(f"{'='*70}\n")
    
    try:
        adapter = CarrierFactory.create_adapter(carrier, **adapter_kwargs)
    except ValueError as e:
        print(f"❌ {e}")
        return None
    
    print(f"🔐 Step 1: Authenticating with {carrier.upper()}...")
    token = adapter.authenticate(credentials)
    if not token:
        return None
    
    print(f"\n📦 Step 2: Fetching tracking data...")
    tracking_data = adapter.get_tracking_data(token, tracking_number)
    if not tracking_data:
        return None
    
    print(f"\n📄 Step 3: Parsing package information...")
    package_info = adapter.parse_tracking_data(tracking_data)
    if not package_info:
        return None
    
    if dimensions:
        package_info.dimensions = dimensions
    
    print(f"\n🌍 Step 4: Calculating carbon emissions...")
    calculator = EmissionsCalculator()
    result = calculator.calculate_from_package_info(package_info)
    
    if result:
        print(f"\n{'='*70}")
        print(f"CARBON EMISSIONS REPORT")
        print(f"{'='*70}\n")
        print(f"🌱 TOTAL EMISSIONS: {result.total_emissions_kg:.4f} kg CO2e")
        print(f"{'='*70}\n")
    
    return result


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # UPS Example
    result = calculate_package_emissions(
        carrier='ups',
        tracking_number='1ZA81H440313373222',
        credentials={
            'client_id': 'HCTsyp8JsmGuiOYCkxpZAak9ZusNbA8Me9d1k5g7rmivxpoC',
            'client_secret': 'bbUGGCg1q66AuEeGV66EjhcbG6GNtOGYTb1r5vqAxssUaBsovaQIKPiTWHHpAGZV'
        },
        dimensions=(50, 40, 30),  # L, W, H in cm
        production=True
    )
    
    # Save results if needed
    if result:
        output = {
            'tracking_number': result.package_info.tracking_number,
            'carrier': result.package_info.carrier,
            'total_emissions_kg': result.total_emissions_kg,
            'weight_kg': result.weight_used_kg,
            'distance_km': result.distance_km,
            'transport_mode': result.transport_mode,
            'breakdown': result.breakdown
        }
        
        with open('emissions_report.json', 'w') as f:
            json.dump(output, f, indent=2)