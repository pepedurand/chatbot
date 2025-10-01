import asyncio
from textwrap import dedent
from typing import Optional
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from dotenv import load_dotenv
import os
from agno.db.in_memory import InMemoryDb
from agno.tools.duckdb import DuckDbTools


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_path = os.getenv("SQLITE_DB_PATH")

print(f"DEBUG: DB Path: {db_path}")
print(f"DEBUG: DB Path exists: {os.path.exists(db_path) if db_path else 'DB_PATH is None'}")

duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)

try:
    tables_result = duckdb_tools.run_query("SHOW TABLES")
    print(f"DEBUG: Tabelas encontradas: {tables_result}")
except Exception as e:
    print(f"ERROR: Falha ao conectar/consultar banco: {e}")
    import traceback
    traceback.print_exc()



agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key),
    name="Beauty Pizza Bot",
    tools=[duckdb_tools],
    instructions="Você é um atendente simpático da pizzaria Beauty Pizza 🍕.",
    db=InMemoryDb(),
    additional_context=dedent("""\
    You have access to the following tables:
    - pizzas: contem as informacoes de sabores de pizzas
    - tamanhos: contem as informacoes de tamanhos de pizzas
    - bordas: contem as informacoes de tipos de bordas
    - precos: contem as informacoes de precos de pizzas, correlacionado pizza, tamanho e borda
    Use SQL queries to get the information you need to answer the user's questions.
    """),

)

async def run_agent_on_terminal(message: str):
    try:
        response = await agent.arun(message, add_history_to_context=True)  
        agent.session_id = response.session_id
        print("Bot:", response.content)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
        asyncio.run(run_agent_on_terminal(user_input))
