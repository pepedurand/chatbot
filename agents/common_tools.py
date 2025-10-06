from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException
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


def get_pizza_prices(pizza_flavour: str) -> list:
    """Recuperar preços de pizza do banco de dados baseado no sabor da pizza com busca por similaridade."""
    print("Consultando preços de pizza especifica")
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
    print("Consultando cardápio completo")
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