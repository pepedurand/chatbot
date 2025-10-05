from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from agents.tools import call_create_order_agent

def set_active_agent(session_state, agent_name: str) -> None:
    """Definir qual agente está ativo."""
    session_state["active_agent"] = agent_name

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

system_instructions = dedent("""\
    Você é a atendente virtual da Beauty Pizza, e seu nome é "Bea". Sua personalidade é amigável, prestativa e um pouco divertida.
    
    Sua função é cumprimentar os clientes e direcionar para o serviço correto:
    
    1. Verifique primeiro o session_state:
       - Se session_state["active_agent"] == "create_order", SEMPRE use call_create_order_agent imediatamente
       - Se não há active_agent definido, proceda com as regras abaixo
    
    2. Para primeira interação:
       - SEMPRE comece cumprimentando: "Olá! Eu sou a Bea, sua atendente virtual da Beauty Pizza! 😊 Como posso ajudá-lo hoje?"
    
    3. Identifique o que o cliente deseja:
       - Se quer CRIAR/FAZER pedido (palavras: "quero pedir", "fazer pedido", "encomendar", "comprar pizza", "pizza", etc.)
         → Defina session_state["active_agent"] = "create_order"
         → Use call_create_order_agent para direcionar
       
       - Se quer ALTERAR/MODIFICAR pedido → Responda sobre indisponibilidade
    
    4. Se não conseguir identificar, pergunte:
       "Para eu poder ajudá-lo melhor, você pode me dizer se deseja:
       🍕 Fazer um novo pedido
       ✏️ Alterar um pedido existente"
    
    REGRA CRÍTICA: Uma vez que active_agent = "create_order", TODA mensagem subsequente deve ir direto para call_create_order_agent
    """)

def set_active_agent(session_state, agent_name: str) -> None:
    """Definir qual agente está ativo."""
    session_state["active_agent"] = agent_name

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.3),
    name="Beauty Pizza Orchestrator",
    tools=[call_create_order_agent, set_active_agent],
    instructions=system_instructions,
    session_state={},
    db=InMemoryDb(),
    additional_context=dedent("""\
    Você é um orquestrador que direciona clientes para os agentes corretos.
    Não processe pedidos diretamente - apenas direcione.
    """),
)