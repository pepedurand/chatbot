from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException
from datetime import date
from agno.tools.duckdb import DuckDbTools
import unicodedata
import re
from difflib import get_close_matches

load_dotenv()
db_path = os.getenv("SQLITE_DB_PATH")
ORDER_API_URL = os.getenv("ORDER_API_URL")

try:
    ORDERS_API_TIMEOUT = float(os.getenv("ORDERS_API_TIMEOUT", "10"))
except (TypeError, ValueError):
    ORDERS_API_TIMEOUT = 10.0

# Configurar ferramentas do DuckDB
duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)


def normalize_text(text: str) -> str:
    """Normalizar texto removendo acentos, convertendo para minúsculas e removendo caracteres especiais."""
    if not text:
        return ""
    
    # Converter para minúsculas
    text = text.lower()
    
    # Remover acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Manter apenas letras, números e espaços
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Normalizar espaços
    text = ' '.join(text.split())
    
    return text


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
    session_state["pizzas"].append({
        "name": pizza_name,
        "size": size,
        "crust": crust,
        "quantity": quantity,
        "unit_price": unit_price
    })


def set_user_name(session_state, name: str) -> None:
    """Definir o nome do usuário."""
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
    order_data = {
        "client_name": session_state.get("user_name"),
        "client_document": session_state.get("user_document"),
        "delivery_date": date.today().isoformat(),
        "delivery_address": {
            "street_name": session_state["address"].get("street_name"),
            "number": session_state["address"].get("number"),
            "complement": session_state["address"].get("complement"),
            "reference_point": session_state["address"].get("reference_point")
        },
        "items": [
            {
                "name": f"{item['name']} - {item['size']} - {item['crust']}",
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
            for item in session_state.get("pizzas", [])
        ],
    }
    await make_request('POST', '/api/orders/', order_data)
    return "Pedido enviado para confirmação."


def get_pizza_prices(pizza_flavour: str) -> list:
    """Recuperar preços de pizza do banco de dados baseado no sabor da pizza com busca por similaridade."""
    print(f"[DEBUG] Buscando preços para sabor: '{pizza_flavour}'")
    
    flavours_query = "SELECT DISTINCT sabor FROM pizzas"
    available_flavours = [row[0] for row in duckdb_tools.connection.execute(flavours_query).fetchall()]
    print(f"[DEBUG] Sabores disponíveis: {available_flavours}")
    
    close_matches = get_close_matches(pizza_flavour.lower(), [f.lower() for f in available_flavours], n=1, cutoff=0.3)
    
    if close_matches:
        matched_flavour = None
        for flavour in available_flavours:
            if flavour.lower() == close_matches[0]:
                matched_flavour = flavour
                break
        
        print(f"[DEBUG] Match encontrado: '{pizza_flavour}' -> '{matched_flavour}' (similaridade)")
        
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
        print(f"[DEBUG] Nenhum match similar encontrado para '{pizza_flavour}'")
        results = []
    
    print(f"[DEBUG] Resultados finais: {len(results)} registros")
    print(f"[DEBUG] Dados retornados: {results}")
    
    prices = []
    for row in results:
        prices.append({
            "pizza_name": row[0],
            "size": row[1],
            "crust": row[2],
            "unit_price": row[3]
        })
    print(f"[DEBUG] Lista de preços formatada: {prices}")
    return prices


def get_pizza_menu() -> list:
    """Recuperar o cardápio completo de pizzas do banco de dados."""
    print("[DEBUG] Buscando cardápio completo...")
    query = """
    SELECT p.sabor AS pizza_name, t.tamanho AS size, b.tipo AS crust, pr.preco AS unit_price
    FROM pizzas p
    JOIN precos pr ON p.id = pr.pizza_id
    JOIN tamanhos t ON pr.tamanho_id = t.id
    JOIN bordas b ON pr.borda_id = b.id;
    """
    print(f"[DEBUG] Executando query do menu: {query}")
    results = duckdb_tools.connection.sql(query).fetchall()
    print(f"[DEBUG] Total de itens no cardápio: {len(results)}")
    menu = []
    for row in results:
        menu.append({
            "pizza_name": row[0],
            "size": row[1],
            "crust": row[2],
            "unit_price": row[3]
        })
    print(f"[DEBUG] Sabores únicos no cardápio: {set(item['pizza_name'] for item in menu)}")
    print(f"[DEBUG] Cardápio formatado: {menu[:5]}...")  # Mostra apenas os primeiros 5 para não poluir
    return menu