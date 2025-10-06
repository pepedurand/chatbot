import asyncio
from agents.team import team


async def main():
    session_id = None
    print("🚀 [SISTEMA] Iniciando Beauty Pizza Bot")
    
    while True:
        user_input = await asyncio.to_thread(input, "Você: ")
        try:
            print("🎯 [EQUIPE] Processando sua solicitação...")
            response = await team.arun(user_input, session_id=session_id)
            session_id = response.session_id
            print("Bot:", response.content)
        except Exception as e:
            print("❌ [ERRO] Ocorreu um erro:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
    