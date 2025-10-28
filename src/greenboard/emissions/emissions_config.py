"""
Centralized Emissions Configuration for All Carriers

This module defines standardized service types and their emission factors
that can be used across UPS, FedEx, USPS, DHL, and other carriers.

Emission factors are in kg CO2e per tonne-km (kilogram of CO2 equivalent 
per tonne of goods per kilometer traveled).

Sources:
- EPA SmartWay Transport Partnership
- GLEC Framework (Global Logistics Emissions Council)
- European Environment Agency (EEA)
"""

from typing import Dict, Optional
from enum import Enum


# ============================================================================
# STANDARDIZED SERVICE TYPES
# ============================================================================

class ServiceType(Enum):
    """Standardized service types across all carriers"""
    
    # Ground Services
    GROUND_STANDARD = "ground_standard"           # Standard ground, 5-7 days
    GROUND_ECONOMY = "ground_economy"             # Economy ground, 7+ days
    GROUND_EXPEDITED = "ground_expedited"         # Expedited ground, 3-4 days
    GROUND_2DAY = "ground_2day"                   # 2-day ground service
    
    # Air Services - Domestic
    AIR_NEXT_DAY = "air_next_day"                 # Next day air
    AIR_NEXT_DAY_EARLY = "air_next_day_early"     # Next day air early AM
    AIR_NEXT_DAY_SAVER = "air_next_day_saver"     # Next day air saver
    AIR_2DAY = "air_2day"                         # 2nd day air
    AIR_2DAY_EARLY = "air_2day_early"             # 2nd day air AM
    AIR_3DAY = "air_3day"                         # 3 day select
    
    # Air Services - International
    AIR_INTERNATIONAL_EXPRESS = "air_intl_express"     # Worldwide express
    AIR_INTERNATIONAL_EXPEDITED = "air_intl_expedited" # Worldwide expedited
    AIR_INTERNATIONAL_SAVER = "air_intl_saver"         # International saver
    
    # Ocean/Maritime
    OCEAN_STANDARD = "ocean_standard"             # Standard ocean freight
    OCEAN_EXPEDITED = "ocean_expedited"           # Expedited ocean freight
    
    # Rail
    RAIL_STANDARD = "rail_standard"               # Standard rail freight
    
    # Last Mile
    LAST_MILE_STANDARD = "last_mile_standard"     # Standard last mile delivery
    LAST_MILE_URBAN = "last_mile_urban"           # Urban last mile (more stops)
    
    # Specialized
    FREIGHT_LTL = "freight_ltl"                   # Less than truckload freight
    FREIGHT_FTL = "freight_ftl"                   # Full truckload freight
    MAIL_INNOVATIONS = "mail_innovations"         # Hybrid carrier/postal
    SUREPOST = "surepost"                         # UPS SurePost (hybrid)


# ============================================================================
# EMISSION FACTORS (kg CO2e per tonne-km)
# ============================================================================

EMISSION_FACTORS = {
    # Ground Services
    # Speed increases emissions due to less efficient routing and fewer consolidations
    ServiceType.GROUND_ECONOMY: 0.062,        # Most efficient, optimized long-haul
    ServiceType.GROUND_STANDARD: 0.127,       # Standard trucking average
    ServiceType.GROUND_EXPEDITED: 0.180,      # Less consolidation, more direct
    ServiceType.GROUND_2DAY: 0.220,           # Faster routing, less efficient
    
    # Air Services - Domestic (short-haul, <1500 km)
    # Faster services may use less efficient routes/planes
    ServiceType.AIR_NEXT_DAY_EARLY: 0.90,     # Early AM requires positioning flights
    ServiceType.AIR_NEXT_DAY: 0.82,           # Standard next day air
    ServiceType.AIR_NEXT_DAY_SAVER: 0.78,     # Slightly more consolidated
    ServiceType.AIR_2DAY: 0.75,               # More time for consolidation
    ServiceType.AIR_2DAY_EARLY: 0.77,         # Early AM, slightly less efficient
    ServiceType.AIR_3DAY: 0.72,               # More consolidation opportunities
    
    # Air Services - International (long-haul, >1500 km)
    # Long-haul flights are more fuel-efficient per km
    ServiceType.AIR_INTERNATIONAL_EXPRESS: 0.75,    # Express international
    ServiceType.AIR_INTERNATIONAL_EXPEDITED: 0.69,  # Standard international air
    ServiceType.AIR_INTERNATIONAL_SAVER: 0.65,      # Deferred international
    
    # Ocean/Maritime
    ServiceType.OCEAN_STANDARD: 0.010,        # Modern container ship
    ServiceType.OCEAN_EXPEDITED: 0.015,       # Faster ships use more fuel
    
    # Rail
    ServiceType.RAIL_STANDARD: 0.022,         # Electric or diesel rail
    
    # Last Mile Delivery
    ServiceType.LAST_MILE_STANDARD: 0.200,    # Standard last mile
    ServiceType.LAST_MILE_URBAN: 0.307,       # Urban delivery (many stops, congestion)
    
    # Freight
    ServiceType.FREIGHT_LTL: 0.150,           # Less than truckload
    ServiceType.FREIGHT_FTL: 0.062,           # Full truckload (most efficient)
    
    # Specialized/Hybrid
    ServiceType.MAIL_INNOVATIONS: 0.180,      # Hybrid carrier/USPS
    ServiceType.SUREPOST: 0.180,              # UPS SurePost (hybrid)
}


