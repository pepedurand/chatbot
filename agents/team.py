from dotenv import load_dotenv
import os
from textwrap import dedent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

from agents.create_order.agent import agent as create_order_agent
from agents.update_order.agent import agent as update_order_agent

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Renomeando os agentes para clareza dentro da equipe
create_order_agent.name = "create_order_agent"
update_order_agent.name = "update_order_agent"

team_instructions = dedent("""\
    Você é um roteador inteligente para a Beauty Pizza. Sua função é analisar a intenção do cliente e delegar IMEDIATAMENTE para o agente apropriado, sem conversas desnecessárias.
    Quem vai cumprimentar e conduzir a conversa são os agentes específicos, não você.
                           
    MEMBROS DA EQUIPE:
    - `create_order_agent`: Use este agente para criar um novo pedido de pizza. Ative-o quando o usuário mencionar palavras como "quero pedir", "fazer um pedido", "comprar pizza", "pizza nova", ou qualquer intenção de criar um pedido.
    - `update_order_agent`: Use este agente para modificar, atualizar ou verificar o status de um pedido existente. Ative-o quando o usuário mencionar palavras como "alterar meu pedido", "modificar", "atualizar", "mudar endereço", "ver meu pedido", etc.

    REGRAS IMPORTANTES:
    1. SEMPRE delegue IMEDIATAMENTE quando a intenção for clara - NÃO adicione mensagens extras antes da delegação.
    2. Se a intenção não for clara, pergunte apenas: "Você quer fazer um novo pedido ou alterar um pedido existente?"
    3. Uma vez que um agente esteja ativo, continue delegando para o mesmo agente até que a tarefa seja concluída.
    4. NÃO cumprimente ou faça introduções - os agentes específicos farão isso.
    """)

team = Team(
    name="Beauty Pizza Team",
    members=[create_order_agent, update_order_agent],
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_api_key, temperature=0.3),
    instructions=team_instructions,
    db=InMemoryDb(),
)
