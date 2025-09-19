import asyncio
from config import Config
from body import get_bot_instance

async def main():
    """Основная функция запуска бота"""
    bot = get_bot_instance()
    
    try:
        print("🤖 Запуск бота...")
        print(f"🔧 Режим логирования: {Config.LOG_LEVEL}")
        print(f"👤 ID администратора: {Config.ADMIN_CHAT_ID}")
        
        await bot.polling(non_stop=True, skip_pending=True)
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.close_session()
        print("👋 Бот остановлен")

if __name__ == "__main__":
    # Валидация конфигурации перед запуском
    Config.validate()
    
    # Запуск бота
    asyncio.run(main())