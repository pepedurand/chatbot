# Beauty Pizza - Chatbot de Pedidos (Versão Vetorial)

Este projeto é uma solução para o **Desafio Técnico MLE-Spec 1 GenAI**, que consiste em desenvolver um agente de IA autônomo para atuar como atendente da pizzaria "Beauty Pizza". O chatbot é capaz de interagir com clientes, apresentar o cardápio, anotar e modificar pedidos.

**🚀 Versão Atual**: Esta versão implementa busca vetorial avançada usando LanceDB e embeddings para melhor compreensão das consultas dos clientes sobre o cardápio.

## Arquitetura

A solução foi construída utilizando uma arquitetura multiagente com o framework [Agno](https://docs.agno.com/introduction), garantindo uma separação clara de responsabilidades e um fluxo de conversa coeso.

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

- **Base de Conhecimento Vetorial (LanceDB)**: As informações sobre o cardápio (sabores, ingredientes, tamanhos, bordas e preços) são armazenadas em um banco de dados vetorial LanceDB, permitindo busca semântica avançada através de embeddings. Isso melhora significativamente a capacidade do chatbot de entender consultas em linguagem natural.
- **Base de Conhecimento (SQLite)**: Banco de dados relacional complementar para consultas estruturadas quando necessário, acessado através de ferramentas (`common_tools.py`) que utilizam DuckDB.
- **API de Pedidos**: Uma API REST externa é utilizada para persistir e gerenciar os pedidos (criar, atualizar, buscar).

## Recursos

- **Interação Inteligente**: Cumprimenta o cliente e inicia o processo de pedido de forma proativa.
- **🔍 Busca Vetorial Avançada**: Utiliza LanceDB com embeddings para compreensão semântica superior das consultas dos clientes, permitindo interpretação mais natural de perguntas sobre o cardápio.
- **Consulta ao Cardápio**: Responde a perguntas sobre sabores, ingredientes e preços, utilizando busca por similaridade vetorial para entender exatamente o que o cliente deseja, mesmo com linguagem coloquial.
- **Criação de Pedidos**: Permite ao cliente montar um pedido completo, com múltiplos itens, especificando sabor, tamanho e tipo de borda.
- **Atualização de Pedidos**: Permite que clientes já com pedidos em andamento possam modificá-los.
- **Gerenciamento de Estado**: Mantém o contexto da conversa e do pedido de forma coerente.
- **Execução Simplificada**: O chatbot pode ser iniciado com um único comando no terminal.

## Requisitos do Sistema

- **Python 3.8+**
- **API Key OpenAI**: Para geração de embeddings (configurada através da variável de ambiente `OPENAI_API_KEY`)
- **Memória**: Recomendado pelo menos 4GB RAM para operações com embeddings
- **Espaço em Disco**: ~500MB para banco de dados vetorial

## Como Executar

### 1. API e Bancos de Dados

O chatbot depende de uma API de pedidos, um banco de dados SQLite com o cardápio e um banco de dados vetorial LanceDB. Clone e execute o projeto `candidates-case-order-api` para ter o ambiente necessário.

```bash
git clone https://github.com/gbtech-oss/candidates-case-order-api.git
cd candidates-case-order-api
```

Siga as instruções do `README.md` do repositório da API para instalá-la e executá-la. Por padrão, a API rodará em `http://127.0.0.1:8000`.

### 2. Configuração do Chatbot

Clone este repositório em um diretório separado:

```bash
git clone https://github.com/pepedurand/chatbot
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

**Principais dependências instaladas**:

- `agno`: Framework de agentes de IA com suporte a LanceDB
- `openai`: Para geração de embeddings vetoriais
- `duckdb`: Para consultas SQL eficientes
- `python-dotenv`: Para gerenciamento de variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto e adicione as seguintes variáveis de ambiente, apontando para os recursos da API:

```env
# Caminho para o arquivo de banco de dados SQLite gerado pela API
SQLITE_DB_PATH=../candidates-case-order-api/database/orders.db

# URL base da API de pedidos
ORDER_API_URL=http://127.0.0.1:8000

# Caminho para o banco de dados vetorial LanceDB (será criado automaticamente pela API)
VECTOR_DB_PATH=../candidates-case-order-api/vector_db

# Chave da API OpenAI (obrigatória para geração de embeddings)
OPENAI_API_KEY=sua_chave_openai_aqui
```

**⚠️ Importante**:

- Certifique-se de que a API `candidates-case-order-api` está configurada para gerar o banco de dados vetorial LanceDB. Isso é essencial para o funcionamento da busca semântica.
- A chave da OpenAI (`OPENAI_API_KEY`) é **obrigatória** para o funcionamento da versão vetorial, pois é usada para gerar os embeddings necessários para a busca semântica.

### 3. Execução

Com a API de pedidos rodando e o ambiente do chatbot configurado, execute o seguinte comando:

```bash
python main.py
```

O chatbot será iniciado no seu terminal e você poderá começar a interagir com ele.

## Estrutura do Projeto

```text
.
├── agents/
│   ├── orchestrator/     # Agente que gerencia o fluxo da conversa
│   ├── create_order/     # Agente para criar novos pedidos (com busca vetorial)
│   ├── update_order/     # Agente para atualizar pedidos existentes (com busca vetorial)
│   └── common_tools.py   # Ferramentas compartilhadas (acesso ao DB vetorial e SQLite)
├── main.py               # Ponto de entrada para executar o chatbot (versão vetorial)
├── requirements.txt      # Dependências do projeto
└── README.md             # Este arquivo
```

## Tecnologias Utilizadas

- **[Agno](https://docs.agno.com/introduction)**: Framework para agentes de IA autônomos
- **LanceDB**: Banco de dados vetorial para busca semântica
- **OpenAI Embeddings**: Para geração de representações vetoriais do conteúdo
- **DuckDB**: Para consultas SQL no banco SQLite
- **SQLite**: Banco de dados relacional para informações estruturadas
- **Python 3.8+**: Linguagem principal do projeto

## Melhorias da Versão Vetorial

Esta versão implementa significativas melhorias em relação à versão anterior:

1. **🎯 Compreensão Melhorada**: O uso de embeddings permite que o chatbot entenda consultas mais naturais e coloquiais sobre o cardápio.

2. **🔍 Busca Semântica**: Busca por similaridade vetorial para encontrar sabores e ingredientes mesmo quando o cliente não usa os nomes exatos.

3. **💬 Interações Mais Naturais**: Melhor interpretação de intenções do cliente, permitindo conversas mais fluidas.

4. **⚡ Performance Aprimorada**: Consultas mais eficientes através do banco vetorial LanceDB.

---

**Desenvolvido por**: [José Durand](https://github.com/pepedurand)  
**Framework**: [Agno](https://docs.agno.com/introduction)  
**Versão**: Vetorial com LanceDB
