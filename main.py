import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
from agno.db.in_memory import InMemoryDb
from agno.tools.duckdb import DuckDbTools


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_path = os.getenv("SQLITE_DB_PATH")

duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)

def add_item(session_state, pizza_name: str, size: str, crust: str) -> str:
    """Add a pizza to the list."""
    session_state["pizzas"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust
    })
    return f"The pizza list is now {session_state['pizzas']}"

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key),
    name="Beauty Pizza Bot",
    tools=[duckdb_tools, add_item],
    instructions="Você é um atendente simpático da pizzaria Beauty Pizza 🍕.",
    session_state={"pizzas": []},
    db=InMemoryDb(),
    additional_context=dedent("""\
    Sempre que um cliente falar sobre alguma pizza confira as informacoes no banco de dados.
    Voce tem acesso a um banco de dados com as seguintes tabelas:
    - pizzas: contem as informacoes de sabores de pizzas
    - tamanhos: contem as informacoes de tamanhos de pizzas
    - bordas: contem as informacoes de tipos de bordas
    - precos: contem as informacoes de precos de pizzas, correlacionado pizza, tamanho e borda
    Use queries SQL para obter as informacoes e responder as perguntas dos clientes.
    """),
)

async def run_agent_on_terminal(message: str):
    try:
        response = await agent.arun(message, add_history_to_context=True)  
        agent.session_id = response.session_id
        print("Bot:", response.content)
        print(agent.session_state)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
        asyncio.run(run_agent_on_terminal(user_input))
