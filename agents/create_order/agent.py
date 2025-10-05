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

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

db_url = "postgresql+psycopg://ai:ai@localhost:5533/ai"
training_file = Path("./agents/create_order/treinamento_criar_pedido.md")

_knowledge_base = None
_agent = None

async def get_knowledge_base():
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = Knowledge(
            name="Beauty Pizza Manual",
            description="Manual de treinamento para atendimento da Beauty Pizza",
            vector_db=PgVector(
                table_name="markdown_documents",
                db_url=db_url,
                embedder=OpenAIEmbedder(api_key=openai_api_key),
            ),
            contents_db=InMemoryDb(),
        )
        
        await _knowledge_base.add_content_async(
            path=training_file,
            reader=MarkdownReader(),
        )
    
    return _knowledge_base

async def get_agent():
    global _agent
    if _agent is None:
        kb = await get_knowledge_base()
        
        with open(training_file, "r", encoding="utf-8") as f:
            treinamento_atendimento = f.read()

        system_instructions = dedent(f"""\
            {treinamento_atendimento}
            Você é uma atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
            Olhe o seu knowledge base para entender como a empresa funciona e como é o atendimento.
            Olhe o knowledge para toda ocasião.
            """)

        _agent = Agent(
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
    
    return _agent

class LoadedAgent:
    def __init__(self):
        self._agent = None
    
    async def arun(self, *args, **kwargs):
        if self._agent is None:
            self._agent = await get_agent()
        return await self._agent.arun(*args, **kwargs)

agent = LoadedAgent()
