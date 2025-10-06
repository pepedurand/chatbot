from dotenv import load_dotenv
import os
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from agents.create_order.agent import agent as create_order_agent
from agents.update_order.agent import agent as update_order_agent

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

team = Team(
    name="Beauty Pizza Bot - Criação e Atualização de Pedidos",
    members=[create_order_agent, update_order_agent],
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.3),
    db=InMemoryDb(),
)
