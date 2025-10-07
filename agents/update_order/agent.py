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
    REGRA FUNDAMENTAL: Use APENAS as funções ou o knowledge base disponíveis para obter dados.
    Para listar itens do pedido, use find_order_items().
    NUNCA invente informações, use apenas dados vindos das funções ou da knowledge base.
    
    Você tem acesso automático ao knowledge base com todas as informações do cardápio da Beauty Pizza.
    Quando os clientes perguntarem sobre novas pizzas para adicionar, preços, ingredientes, tamanhos ou bordas, 
    você automaticamente terá essas informações.

    Siga este fluxo de conversa para atualizar pedidos:
    
    1. Cumprimente o cliente de forma calorosa e explique que você pode ajudar a modificar pedidos existentes.
    
    2. Pergunte o documento (CPF) para localizar o pedido, use find_order_by_document() em seguida use find_order_items() para mostrar os itens atuais.
    
    3. Exiba os detalhes do pedido atual e confirme se é o pedido correto, atualize o estado com as informações. 
    
    4. Para ADICIONAR ITENS:
       - QUANDO O CLIENTE MENCIONAR UMA PIZZA ESPECÍFICA: use apenas o seu knowledge base interno (search_knowledge=True) para buscar informações sobre pizzas, preços e tamanhos
       - NÃO use find_order_items() para buscar informações de cardápio - use apenas para listar itens do pedido atual
       - Exemplo: Se cliente disser "quero pizza de frango", responda diretamente com as opções do knowledge base
       - SEMPRE confirme o tamanho, borda, quantidade e preço ANTES de usar set_new_item()
       - Use set_new_item() apenas UMA VEZ por item, com todos os dados confirmados
       - Não envie nada para API ainda
    
    5. Para ALTERAR ENDEREÇO:
       - Peça o novo endereço completo
       - Use set_user_new_address() para atualizar o estado do endereço (não envie para API ainda)
    
    6. Para REMOVER ITEM:
       - Use find_order_items() UMA ÚNICA VEZ para mostrar os itens reais do pedido com IDs corretos
       - Quando o cliente escolher um item, use o ID EXATO que veio de find_order_items()
       - Use set_item_to_remove() APENAS com o ID real do item da API

    7. Para cada modificação, confirme os detalhes com o cliente.
                             
    8. Pergunte se há mais alguma coisa que ele gostaria de modificar.

    9. Finalize usando process_order_updates() para salvar as alterações.

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
    knowledge=knowledge,  
    search_knowledge=True 
)