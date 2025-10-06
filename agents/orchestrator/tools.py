async def call_create_order_agent(session_state, user_input: str) -> str:
    """Chamar o agente de criação de pedido."""
    print("🔄 [ORQUESTRADOR] Direcionando para agente de CRIAR PEDIDO")
    print("Processando solicitação...")
    
    try:
        from ..create_order.agent import agent
        
        session_id = session_state.get("create_order_session_id")
        response = await agent.arun(user_input, session_id=session_id, add_history_to_context=True)
        
        session_state["create_order_session_id"] = response.session_id

        print("[AGENTE CRIAR PEDIDOS] Resposta processada")
        return response.content
        
    except Exception as e:
        print(f"❌ [ERRO] Falha ao carregar agente de criar pedidos: {e}")
        return "Desculpe, estou com problemas técnicos no momento. Tente novamente em alguns instantes."


async def call_update_order_agent(session_state, user_input: str) -> str:
    """Chamar o agente de atualização de pedido."""
    print("🔄 [ORQUESTRADOR] Direcionando para agente de ATUALIZAR PEDIDO")
    print("Processando solicitação...")
    
    try:
        from ..update_order.agent import agent
        
        session_id = session_state.get("update_order_session_id")
        response = await agent.arun(user_input, session_id=session_id, add_history_to_context=True)

        session_state["update_order_session_id"] = response.session_id
        
        print("[AGENTE ATUALIZAR PEDIDOS] Resposta processada")
        return response.content
        
    except Exception as e:
        print(f"❌ [ERRO] Falha ao carregar agente de atualizar pedidos: {e}")
        import traceback
        traceback.print_exc()
        return "Desculpe, estou com problemas técnicos no momento. Tente novamente em alguns instantes."