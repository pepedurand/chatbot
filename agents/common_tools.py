from dotenv import load_dotenv
import os
import asyncio
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException
load_dotenv()
ORDER_API_URL = os.getenv("ORDER_API_URL")

try:
    ORDERS_API_TIMEOUT = float(os.getenv("ORDERS_API_TIMEOUT", "10"))
except (TypeError, ValueError):
    ORDERS_API_TIMEOUT = 10.0

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


