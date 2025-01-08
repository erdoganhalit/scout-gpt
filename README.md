
# Scout-GPT

Scout-GPT is an agentic AI assistant designed to analyze football data. It integrates personal AWS DynamoDB and Sofascore APIs to provide insights. The app evaluates user queries, routes them to relevant agents, retrieves data, and delivers answers. Basic memory management and human feedback are included for enhanced interaction.

---

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/erdoganhalit/scout-gpt.git
   cd scout-gpt
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY = "sk-..."
   ```
4. Run the app:
   ```bash
   python app.py
   ```
   For terminal-based interaction:
   ```bash
   python terminal_app.py
   ```

---

## Configurations

### Graph Configurations (`graph/config.py`)
- **Agent Settings**: Customize OpenAI models, temperature values, and system messages.
  
### Proxy Configurations (`config.py`)
- **Enable Proxies**:
  ```python
  USE_PROXIES = False
  if USE_PROXIES:
      PROXIES = os.getenv("PROXIES")
  ```
- To use proxies, set `USE_PROXIES` to `True` and add a list of proxies in the `.env` file. Useful when Sofascore API access is restricted.

---

## Features
- **Agentic Query Handling**: Routes user queries to the appropriate agents for data retrieval.
- **Memory Management**: Basic memory for maintaining context.
- **Human Feedback**: Integrated for improving responses.

For detailed functionality, refer to the app.
