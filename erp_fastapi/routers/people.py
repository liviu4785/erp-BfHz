from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.person import Person
from erp_fastapi.models.company import Company
from erp_fastapi.models.user import User
from erp_fastapi.schemas.person import PersonCreate, PersonUpdate, PersonOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/people", tags=["people"])


def _person_out(p: Person) -> PersonOut:
    return PersonOut(
        id=p.id, first_name=p.first_name, last_name=p.last_name,
        email=p.email, phone=p.phone, date_of_birth=p.date_of_birth,
        unique_identifier=p.unique_identifier, notes=p.notes,
        company_ids=[c.id for c in p.companies],
    )


@router.get("/", response_model=List[PersonOut])
def list_people(q: str = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(Person)
    if q:
        query = query.filter(
            (Person.first_name.ilike(f"%{q}%")) | (Person.last_name.ilike(f"%{q}%"))
        )
    return [_person_out(p) for p in query.order_by(Person.last_name).all()]


@router.post("/", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    data = payload.model_dump(exclude={"company_ids"})
    person = Person(**data)
    if payload.company_ids:
        companies = db.query(Company).filter(Company.id.in_(payload.company_ids)).all()
        person.companies = companies
    db.add(person)
    db.commit()
    db.refresh(person)
    return _person_out(person)


@router.get("/{person_id}", response_model=PersonOut)
def get_person(person_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return _person_out(person)


@router.put("/{person_id}", response_model=PersonOut)
def update_person(person_id: int, payload: PersonUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    update_data = payload.model_dump(exclude_unset=True)
    company_ids = update_data.pop("company_ids", None)
    for field, value in update_data.items():
        setattr(person, field, value)
    if company_ids is not None:
        person.companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
    db.commit()
    db.refresh(person)
    return _person_out(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(person_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(person)
    db.commit()
