from dotenv import load_dotenv
import os
from agno.tools.duckdb import DuckDbTools
from difflib import get_close_matches

load_dotenv()
db_path = os.getenv("SQLITE_DB_PATH")

duckdb_tools = DuckDbTools(
    db_path=db_path, 
    read_only=True  
)


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
