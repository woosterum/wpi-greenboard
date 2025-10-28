from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List

from .database import get_session
from .models import Package, Carrier, Emission, PackageRead

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("/", response_model=List[Package])
async def get_packages(
    skip: int = Query(0, ge=0),
    entries_per_page: int = Query(100, le=1000),
    session: Session = Depends(get_session)
):
    """Get all packages with carrier info."""
    statement = (
        select(
            Package.package_id,
            Package.tracking_number,
            Carrier.carrier_name,
            Package.service_type,
            Package.date_shipped,
            Package.total_emissions_kg,
            Package.distance_traveled
        )
        .join(Carrier, Package.carrier_id == Carrier.carrier_id, isouter=True)
        .offset(skip)
        .limit(entries_per_page)
    )
    
    results = session.exec(statement).all()
    
    return [
        PackageRead(
            package_id=r[0],
            tracking_number=r[1],
            carrier_name=r[2],
            service_type=r[3],
            date_shipped=r[4],
            total_emissions_kg=r[5],
            distance_traveled=r[6]
        )
        for r in results
    ]


@router.get("/{package_id}", response_model=PackageRead)
async def get_package(
    package_id: int,
    session: Session = Depends(get_session)
):
    """Get single package by ID."""
    statement = (
        select(
            Package.package_id,
            Package.tracking_number,
            Carrier.carrier_name,
            Package.service_type,
            Package.date_shipped,
            Package.total_emissions_kg,
            Package.distance_traveled
        )
        .join(Carrier, Package.carrier_id == Carrier.carrier_id, isouter=True)
        .where(Package.package_id == package_id)
    )
    
    result = session.exec(statement).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return PackageRead(
        package_id=result[0],
        tracking_number=result[1],
        carrier_name=result[2],
        service_type=result[3],
        date_shipped=result[4],
        total_emissions_kg=result[5],
        distance_traveled=result[6]
    )


@router.get("/tracking/{tracking_number}", response_model=PackageRead)
async def get_package_by_tracking(
    tracking_number: str,
    session: Session = Depends(get_session)
):
    """Get package by tracking number."""
    statement = select(Package).where(Package.tracking_number == tracking_number)
    package = session.exec(statement).first()
    
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return await get_package(package.package_id, session)