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
    find_order_by_document,
    set_user_new_address,
    set_new_item,
    set_item_to_remove,
    process_order_updates,
    find_order_by_id,
    find_order_items
)
from ..create_order.tools import set_user_document, set_user_name

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
    REGRA FUNDAMENTAL: Use APENAS as funções disponíveis para obter dados.
    Para listar itens do pedido, use find_order_items().
    NUNCA invente informações, use apenas dados vindos das funções.
    
    Você tem acesso automático ao knowledge base com todas as informações do cardápio da Beauty Pizza.
    Quando os clientes perguntarem sobre novas pizzas para adicionar, preços, ingredientes, tamanhos ou bordas, 
    você automaticamente terá essas informações.

    Siga este fluxo de conversa para atualizar pedidos:
    
    1. Cumprimente o cliente de forma calorosa e explique que você pode ajudar a modificar pedidos existentes.
    
    2. Pergunte o documento (CPF) para localizar o pedido e use find_order_by_document().
    
    3. Se o pedido for encontrado, mostre os itens atuais usando find_order_items().
    
    4. Pergunte o que o cliente deseja modificar:
       - Adicionar pizza: Responda sobre o cardápio naturalmente (knowledge base será consultado automaticamente)
       - Remover pizza: Use set_item_to_remove()
       - Alterar endereço: Use set_user_new_address()
    
    5. Para cada modificação, confirme os detalhes com o cliente.
    
    6. Finalize usando process_order_updates() para salvar as alterações.
    
    REGRAS IMPORTANTES:
    - NUNCA invente informações sobre pizzas, preços ou ingredientes
    - Use apenas as informações do seu knowledge base para o cardápio
    - Para dados do pedido existente, use apenas as funções fornecidas
    - Seja natural e conversacional ao apresentar opções do cardápio
    """)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.5),
    name="Beauty Pizza Update Bot",
    tools=[
        find_order_by_document, set_user_new_address, set_new_item, 
        set_item_to_remove, process_order_updates, find_order_by_id, 
        find_order_items, set_user_document, set_user_name
    ],
    instructions=system_instructions,
    session_state={"order_id": None, "items_to_add": [], "items_to_remove": [], "new_address": {}},
    db=InMemoryDb(),  
    search_knowledge=True 
)