# ============================================================================
# CARRIER SERVICE CODE MAPPINGS
# ============================================================================

class CarrierServiceMapper:
    """Maps carrier-specific service codes to standardized ServiceType"""
    
    # UPS Service Codes
    UPS_SERVICE_MAP = {
        '01': ServiceType.AIR_NEXT_DAY,
        '02': ServiceType.AIR_2DAY,
        '03': ServiceType.GROUND_STANDARD,
        '07': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        '08': ServiceType.AIR_INTERNATIONAL_EXPEDITED,
        '11': ServiceType.GROUND_STANDARD,
        '12': ServiceType.AIR_3DAY,
        '13': ServiceType.AIR_NEXT_DAY_SAVER,
        '14': ServiceType.AIR_NEXT_DAY_EARLY,
        '54': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        '59': ServiceType.AIR_2DAY_EARLY,
        '65': ServiceType.AIR_INTERNATIONAL_SAVER,
        '70': ServiceType.FREIGHT_LTL,
        '74': ServiceType.GROUND_ECONOMY,
        '82': ServiceType.GROUND_ECONOMY,
        '83': ServiceType.GROUND_ECONOMY,
        '93': ServiceType.SUREPOST,
        'M2': ServiceType.MAIL_INNOVATIONS,
        'M3': ServiceType.MAIL_INNOVATIONS,
        'M4': ServiceType.MAIL_INNOVATIONS,
        'M5': ServiceType.MAIL_INNOVATIONS,
        'M6': ServiceType.MAIL_INNOVATIONS,
    }
    
    # FedEx Service Codes (to be implemented)
    FEDEX_SERVICE_MAP = {
        'FEDEX_GROUND': ServiceType.GROUND_STANDARD,
        'GROUND_HOME_DELIVERY': ServiceType.GROUND_STANDARD,
        'FEDEX_EXPRESS_SAVER': ServiceType.AIR_3DAY,
        'FEDEX_2_DAY': ServiceType.AIR_2DAY,
        'FEDEX_2_DAY_AM': ServiceType.AIR_2DAY_EARLY,
        'STANDARD_OVERNIGHT': ServiceType.AIR_NEXT_DAY,
        'PRIORITY_OVERNIGHT': ServiceType.AIR_NEXT_DAY_EARLY,
        'FIRST_OVERNIGHT': ServiceType.AIR_NEXT_DAY_EARLY,
        'INTERNATIONAL_ECONOMY': ServiceType.AIR_INTERNATIONAL_SAVER,
        'INTERNATIONAL_PRIORITY': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        'INTERNATIONAL_FIRST': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        'FEDEX_FREIGHT_PRIORITY': ServiceType.FREIGHT_LTL,
        'FEDEX_FREIGHT_ECONOMY': ServiceType.FREIGHT_LTL,
        'FEDEX_FREIGHT': ServiceType.FREIGHT_FTL,
        'SMART_POST': ServiceType.MAIL_INNOVATIONS,
    }
    
    # USPS Service Codes (to be implemented)
    USPS_SERVICE_MAP = {
        'PRIORITY': ServiceType.AIR_2DAY,
        'PRIORITY_EXPRESS': ServiceType.AIR_NEXT_DAY,
        'FIRST_CLASS': ServiceType.GROUND_STANDARD,
        'PARCEL_SELECT': ServiceType.GROUND_ECONOMY,
        'MEDIA_MAIL': ServiceType.GROUND_ECONOMY,
        'PRIORITY_MAIL_EXPRESS_INTERNATIONAL': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        'PRIORITY_MAIL_INTERNATIONAL': ServiceType.AIR_INTERNATIONAL_EXPEDITED,
        'FIRST_CLASS_PACKAGE_INTERNATIONAL': ServiceType.GROUND_STANDARD,
    }
    
    # DHL Service Codes (to be implemented)
    DHL_SERVICE_MAP = {
        'EXPRESS_WORLDWIDE': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        'EXPRESS_12:00': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        'EXPRESS_9:00': ServiceType.AIR_INTERNATIONAL_EXPRESS,
        'EXPRESS_EASY': ServiceType.AIR_INTERNATIONAL_EXPEDITED,
        'ECONOMY_SELECT': ServiceType.AIR_INTERNATIONAL_SAVER,
        'GROUND': ServiceType.GROUND_STANDARD,
    }
    
    @classmethod
    def get_service_type(cls, carrier: str, service_code: str) -> ServiceType:
        """
        Get standardized service type from carrier-specific service code.
        
        Args:
            carrier: Carrier name (ups, fedex, usps, dhl)
            service_code: Carrier-specific service code
            
        Returns:
            StandardizedServiceType enum value
        """
        carrier_lower = carrier.lower().strip()
        service_code_upper = service_code.upper().strip()
        
        if carrier_lower == 'ups':
            return cls.UPS_SERVICE_MAP.get(service_code, ServiceType.GROUND_STANDARD)
        elif carrier_lower == 'fedex':
            return cls.FEDEX_SERVICE_MAP.get(service_code_upper, ServiceType.GROUND_STANDARD)
        elif carrier_lower == 'usps':
            return cls.USPS_SERVICE_MAP.get(service_code_upper, ServiceType.GROUND_STANDARD)
        elif carrier_lower == 'dhl':
            return cls.DHL_SERVICE_MAP.get(service_code_upper, ServiceType.GROUND_STANDARD)
        else:
            return ServiceType.GROUND_STANDARD
    
    @classmethod
    def get_emission_factor(cls, carrier: str, service_code: str) -> float:
        """
        Get emission factor for a carrier's service code.
        
        Args:
            carrier: Carrier name
            service_code: Carrier-specific service code
            
        Returns:
            Emission factor in kg CO2e per tonne-km
        """
        service_type = cls.get_service_type(carrier, service_code)
        return EMISSION_FACTORS.get(service_type, EMISSION_FACTORS[ServiceType.GROUND_STANDARD])


