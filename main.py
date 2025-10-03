from dotenv import load_dotenv
import os
import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb
from agno.tools.duckdb import DuckDbTools
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
db_path = os.getenv("SQLITE_DB_PATH")
ORDER_API_URL = os.getenv("ORDER_API_URL")

try:
    ORDERS_API_TIMEOUT = float(os.getenv("ORDERS_API_TIMEOUT", "10"))
except (TypeError, ValueError):
    ORDERS_API_TIMEOUT = 10.0

duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)

async def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    if not ORDER_API_URL:
        raise RuntimeError("A variável de ambiente ORDER_API_URL não foi configurada.")

    url = f"{ORDER_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    def _do_request() -> Dict:
        try:
            if method.upper() == 'POST':
                response = requests.post(
                    url=url,
                    json=data,
                    timeout=ORDERS_API_TIMEOUT
                )
            else:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=ORDERS_API_TIMEOUT
                )
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if response.content and "application/json" in content_type:
                return response.json()
            return {}
        except RequestException as exc:
            raise RequestException(f"Erro na requisição para {url}: {exc}") from exc

    return await asyncio.to_thread(_do_request)


def set_item(session_state, pizza_name: str, size: str, crust: str, quantity: int, unit_price: float) -> None:
    """Add a pizza to the list."""
    session_state["pizzas"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust,
        "quantity": quantity,
        "unit_price": unit_price
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

async def send_data_to_api(session_state) -> str:
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
        "items": [
            {
                "name": f"{item['name']} - {item['size']} - {item['crust']}",
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
            for item in session_state.get("pizzas", [])
        ],
    }
    await make_request('POST', '/api/orders/', order_data)
    return "Pedido enviado para confirmação."


def get_pizza_prices(pizza_flavour: str) -> list:
    """Retrieve pizza prices from the database based on the pizza flavour."""
    query = """
    SELECT p.sabor AS pizza_name, t.tamanho AS size, b.tipo AS crust, pr.preco AS unit_price
    FROM pizzas p
    JOIN precos pr ON p.id = pr.pizza_id
    JOIN tamanhos t ON pr.tamanho_id = t.id
    JOIN bordas b ON pr.borda_id = b.id
    WHERE p.sabor = ?;
    """
    results = duckdb_tools.connection.execute(query, [pizza_flavour]).fetchall()
    prices = []
    for row in results:
        prices.append({
            "pizza_name": row[0],
            "size": row[1],
            "crust": row[2],
            "unit_price": row[3]
        })
    return prices

def get_pizza_menu() -> list:
    """Retrieve the pizza menu from the database."""
    query = """
    SELECT p.sabor AS pizza_name, t.tamanho AS size, b.tipo AS crust, pr.preco AS unit_price
    FROM pizzas p
    JOIN precos pr ON p.id = pr.pizza_id
    JOIN tamanhos t ON pr.tamanho_id = t.id
    JOIN bordas b ON pr.borda_id = b.id;
    """
    results = duckdb_tools.connection.sql(query).fetchall()
    menu = []
    for row in results:
        menu.append({
            "pizza_name": row[0],
            "size": row[1],
            "crust": row[2],
            "unit_price": row[3]
        })
    return menu

system_instructions = dedent("""\
    Você é uma atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
    Seu objetivo é guiar o cliente de forma natural pelo processo de pedido, coletando todas as informações necessárias.

    Siga este fluxo de conversa:
    1. Cumprimente o cliente de forma calorosa, pergunte o nome dele e guarde essa informação no estado da sessão.
    2. Pergunte se o cliente já sabe o que quer ou se precisa ver o cardápio.
    3. Caso o cliente queira ver o cardápio use get_pizza_menu() e mostre as opções.
    4. Caso ele escolha uma pizza, sempre use get_pizza_prices(pizza) e mostra o preço dessa pizza em cada situação.
    5. Quando ele escolher, o tamanho, a borda e o preço e salve a pizza no estado use set_item().
    6. Pergunte se ele quer adicionar mais itens ao pedido.
    7. Se ele disser que não quiser adicionar mais itens no pedido, pergunte o endereço de entrega e salve-o no estado usando set_user_address().
    8. Pergunte o documento para a nota fiscal e salve-o no estado usando set_user_document().
    9. Nesse momento chame a API de pedidos para enviar usando send_data_to_api() o pedido e diga que o pedido está confirmado.
    """)


agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.5),
    name="Beauty Pizza Bot",
    tools=[get_pizza_menu, get_pizza_prices, set_item, set_user_name, set_user_document, set_user_address, send_data_to_api],
    instructions=system_instructions,
    session_state={"pizzas": [], "user_name": "", "user_document": "", "address": {}},
    db=InMemoryDb(),
    additional_context=dedent("""\
    Sempre que um cliente falar sobre alguma pizza confira as informacoes e preco no banco de dados.
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