import asyncio
from agents.create_order.agent import agent


async def main():
    session_id = None
    while True:
        user_input = await asyncio.to_thread(input, "Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
        try:
            response = await agent.arun(user_input, session_id=session_id, add_history_to_context=True)  
            session_id = response.session_id
            print("Bot:", response.content)
            print("Current session state:", agent.session_state)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())