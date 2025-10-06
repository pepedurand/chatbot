# Beauty Pizza - Chatbot de Pedidos

Este projeto é uma solução para o **Desafio Técnico MLE-Spec 1 GenAI**, que consiste em desenvolver um agente de IA autônomo para atuar como atendente da pizzaria "Beauty Pizza". O chatbot é capaz de interagir com clientes, apresentar o cardápio, anotar e modificar pedidos.

## Arquitetura

A solução foi construída utilizando uma arquitetura multiagente com o framework [Agno](https://github.com/Agno-python/agno), garantindo uma separação clara de responsabilidades e um fluxo de conversa coeso.

A arquitetura é composta por três agentes principais:

1. **Agente Orquestrador (`agents/orchestrator`)**:

   - É o ponto de entrada da conversa.
   - Cumprimenta o cliente e identifica a intenção principal (criar um novo pedido ou atualizar um existente).
   - Direciona a conversa para o agente especialista apropriado.

2. **Agente de Criação de Pedidos (`agents/create_order`)**:

   - Especializado em guiar o cliente durante a criação de um novo pedido.
   - Apresenta o cardápio, responde a perguntas sobre sabores e preços, e adiciona itens ao carrinho.
   - Mantém o estado do pedido (sabores, tamanhos, bordas) e calcula o valor total.
   - Finaliza o pedido enviando os dados para a API de pedidos.

3. **Agente de Atualização de Pedidos (`agents/update_order`)**:
   - Gerencia modificações em pedidos já existentes.
   - Busca pedidos pelo CPF do cliente.
   - Permite adicionar ou remover itens e atualizar o endereço de entrega.

### Fontes de Dados

- **Base de Conhecimento (SQLite)**: As informações sobre o cardápio (sabores, ingredientes, tamanhos, bordas e preços) são armazenadas em um banco de dados SQLite e consultadas através de ferramentas (`common_tools.py`) que utilizam DuckDB para acesso.
- **API de Pedidos**: Uma API REST externa é utilizada para persistir e gerenciar os pedidos (criar, atualizar, buscar).

## Recursos

- **Interação Inteligente**: Cumprimenta o cliente e inicia o processo de pedido de forma proativa.
- **Consulta ao Cardápio**: Responde a perguntas sobre sabores, ingredientes e preços, utilizando busca por similaridade para entender o que o cliente deseja.
- **Criação de Pedidos**: Permite ao cliente montar um pedido completo, com múltiplos itens, especificando sabor, tamanho e tipo de borda.
- **Atualização de Pedidos**: Permite que clientes já com pedidos em andamento possam modificá-los.
- **Gerenciamento de Estado**: Mantém o contexto da conversa e do pedido de forma coerente.
- **Execução Simplificada**: O chatbot pode ser iniciado com um único comando no terminal.

## Como Executar

### Pré-requisitos

- Python 3.9+
- Git

### 1. API e Banco de Dados

O chatbot depende de uma API de pedidos e de um banco de dados com o cardápio. Clone e execute o projeto `candidates-case-order-api` para ter o ambiente necessário.

```bash
git clone https://github.com/gbtech-oss/candidates-case-order-api.git
cd candidates-case-order-api
```

Siga as instruções do `README.md` do repositório da API para instalá-la e executá-la. Por padrão, a API rodará em `http://127.0.0.1:8000`.

### 2. Configuração do Chatbot

Clone este repositório em um diretório separado:

```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd chatbot
```

Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate
# No Windows: .\venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto e adicione as seguintes variáveis de ambiente, apontando para os recursos da API:

```env
# Caminho para o arquivo de banco de dados SQLite gerado pela API
SQLITE_DB_PATH=../candidates-case-order-api/database/orders.db

# URL base da API de pedidos
ORDER_API_URL=http://127.0.0.1:8000
```

### 3. Execução

Com a API de pedidos rodando e o ambiente do chatbot configurado, execute o seguinte comando:

```bash
python main.py
```

O chatbot será iniciado no seu terminal e você poderá começar a interagir com ele.

## Estrutura do Projeto

```
.
├── agents/
│   ├── orchestrator/     # Agente que gerencia o fluxo da conversa
│   ├── create_order/     # Agente para criar novos pedidos
│   ├── update_order/     # Agente para atualizar pedidos existentes
│   └── common_tools.py   # Ferramentas compartilhadas (acesso ao DB, etc.)
├── main.py               # Ponto de entrada para executar o chatbot
├── requirements.txt      # Dependências do projeto
└── README.md             # Este arquivo
```
