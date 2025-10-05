from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from agents.tools import (
    get_pizza_menu,
    get_pizza_prices,
    set_item,
    set_user_name,
    set_user_document,
    set_user_address,
    send_data_to_api
)

from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from pathlib import Path
from agno.knowledge.reader.markdown_reader import MarkdownReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5533/ai"

training_file = Path("./agents/create_order/treinamento_atendimento.md")

# Knowledge base simples - usar apenas o conteúdo do arquivo sem vector DB
kb = None

# Para evitar problemas com event loop, vamos usar apenas o conteúdo direto do arquivo
try:
    # Simular um knowledge base básico usando apenas o conteúdo do arquivo
    kb = None  # Desabilitado por enquanto
except Exception as e:
    kb = None


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

with open(training_file, "r", encoding="utf-8") as f:
    treinamento_atendimento = f.read()

system_instructions = dedent(f"""\
    {treinamento_atendimento}
    
    INSTRUÇÕES PRINCIPAIS:
    Você é uma atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
    
    SIGA RIGOROSAMENTE O FLUXO OFICIAL DE ATENDIMENTO:
    1. Cumprimento & nome - sempre pergunte o nome e salve com set_user_name()
    2. Cardápio - ofereça mostrar o cardápio com get_pizza_menu()
    3. Escolha por sabor - sempre use get_pizza_prices(sabor) ao mencionar sabor
    4. Montagem do item - confirme tamanho, borda, quantidade e salve com set_item()
    5. Mais itens? - pergunte se quer adicionar mais
    6. Endereço e documento - colete com set_user_address() e set_user_document()
    7. Resumo & confirmação - mostre todos os itens e total antes de confirmar
    8. Envio - use send_data_to_api() após confirmação
    
    REGRAS IMPORTANTES:
    - SEMPRE consulte o banco de dados para preços com get_pizza_prices() ou get_pizza_menu()
    - NUNCA invente preços
    - SEMPRE confirme o resumo completo antes de enviar
    - Uma pergunta por vez quando necessário
    - Seja objetiva e clara
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
    knowledge=kb,
    search_knowledge=False if kb is None else True,
)
