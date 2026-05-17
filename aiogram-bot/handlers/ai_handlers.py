from aiogram import Router, types
from database.models import db_manager
from services.ai_service import get_ai_response

router = Router()

@router.message()
async def chat_with_ai(message: types.Message):
    user = await db_manager.get_user(message.from_user.id)
    
    if not user:
        await message.answer("Сначала пройди регистрацию командой /start")
        return

    response = await get_ai_response(user['name'], user['activity'], message.text)
    await message.answer(response)
