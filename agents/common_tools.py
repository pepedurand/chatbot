from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.knowledge import Knowledge

load_dotenv()
ORDER_API_URL = os.getenv("ORDER_API_URL")

try:
    ORDERS_API_TIMEOUT = float(os.getenv("ORDERS_API_TIMEOUT", "10"))
except (TypeError, ValueError):
    ORDERS_API_TIMEOUT = 10.0

embedder = OpenAIEmbedder()
vector_db = LanceDb(
    table_name="beauty_pizza_menu",
    uri="/Users/colaborador/ia-case/candidates-case-order-api/vector_db",
    embedder=embedder
)
knowledge = Knowledge(vector_db=vector_db)

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


def get_pizza_prices(pizza_flavour: str) -> str:
    """Recuperar preços de pizza específica usando busca vetorial."""
    print(f"Consultando preços da pizza: {pizza_flavour}")
    
    query = f"preços da pizza {pizza_flavour} todos os tamanhos e bordas"
    results = knowledge.search(query=query, limit=5)
    
    if results and hasattr(results, 'responses') and results.responses:
        response_text = results.responses[0].content if results.responses[0].content else ""
        return response_text
    
    return f"Não encontrei informações sobre a pizza {pizza_flavour}. Consulte o cardápio completo."


def get_pizza_menu() -> str:
    """Recuperar o cardápio completo usando busca vetorial."""
    print("Consultando cardápio completo")
    
    query = "cardápio completo beauty pizza todas as pizzas preços tamanhos bordas"
    results = knowledge.search(query=query, limit=10)
    
    if results and hasattr(results, 'responses') and results.responses:
        response_text = results.responses[0].content if results.responses[0].content else ""
        return response_text
    
    return "Não foi possível carregar o cardápio no momento."