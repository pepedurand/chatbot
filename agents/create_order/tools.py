from datetime import date
from ..common_tools import make_request


def set_item(session_state, pizza_name: str, size: str, crust: str, quantity: int, unit_price: float) -> None:
    """Adicionar uma pizza à lista de itens do pedido."""
    print("Adicionando pizza ao pedido")
    session_state["pizzas"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust,
        "quantity": quantity,
        "unit_price": unit_price
    })


def set_user_name(session_state, name: str) -> None:
    """Definir o nome do usuário."""
    print("Salvando nome do cliente")
    session_state["user_name"] = name


def set_user_document(session_state, document: str) -> None:
    """Definir o documento do usuário."""
    print("Salvando documento do cliente")
    session_state["user_document"] = document


def set_user_address(session_state, street_name: str, number: int, reference_point: str, complement: str) -> None:
    """Definir o endereço de entrega do usuário."""
    print("Salvando endereço do cliente")
    session_state["address"] = {
        "street_name": street_name,
        "number": number,
        "reference_point": reference_point,
        "complement": complement
    }


async def send_data_to_api(session_state) -> str:
    """Enviar os dados do pedido para a API externa e retornar uma mensagem de sucesso."""
    print("Preparando pedido para envio")
    
    if not session_state.get("user_name") or not session_state.get("user_name").strip():
        return "❌ Erro: Nome do cliente não foi informado. Por favor, informe seu nome."
    
    if not session_state.get("user_document") or not session_state.get("user_document").strip():
        return "❌ Erro: Documento do cliente não foi informado. Por favor, informe seu CPF."
    
    address = session_state.get("address", {})
    if not address or not address.get("street_name") or not address.get("number"):
        return "❌ Erro: Endereço completo não foi informado. Por favor, informe rua e número."
    
    pizzas = session_state.get("pizzas", [])
    if not pizzas or len(pizzas) == 0:
        return "❌ Erro: Nenhum item foi adicionado ao pedido. Por favor, adicione pelo menos uma pizza."
    
    for i, item in enumerate(pizzas):
        if not all(key in item for key in ['name', 'size', 'crust', 'quantity', 'unit_price']):
            return f"❌ Erro: Item {i+1} do pedido está incompleto. Faltam informações obrigatórias."
    
    address = session_state.get("address", {})
    
    order_data = {
        "client_name": str(session_state.get("user_name", "")),
        "client_document": str(session_state.get("user_document", "")),
        "delivery_date": date.today().isoformat(),
        "delivery_address": {
            "street_name": str(address.get("street_name", "")),
            "number": int(address.get("number", 0)) if address.get("number") else 0,
            "complement": str(address.get("complement", "")),
            "reference_point": str(address.get("reference_point", ""))
        },
        "items": [
            {
                "name": f"{item['name']} - {item['size']} - {item['crust']}",
                "quantity": int(item["quantity"]),
                "unit_price": float(item["unit_price"]),
            }
            for item in session_state.get("pizzas", [])
        ],
    }
    
    try:
        print("Enviando pedido para API")
        response = await make_request('POST', '/api/orders/', order_data)
        print("Pedido enviado com sucesso!")
        return "Pedido enviado para confirmação com sucesso! 🎉"
    except Exception as e:
        print(f"Erro ao enviar pedido: {str(e)}")
        error_msg = str(e)
        if "400" in error_msg:
            return "❌ Erro: Os dados do pedido estão incompletos ou inválidos. Verifique se todas as informações foram preenchidas corretamente."
        elif "404" in error_msg:
            return "❌ Erro: Serviço de pedidos não encontrado. Tente novamente mais tarde."
        elif "500" in error_msg:
            return "❌ Erro interno do servidor. Tente novamente mais tarde."
        else:
            return f"❌ Erro ao enviar pedido: {error_msg}"