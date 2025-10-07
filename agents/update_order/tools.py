from ..common_tools import make_request


def set_user_new_address(session_state, street_name: str, number: int, complement: str, reference_point: str) -> None:
    """Definir o novo endereço para atualização do pedido."""
    print("Atualizando novo endereço no estado")
    session_state["new_user_address"] = {
        "street_name": street_name,
        "number": number,
        "complement": complement,
        "reference_point": reference_point
    }


def set_new_item(session_state, pizza_name: str, size: str, crust: str, quantity: int, unit_price: float) -> None:
    """Adicionar um novo item à lista de itens para adicionar ao pedido."""
    print("Adicionando novo item ao estado")
    session_state["new_items"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust,
        "quantity": quantity,
        "unit_price": unit_price
    })


def set_item_to_remove(session_state, item_id: int) -> None:
    """Adicionar um item à lista de itens para remover do pedido."""
    print("Marcando item para remoção no estado")
    session_state["to_delete_items"].append(item_id)


async def find_order_by_document(session_state, client_document: str) -> list:
    """Buscar pedidos pelo documento do cliente e retorna a lista de pedidos."""
    print("Buscando pedidos por documento")
    try:
        response = await make_request('GET', f'/api/orders/filter/?client_document={client_document}')
        
        if not response or not isinstance(response, list) or len(response) == 0:
            print(f"Nenhum pedido encontrado para o documento {client_document}.")
            return []
        
        if len(response) == 1:
            session_state["selected_order_id"] = response[0]["id"]
            session_state["selected_order"] = response[0]
            print(f"Um pedido encontrado e selecionado: #{response[0]['id']}")

        session_state["orders_list"] = response
        print(f"{len(response)} pedidos encontrados.")
        return response
        
    except Exception as e:
        print(f"Erro ao buscar pedidos: {str(e)}")
        return []


async def find_order_by_id(session_state, order_id: int) -> dict | None:
    """Buscar um pedido específico pelo ID e retorna os detalhes do pedido."""
    print("Buscando pedido por ID")
    
    try:
        response = await make_request('GET', f'/api/orders/{order_id}/')
        
        if not response:
            print(f"Nenhum pedido encontrado com o ID {order_id}.")
            return None
        
        session_state["selected_order_id"] = order_id
        session_state["selected_order"] = response
        print(f"Pedido #{order_id} selecionado com sucesso!")
        return response
        
    except Exception as e:
        print(f"Erro ao buscar pedido: {str(e)}")
        return None


def find_order_items(session_state) -> list:
    """Listar os itens do pedido selecionado."""
    print("Listando itens do pedido selecionado")
    
    selected_order = session_state.get("selected_order")
    if not selected_order:
        print("Nenhum pedido selecionado.")
        return []
    
    items = selected_order.get("items", [])
    if not items:
        print("Este pedido não possui itens.")
        return []
    
    return items


async def process_order_updates(session_state) -> str:
    """Processar todas as atualizações pendentes no pedido."""
    print("Enviando todas as atualizações para a API")
    
    order_id = session_state.get("selected_order_id")
    if not order_id:
        return "❌ Nenhum pedido selecionado. Por favor, selecione um pedido primeiro."
    
    results = []
    
    new_items = session_state.get("new_items", [])
    if new_items:
        try:
            items_data = []
            for item in new_items:
                items_data.append({
                    "name": f"{item['name']} - {item['size']} - {item['crust']}",
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"]
                })
            
            data = {"items": items_data}
            response = await make_request('PATCH', f'/api/orders/{order_id}/add-items/', data)
            results.append(f"✅ {len(items_data)} item(ns) adicionado(s) com sucesso!")
            
            session_state["new_items"] = []
            
        except Exception as e:
            results.append(f"❌ Erro ao adicionar itens: {str(e)}")
    
    new_user_address = session_state.get("new_user_address", {})
    if new_user_address and new_user_address.get("street_name"):
        try:
            data = {"delivery_address": new_user_address}
            response = await make_request('PATCH', f'/api/orders/{order_id}/update-address/', data)
            results.append(f"✅ Endereço atualizado com sucesso!")
            
            session_state["new_user_address"] = {}
            
        except Exception as e:
            results.append(f"❌ Erro ao atualizar endereço: {str(e)}")
    
    to_delete_items = session_state.get("to_delete_items", [])
    if to_delete_items:
        for item_id in to_delete_items:
            try:
                response = await make_request('DELETE', f'/api/orders/{order_id}/items/{item_id}/')
                results.append(f"✅ Item {item_id} removido com sucesso!")
            except Exception as e:
                results.append(f"❌ Erro ao remover item {item_id}: {str(e)}")
        
        session_state["to_delete_items"] = []
    
    if not results:
        return "ℹ️ Nenhuma alteração pendente para processar."
    
    return "\n".join(results) + "\n\n🎉 Todas as atualizações foram processadas!"