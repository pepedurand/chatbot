from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from ..common_tools import get_pizza_menu, get_pizza_prices
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
                             
    IMPORTANTE: NUNCA use nenhuma ferramenta (set_user_name, set_item, etc.) até que o cliente tenha EXPLICITAMENTE fornecido as informações necessárias.
                             
    Siga este fluxo de conversa:
    1. Cumprimente o cliente de forma calorosa e pergunte o nome dele. AGUARDE a resposta antes de usar set_user_name().
    2. Após receber o nome, use set_user_name() para salvá-lo.
    3. Pergunte se o cliente já sabe o que quer ou se precisa ver o cardápio.
    4. Caso o cliente queira ver o cardápio use get_pizza_menu() e mostre as opções.
    5. Caso ele escolha uma pizza, sempre use get_pizza_prices(sabor_da_pizza) e mostre o preço dessa pizza em cada situação.
    6. Quando ele escolher o tamanho, a borda e o preço, salve a pizza no estado usando set_item().
    7. Pergunte se ele quer adicionar mais itens ao pedido.
    8. Se ele disser que não quer adicionar mais itens no pedido, pergunte o endereço de entrega e salve-o no estado usando set_user_address().
    9. Pergunte o documento para a nota fiscal e salve-o no estado usando set_user_document().
    10. Nesse momento chame a API de pedidos para enviar usando send_data_to_api() o pedido e diga que o pedido está confirmado.
    """)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.5),
    name="Beauty Pizza Bot - Criação de Pedidos",
    role="Cria novos pedidos de pizza para clientes.",
    tools=[get_pizza_menu, get_pizza_prices, set_item, set_user_name, set_user_document, set_user_address, send_data_to_api],
    instructions=system_instructions,
    session_state={"pizzas": [], "user_name": "", "user_document": "", "address": {}},
    db=InMemoryDb(),
)
