from ..create_order.agent import agent as create_order_agent
from ..update_order.agent import agent as update_order_agent

async def call_create_order_agent(session_state, input: str) -> str:
    """Chama o agente de criação de pedidos com knowledge base vetorial."""
    response = await create_order_agent.arun(input, session_state=session_state, add_history_to_context=True)
    return response.content

async def call_update_order_agent(session_state, input: str) -> str:
    """Chama o agente de atualização de pedidos com knowledge base vetorial."""
    response = await update_order_agent.arun(input, session_state=session_state, add_history_to_context=True)
    return response.content