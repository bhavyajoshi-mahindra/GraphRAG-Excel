# 📘 Financial Inventory RAG Chatbot with Neo4j Knowledge Graph

This application enables **Retrieval-Augmented Generation (RAG)** on a complex Excel dataset containing multi-level inventory data across different group companies. It uses **Neo4j Knowledge Graph** for structured representation and **LangChain with Azure OpenAI** for intelligent querying and answer generation.

---

## 💻 Python Environment Setup

1. Create a virtual environment:

```bash
python -m venv code-rag-env
source code-rag-env/bin/activate  # or .\code-rag-env\Scripts\activate on Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 📌 Features

* Converts Excel-based multi-level inventory data into a **Neo4j Knowledge Graph**
* Performs **semantic RAG-style Question Answering** over the graph
* Uses **LangChain + Azure OpenAI** to convert natural language to Cypher and generate accurate responses
* Streamlit-powered UI for easy interaction

---

## 🧩 Data Schema

* **Inventory Levels:** `InventoryLevel1 -> InventoryLevel2 -> InventoryLevel3 -> InventoryLevel4`
* **Relationships:**

  * `(:InventoryLevelX)-[:SUB_INVENTORY]->(:InventoryLevelY)`
  * `(:GroupCompany)-[:HAS_VALUE {amount, year}]->(:InventoryLevel4)`

---

## ⚙️ Setup Instructions

### 🔹 Step 1: Neo4j Desktop Setup

1. Download and install [Neo4j Desktop](https://neo4j.com/download/)

2. Create a new **Project** and inside it, a new **Local DBMS**

3. Start the database and get:

   * **Bolt URL** (e.g., `bolt://localhost:7687`)
   * **Username** (default: `neo4j`)
   * **Password** (set by you)

4. Create a `.env` file in the root directory:

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
AZURE_DEPLOYMENT=your_azure_deployment_name
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_VERSION=2023-05-15
```

### 🔹 Step 2: Create the Knowledge Graph

> 📝 **Update the `.env` file with the correct Neo4j and Azure OpenAI credentials before executing this step.**

Use the notebook `create_kg.ipynb` to:

* Load Excel file (containing inventory and company data)
* Extract and process:

  * Inventory Levels (L1 to L4)
  * Relationships between inventories
  * GroupCompany to Inventory mappings with properties `amount` and `year`
* Push structured nodes and relationships to Neo4j

### 🔹 Step 3: RAG Pipeline Execution

The core RAG logic is defined in [`main.py`](main.py):

1. **Normalization Layer**

   * Uses LLM to extract structured fields: `company_name`, `inventory_type`, `year`, and `canonicalized_query`
2. **Cypher Generation Layer**

   * Generates a Cypher query from the canonicalized query using LangChain prompts
3. **Query Execution**

   * Runs the Cypher on Neo4j and extracts the relevant data
4. **Answer Generation Layer**

   * Uses LLM to synthesize an answer from Cypher results + user query

### 🔹 Step 4: Chatbot UI

Run the Streamlit app with:

```bash
streamlit run streamlit_app.py
```

* Ask financial questions like:

  * "Which inventory tools has the highest difference for AS from 2023 to 2024?"
  * "Show amount change for Machinery across years"
* View normalized query, generated Cypher, and final answer

---

## 📁 File Structure

```text
├── create_kg.ipynb         # Creates and loads Neo4j KG from Excel
├── main.py                 # Core RAG pipeline: query normalization, Cypher gen, LLM response
├── prompts.py              # Required Prompts for RAG and QA 
├── streamlit_app.py        # Streamlit chatbot interface
├── .env                    # Neo4j and Azure OpenAI secrets
├── requirements.txt        # Required packages
```

---

## 🧠 Tech Stack

* **Neo4j** – Graph DBMS for structured inventory data
* **LangChain** – RAG pipeline orchestration
* **Azure OpenAI** – LLM backend (ChatGPT)
* **Streamlit** – UI for chatbot
* **Python** – Core implementation


**⚠️ Note: The Excel data file is not provided in this repository for security and confidentiality reasons.**
