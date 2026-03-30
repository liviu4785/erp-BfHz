from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.document import Document
from erp_fastapi.models.user import User
from erp_fastapi.schemas.document import DocumentCreate, DocumentUpdate, DocumentOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[DocumentOut])
def list_documents(
    record_type: str = Query(None),
    record_id: int = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Document)
    if record_type:
        query = query.filter(Document.record_type == record_type)
    if record_id:
        query = query.filter(Document.record_id == record_id)
    return query.order_by(Document.id.desc()).all()


@router.post("/", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    doc = Document(**payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: int, payload: DocumentUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
