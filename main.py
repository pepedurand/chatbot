from dotenv import load_dotenv
import os
import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb
from agno.tools.duckdb import DuckDbTools


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_path = os.getenv("SQLITE_DB_PATH")

if not openai_api_key:
    raise ValueError("A variável de ambiente OPENAI_API_KEY não foi definida. Crie um arquivo .env e adicione-a.")
if not db_path:
    raise ValueError("A variável de ambiente SQLITE_DB_PATH não foi definida. Crie um arquivo .env e adicione-a.")

duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)

def set_item(session_state, pizza_name: str, size: str, crust: str, quantity: int) -> None:
    """Add a pizza to the list."""
    session_state["pizzas"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust,
        "quantity": quantity
    })

def set_user_name(session_state, name: str) -> None:
    """Set the user's name."""
    session_state["user_name"] = name

def set_user_document(session_state, document: str) -> None:
    """Set the user's document."""
    session_state["user_document"] = document

def set_user_address(session_state, street_name: str, number: int, reference_point: str, complement: str) -> None:
    """Set the user's address."""
    session_state["address"] = {
        "street_name": street_name,
        "number": number,
        "reference_point": reference_point,
        "complement": complement
    }

def send_data_to_api(session_state) -> str:
    """Send the order data to an external API and return a success message."""
    order_data = {
        "client_name": session_state.get("user_name"),
        "client_document": session_state.get("user_document"),
        "delivery_address": {
            "street_name": session_state["address"].get("street_name"),
            "number": session_state["address"].get("number"),
            "complement": session_state["address"].get("complement"),
            "reference_point": session_state["address"].get("reference_point")
        },
	    "items": session_state.get("pizzas")
    }
    print("Sending order data to API:", order_data)
    # Aqui você faria a chamada real para a API, por exemplo, com a biblioteca requests.
    # Ex: requests.post("https://api.pizzaria.com/orders", json=order_data)
    return "Seu pedido foi enviado com sucesso e chegará quentinho em aproximadamente 40 minutos!"

system_instructions = dedent("""\
    Você é uma atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
    Seu objetivo é guiar o cliente de forma natural pelo processo de pedido, coletando todas as informações necessárias.

    Siga este fluxo de conversa:
    1. Cumprimente o cliente e pergunta se ele precisa ver o cardápio ou se já sabe o que quer.
    2. Pergunte o nome do cliente antes de continuar, guarde essa informação no estado da sessão.
    3. Continue, se ele quiser ver o cardápio, mostre as opções de pizzas, tamanhos e bordas.
    4. Quando ele escolher uma pizza, pergunte o tamanho, a borda e a quantidade.
    5. Pergunte se ele quer adicionar mais alguma pizza.
    6. Se ele não quiser adicionar mais pizzas, pergunte o endereço de entrega.
    7. Pergunte o documento para a nota fiscal.
    8. Nesse momento chame a API de pedidos para enviar o pedido.
    """)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key),
    name="Beauty Pizza Bot",
    tools=[duckdb_tools, set_item, set_user_name, set_user_document, set_user_address, send_data_to_api],
    instructions=system_instructions,
    session_state={"pizzas": [], "user_name": "", "user_document": "", "address": {}},
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
