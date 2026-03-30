from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.comment import Comment
from erp_fastapi.models.user import User
from erp_fastapi.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])


def _comment_out(c: Comment) -> CommentOut:
    return CommentOut(
        id=c.id, content=c.content, author_id=c.author_id,
        author_name=c.author.name if c.author else None,
        record_type=c.record_type, record_id=c.record_id,
        created_at=c.created_at,
    )


@router.get("/", response_model=List[CommentOut])
def list_comments(
    record_type: str = Query(None),
    record_id: int = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Comment)
    if record_type:
        query = query.filter(Comment.record_type == record_type)
    if record_id:
        query = query.filter(Comment.record_id == record_id)
    return [_comment_out(c) for c in query.order_by(Comment.id.desc()).all()]


@router.post("/", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = Comment(
        content=payload.content,
        author_id=current_user.id,
        record_type=payload.record_type,
        record_id=payload.record_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_out(comment)


@router.put("/{comment_id}", response_model=CommentOut)
def update_comment(comment_id: int, payload: CommentUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(comment, field, value)
    db.commit()
    db.refresh(comment)
    return _comment_out(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
