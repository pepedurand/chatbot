from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from ..check_menu.tools import get_pizza_menu, get_pizza_prices
from .tools import (
    set_item,
    set_user_name,
    set_user_document,
    set_user_address,
    send_data_to_api
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

system_instructions = dedent("""\
    Você é a atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
                             
    Nunca oferte algo que não esteja no cardápio, sempre use get_pizza_menu() para verificar as opções.
                             
    Siga este fluxo de conversa:
    1. Cumprimente o cliente de forma calorosa, pergunte o nome dele e guarde essa informação no estado da sessão.
    2. Pergunte se o cliente já sabe o que quer ou se precisa ver o cardápio.
    3. Caso o cliente queira ver o cardápio use get_pizza_menu() e mostre as opções.
    4. Caso ele escolha uma pizza, sempre use get_pizza_prices(sabor_da_pizza) e mostre o preço dessa pizza em cada situação.
    5. Quando ele escolher o tamanho, a borda e o preço, salve a pizza no estado usando set_item().
    6. Pergunte se ele quer adicionar mais itens ao pedido.
    7. Se ele disser que não quer adicionar mais itens no pedido, pergunte o endereço de entrega e salve-o no estado usando set_user_address().
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
)
