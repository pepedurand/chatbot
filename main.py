from dotenv import load_dotenv
import os
import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from tools import (
    get_pizza_menu,
    get_pizza_prices,
    set_item,
    set_user_name,
    set_user_document,
    set_user_address,
    send_data_to_api
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

system_instructions = dedent("""\
    Você é uma atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
    Seu objetivo é guiar o cliente de forma natural pelo processo de pedido, coletando todas as informações necessárias.

    IMPORTANTE: Use APENAS as funções fornecidas. NÃO execute queries SQL diretamente.

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
    additional_context=dedent("""\
    Sempre que um cliente falar sobre alguma pizza, use APENAS as funções fornecidas: get_pizza_menu() e get_pizza_prices(pizza_flavour).
    NÃO execute queries SQL diretamente. Use sempre as funções disponíveis.
    
    Informações sobre o banco de dados (apenas para referência):
    - pizzas: contém os sabores (campo: sabor)
    - tamanhos: contém os tamanhos (campo: tamanho)  
    - bordas: contém os tipos de bordas (campo: tipo)
    - precos: contém os preços correlacionados
    
    IMPORTANTE: Use APENAS as funções get_pizza_menu() e get_pizza_prices(sabor_da_pizza) para consultar informações.
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