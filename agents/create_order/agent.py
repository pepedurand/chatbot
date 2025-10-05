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

kb = Knowledge(
    name="Beauty Pizza Manual",
    description="Manual de treinamento para atendimento da Beauty Pizza",
    vector_db=PgVector(
        table_name="markdown_documents",
        db_url=db_url,
        embedder=OpenAIEmbedder(api_key=os.getenv("OPENAI_API_KEY")),
    ),
    contents_db=InMemoryDb(),
)

training_file = Path("./agents/create_order/treinamento_atendimento.md")

kb.add_content(
    path=training_file,
    reader=MarkdownReader(),
)


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

with open(training_file, "r", encoding="utf-8") as f:
    treinamento_atendimento = f.read()

system_instructions = dedent(f"""\
    {treinamento_atendimento}
    Você é uma atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
    Olhe o seu knowledge base para entender como a empresa funciona e como é o atendimento.
    Olhe o knowledge para toda ocasião.
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
    search_knowledge=True,
)
