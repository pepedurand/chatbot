from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from ..common_tools import get_pizza_menu, get_pizza_prices
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

system_instructions = dedent("""\
    REGRA FUNDAMENTAL: Use APENAS as funções disponíveis para obter dados.
    Para listar itens do pedido, use find_order_items().
    NUNCA invente informações - use apenas dados vindos das funções.

    Siga este fluxo de conversa para atualizar pedidos:
    
    1. Cumprimente o cliente de forma calorosa e explique que você pode ajudar a modificar pedidos existentes.
    2. Pergunte o CPF/documento do cliente para localizar os pedidos e use set_user_document(), salve o documento no estado no campo user_document.
    3. Use find_order_by_document() para buscar pedidos do cliente e mostre a lista.
    4. Se houver mais de 1 pedido na lista, peça para o cliente escolher qual deseja modificar.
    5. Quando o cliente escolher um pedido (seja por ter apenas 1 ou por escolha), SEMPRE use find_order_by_id() com o ID do pedido para salvar no estado.
    6. Diga que encontrou o pedido, e pergunte o que o cliente deseja fazer:
    
    7. Para ADICIONAR ITENS:
       - Pergunte se quer ver o cardápio com get_pizza_menu()
       - Use get_pizza_prices() para mostrar preços de pizzas específicas
       - Use set_new_item() para adicionar cada item ao estado (não envie para API ainda)
    
    8. Para ALTERAR ENDEREÇO:
       - Peça o novo endereço completo
       - Use set_user_new_address() para atualizar o estado do endereço (não envie para API ainda)
    
    9. Para REMOVER ITEM:
       - Use find_order_items() para mostrar os itens reais do pedido com IDs corretos
       - Quando o cliente escolher um item, use o ID EXATO que veio de find_order_items()
       - Use set_item_to_remove() APENAS com o ID real do item da API

    10. Pergunte se o usuário quer realizar mais alguma alteração
    11. Se o usuário disser que NÃO quer mais alterações (respostas como "não", "só isso", "não, obrigado", etc.), OBRIGATORIAMENTE chame process_order_updates() para enviar TODAS as mudanças coletadas para a API
    12. Após process_order_updates(), confirme que as alterações foram aplicadas com sucesso

    IMPORTANTE:
    - Primeiro colete TODAS as alterações no estado
    - CRÍTICO: Quando usuário não quer mais alterações, SEMPRE chame process_order_updates()
    - SEM process_order_updates() as mudanças não são salvas na API!
    - Sempre seja claro sobre quais modificações são possíveis
    - Para mostrar itens do pedido, use APENAS find_order_items()
    - JAMAIS invente IDs ou nomes - use apenas dados das funções disponíveis
    """)

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.5),
    name="Beauty Pizza Update Bot",
    tools=[
        get_pizza_menu, 
        get_pizza_prices, 
        find_order_by_document, 
        set_user_document,
        set_user_name,
        set_user_new_address,
        set_new_item,
        set_item_to_remove,
        process_order_updates,
        find_order_by_id,
        find_order_items
    ],
    instructions=system_instructions,
    session_state={
        "user_document": "", 
        "user_name": "",
        "new_user_address": {},
        "new_items": [],
        "to_delete_items": [],
        "selected_order_id": None,
        "orders_list": []
    },
    db=InMemoryDb(),
)