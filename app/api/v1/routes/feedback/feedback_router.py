from fastapi import APIRouter, Depends, HTTPException
from app.services.auth_handler import verify_token
from app.models.schemas.feedback import Feedback
from app.services.feedback_service import insert_feedback, get_feedback
from typing import List

router = APIRouter()

@router.post("")
async def submit_feedback(feedback: Feedback, user=Depends(verify_token)):
    return await insert_feedback(feedback.model_dump(), user)

@router.get("", response_model=List[Feedback])
async def get_all_feedback(user=Depends(verify_token)):
    return await get_feedback(user)

@router.get("/{user_id}", response_model=List[Feedback])
async def get_feedback_by_user(user_id: str, user=Depends(verify_token)):
    return await get_feedback_by_user(user_id)

@router.delete("/{feedback_id}")
async def delete_feedback(feedback_id: str, user=Depends(verify_token)):
    return await delete_feedback(feedback_id)
