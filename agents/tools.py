from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException
from datetime import date
from agno.tools.duckdb import DuckDbTools
from difflib import get_close_matches

load_dotenv()
db_path = os.getenv("SQLITE_DB_PATH")
ORDER_API_URL = os.getenv("ORDER_API_URL")

try:
    ORDERS_API_TIMEOUT = float(os.getenv("ORDERS_API_TIMEOUT", "10"))
except (TypeError, ValueError):
    ORDERS_API_TIMEOUT = 10.0

duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)


async def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Fazer requisição HTTP para a API de pedidos."""
    if not ORDER_API_URL:
        raise RuntimeError("A variável de ambiente ORDER_API_URL não foi configurada.")

    url = f"{ORDER_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    def _do_request() -> Dict:
        try:
            if method.upper() == 'POST':
                response = requests.post(
                    url=url,
                    json=data,
                    timeout=ORDERS_API_TIMEOUT
                )
            else:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=ORDERS_API_TIMEOUT
                )
            
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if response.content and "application/json" in content_type:
                return response.json()
            return {}
        except RequestException as exc:
            raise RequestException(f"Erro na requisição para {url}: {exc}") from exc

    return await asyncio.to_thread(_do_request)


def set_item(session_state, pizza_name: str, size: str, crust: str, quantity: int, unit_price: float) -> None:
    """Adicionar uma pizza à lista de itens do pedido."""
    print("🍕 [AGENTE CRIAR PEDIDOS] Adicionando pizza ao pedido")
    session_state["pizzas"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust,
        "quantity": quantity,
        "unit_price": unit_price
    })


def set_user_name(session_state, name: str) -> None:
    """Definir o nome do usuário."""
    print("🍕 [AGENTE CRIAR PEDIDOS] Salvando nome do cliente")
    session_state["user_name"] = name


def set_user_document(session_state, document: str) -> None:
    """Definir o documento do usuário."""
    session_state["user_document"] = document


def set_user_address(session_state, street_name: str, number: int, reference_point: str, complement: str) -> None:
    """Definir o endereço de entrega do usuário."""
    session_state["address"] = {
        "street_name": street_name,
        "number": number,
        "reference_point": reference_point,
        "complement": complement
    }


async def send_data_to_api(session_state) -> str:
    """Enviar os dados do pedido para a API externa e retornar uma mensagem de sucesso."""
    print("🍕 [AGENTE CRIAR PEDIDOS] Preparando pedido para envio")
    
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
        print("🍕 [AGENTE CRIAR PEDIDOS] Enviando pedido para API")
        response = await make_request('POST', '/api/orders/', order_data)
        print("✅ [AGENTE CRIAR PEDIDOS] Pedido enviado com sucesso!")
        return "Pedido enviado para confirmação com sucesso! 🎉"
    except Exception as e:
        print(f"❌ [AGENTE CRIAR PEDIDOS] Erro ao enviar pedido: {str(e)}")
        error_msg = str(e)
        if "400" in error_msg:
            return "❌ Erro: Os dados do pedido estão incompletos ou inválidos. Verifique se todas as informações foram preenchidas corretamente."
        elif "404" in error_msg:
            return "❌ Erro: Serviço de pedidos não encontrado. Tente novamente mais tarde."
        elif "500" in error_msg:
            return "❌ Erro interno do servidor. Tente novamente mais tarde."
        else:
            return f"❌ Erro ao enviar pedido: {error_msg}"


def get_pizza_prices(pizza_flavour: str) -> list:
    """Recuperar preços de pizza do banco de dados baseado no sabor da pizza com busca por similaridade."""
    print("🍕 [AGENTE CRIAR PEDIDOS] Consultando preços da pizza")
    flavours_query = "SELECT DISTINCT sabor FROM pizzas"
    available_flavours = [row[0] for row in duckdb_tools.connection.execute(flavours_query).fetchall()]
    
    close_matches = get_close_matches(pizza_flavour.lower(), [f.lower() for f in available_flavours], n=1, cutoff=0.3)
    
    if close_matches:
        matched_flavour = None
        for flavour in available_flavours:
            if flavour.lower() == close_matches[0]:
                matched_flavour = flavour
                break
        
        query = """
        SELECT p.sabor AS pizza_name, t.tamanho AS size, b.tipo AS crust, pr.preco AS unit_price
        FROM pizzas p
        JOIN precos pr ON p.id = pr.pizza_id
        JOIN tamanhos t ON pr.tamanho_id = t.id
        JOIN bordas b ON pr.borda_id = b.id
        WHERE p.sabor = ?;
        """
        
        results = duckdb_tools.connection.execute(query, [matched_flavour]).fetchall()
    else:
        results = []
    
    prices = []
    for row in results:
        prices.append({
            "pizza_name": row[0],
            "size": row[1],
            "crust": row[2],
            "unit_price": row[3]
        })
    return prices


def get_pizza_menu() -> list:
    """Recuperar o cardápio completo de pizzas do banco de dados."""
    print("🍕 [AGENTE CRIAR PEDIDOS] Consultando cardápio completo")
    query = """
    SELECT p.sabor AS pizza_name, t.tamanho AS size, b.tipo AS crust, pr.preco AS unit_price
    FROM pizzas p
    JOIN precos pr ON p.id = pr.pizza_id
    JOIN tamanhos t ON pr.tamanho_id = t.id
    JOIN bordas b ON pr.borda_id = b.id;
    """
    results = duckdb_tools.connection.sql(query).fetchall()
    menu = []
    for row in results:
        menu.append({
            "pizza_name": row[0],
            "size": row[1],
            "crust": row[2],
            "unit_price": row[3]
        })
    return menu


async def call_create_order_agent(session_state, user_input: str) -> str:
    """Chamar o agente de criação de pedido."""
    print("🔄 [ORQUESTRADOR] Direcionando para agente de CRIAR PEDIDO")
    print("🍕 [AGENTE CRIAR PEDIDOS] Processando solicitação...")
    
    try:
        # Import do agente apenas quando necessário
        from agents.create_order.agent import agent
        
        # Usa o session_id armazenado no session_state ou None se não existir
        session_id = session_state.get("create_order_session_id")
        response = await agent.arun(user_input, session_id=session_id, add_history_to_context=True)
        
        # Armazena o session_id para futuras interações com o agente de criar pedido
        session_state["create_order_session_id"] = response.session_id
        
        print("✅ [AGENTE CRIAR PEDIDOS] Resposta processada")
        return response.content
        
    except Exception as e:
        print(f"❌ [ERRO] Falha ao carregar agente de criar pedidos: {e}")
        return "Desculpe, estou com problemas técnicos no momento. Tente novamente em alguns instantes."