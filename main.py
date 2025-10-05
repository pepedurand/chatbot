import asyncio
from agents.orchestrator.agent import agent


async def main():
    session_id = None
    print("🚀 [SISTEMA] Iniciando Beauty Pizza Bot com Agente Orquestrador")
    print("=" * 60)
    
    while True:
        user_input = await asyncio.to_thread(input, "Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            print("👋 [SISTEMA] Encerrando Beauty Pizza Bot. Até logo!")
            break
        try:
            print("🎯 [ORQUESTRADOR] Processando sua solicitação...")
            response = await agent.arun(user_input, session_id=session_id, add_history_to_context=True)  
            session_id = response.session_id
            print("Bot:", response.content)
            print("-" * 60)
        except Exception as e:
            print("❌ [ERRO] Ocorreu um erro:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())