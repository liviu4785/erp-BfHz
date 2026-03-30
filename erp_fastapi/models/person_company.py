from sqlalchemy import Table, Column, Integer, ForeignKey
from erp_fastapi.database import Base

person_company = Table(
    "person_company",
    Base.metadata,
    Column("person_id", Integer, ForeignKey("people.id"), primary_key=True),
    Column("company_id", Integer, ForeignKey("companies.id"), primary_key=True),
)