# ============================================================================
# DISTANCE DEFAULTS (km)
# ============================================================================

DEFAULT_DISTANCES = {
    'domestic_ground': 1200,
    'domestic_air': 1500,
    'international': 5000,
    'last_mile': 10,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_service_description(service_type: ServiceType) -> str:
    """Get human-readable description of service type"""
    descriptions = {
        ServiceType.GROUND_STANDARD: "Standard Ground Shipping",
        ServiceType.GROUND_ECONOMY: "Economy Ground Shipping",
        ServiceType.GROUND_EXPEDITED: "Expedited Ground Shipping",
        ServiceType.GROUND_2DAY: "2-Day Ground Shipping",
        ServiceType.AIR_NEXT_DAY: "Next Day Air",
        ServiceType.AIR_NEXT_DAY_EARLY: "Next Day Air Early AM",
        ServiceType.AIR_NEXT_DAY_SAVER: "Next Day Air Saver",
        ServiceType.AIR_2DAY: "2nd Day Air",
        ServiceType.AIR_2DAY_EARLY: "2nd Day Air Early AM",
        ServiceType.AIR_3DAY: "3 Day Select",
        ServiceType.AIR_INTERNATIONAL_EXPRESS: "International Express",
        ServiceType.AIR_INTERNATIONAL_EXPEDITED: "International Expedited",
        ServiceType.AIR_INTERNATIONAL_SAVER: "International Saver",
        ServiceType.OCEAN_STANDARD: "Standard Ocean Freight",
        ServiceType.OCEAN_EXPEDITED: "Expedited Ocean Freight",
        ServiceType.RAIL_STANDARD: "Rail Freight",
        ServiceType.LAST_MILE_STANDARD: "Last Mile Delivery",
        ServiceType.LAST_MILE_URBAN: "Urban Last Mile Delivery",
        ServiceType.FREIGHT_LTL: "Less Than Truckload Freight",
        ServiceType.FREIGHT_FTL: "Full Truckload Freight",
        ServiceType.MAIL_INNOVATIONS: "Mail Innovations",
        ServiceType.SUREPOST: "SurePost",
    }
    return descriptions.get(service_type, "Standard Shipping")


def is_air_service(service_type: ServiceType) -> bool:
    """Check if service type is air-based"""
    air_services = {
        ServiceType.AIR_NEXT_DAY,
        ServiceType.AIR_NEXT_DAY_EARLY,
        ServiceType.AIR_NEXT_DAY_SAVER,
        ServiceType.AIR_2DAY,
        ServiceType.AIR_2DAY_EARLY,
        ServiceType.AIR_3DAY,
        ServiceType.AIR_INTERNATIONAL_EXPRESS,
        ServiceType.AIR_INTERNATIONAL_EXPEDITED,
        ServiceType.AIR_INTERNATIONAL_SAVER,
    }
    return service_type in air_services


def is_international(service_type: ServiceType) -> bool:
    """Check if service type is international"""
    intl_services = {
        ServiceType.AIR_INTERNATIONAL_EXPRESS,
        ServiceType.AIR_INTERNATIONAL_EXPEDITED,
        ServiceType.AIR_INTERNATIONAL_SAVER,
        ServiceType.OCEAN_STANDARD,
        ServiceType.OCEAN_EXPEDITED,
    }
    return service_type in intl_services


def get_default_distance(service_type: ServiceType) -> float:
    """Get default distance estimate for service type"""
    if is_international(service_type):
        return DEFAULT_DISTANCES['international']
    elif is_air_service(service_type):
        return DEFAULT_DISTANCES['domestic_air']
    else:
        return DEFAULT_DISTANCES['domestic_ground']


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Get emission factor for UPS Ground
    service_type = CarrierServiceMapper.get_service_type('ups', '03')
    emission_factor = EMISSION_FACTORS[service_type]
    print(f"UPS Ground (03): {service_type.value}")
    print(f"Emission Factor: {emission_factor} kg CO2e/tonne-km")
    print(f"Description: {get_service_description(service_type)}")
    
    print("\n" + "="*70)
    
    # Example: Compare emission factors for different speeds
    print("\nEmission Factor Comparison (kg CO2e/tonne-km):")
    print(f"Ground Economy:     {EMISSION_FACTORS[ServiceType.GROUND_ECONOMY]:.3f}")
    print(f"Ground Standard:    {EMISSION_FACTORS[ServiceType.GROUND_STANDARD]:.3f}")
    print(f"Ground Expedited:   {EMISSION_FACTORS[ServiceType.GROUND_EXPEDITED]:.3f}")
    print(f"Ground 2-Day:       {EMISSION_FACTORS[ServiceType.GROUND_2DAY]:.3f}")
    print(f"Air 3-Day:          {EMISSION_FACTORS[ServiceType.AIR_3DAY]:.3f}")
    print(f"Air 2-Day:          {EMISSION_FACTORS[ServiceType.AIR_2DAY]:.3f}")
    print(f"Air Next Day:       {EMISSION_FACTORS[ServiceType.AIR_NEXT_DAY]:.3f}")
    print(f"Air Next Day Early: {EMISSION_FACTORS[ServiceType.AIR_NEXT_DAY_EARLY]:.3f}")
    
    print("\n" + "="*70)
    print("\n⚠️  Key Insight: Faster shipping = Higher emissions!")
    print("Next Day Air emits ~14x more CO2 than economy ground per tonne-km")
