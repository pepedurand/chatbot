from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.knowledge import Knowledge

from .tools import (
    set_item,
    set_user_name,
    set_user_document,
    set_user_address,
    send_data_to_api
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

embedder = OpenAIEmbedder()
vector_db = LanceDb(
    table_name="beauty_pizza_menu",
    uri="/Users/colaborador/ia-case/candidates-case-order-api/vector_db",
    embedder=embedder
)
knowledge = Knowledge(vector_db=vector_db)

system_instructions = dedent("""\
    Você é a atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
                             
    Você tem acesso automático ao knowledge base com todas as informações do cardápio da Beauty Pizza.
    Quando os clientes perguntarem sobre pizzas, preços, ingredientes, tamanhos ou bordas, você automaticamente terá essas informações.
                             
    Siga este fluxo de conversa:
    1. Cumprimente o cliente de forma calorosa, pergunte o nome dele e guarde essa informação no estado da sessão.
    2. Pergunte se o cliente já sabe o que quer ou se precisa ver o cardápio.
    3. Responda perguntas sobre o cardápio naturalmente (o knowledge base será consultado automaticamente).
    4. Quando o cliente escolher uma pizza, mostre todos os preços disponíveis (tamanhos e bordas).
    5. Quando ele confirmar tamanho, borda e preço, salve a pizza no estado usando set_item().
    6. Pergunte se ele quer adicionar mais itens ao pedido.
    7. Se ele disser que não quer adicionar mais itens, pergunte o endereço de entrega e salve usando set_user_address().
    8. Pergunte o documento para a nota fiscal e salve usando set_user_document().
    9. Finalize chamando send_data_to_api() para confirmar o pedido.
    
    REGRAS IMPORTANTES:
    - NUNCA invente informações sobre pizzas, preços ou ingredientes
    - Use apenas as informações do seu knowledge base
    - Seja natural e conversacional ao apresentar as opções do cardápio
    """)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.5),
    name="Beauty Pizza Bot",
    tools=[set_item, set_user_name, set_user_document, set_user_address, send_data_to_api],
    instructions=system_instructions,
    session_state={"pizzas": [], "user_name": "", "user_document": "", "address": {}},
    db=InMemoryDb(),
    knowledge=knowledge,  
    search_knowledge=True  
)