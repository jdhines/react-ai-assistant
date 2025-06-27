# 👋 Minimal CopilotKit + LangGraph Dojo

Get all AG-UI features betwen langgraph and copilotkit working with minimal cloud/framework dependencies.

## Project Structure

- `react-client`: The frontend React application
- `copilot-runtime-service`: The CopilotKit runtime service
- `lang-graph-service`: The LangGraph agent service

```sh
[react-client]
      |
[copilot-runtime-service]
      |
[lang-graph-service]
```

## Setup

1. **Copy environment variables:**

   ```sh
   cp lang-graph-service/.env.example lang-graph-service/.env
   # Edit lang-graph-service/.env and set your OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT
   ```

2. **Create a Python virtual environment**

   ```sh
      python -m venv .venv
      . ./.venv/Scripts/activate
      # use command deactivate to get out of the venv when you want
   ```

3. **Install poetry**
   Install the poetry package manager for python. [See how](https://python-poetry.org/docs/#installing-with-the-official-installer).

4. **Install and start all services:**

   Open a new terminal tab (or shell) for each service, and run:

   ```sh
      cd ../copilot-runtime-service && npm install
      npm run dev
   ```

   ```sh
      cd ../lang-graph-servicereact-client && poetry install
      npm run dev
   ```

- Copilot runtime: http://localhost:4000/copilotkit
- LangGraph agent: http://localhost:8000/copilotkit

---

## Contributing

This repo was cloned from [minimal-copilotkit-langgraph](https://github.com/jrhicks/minimal-copilotkit-langgraph). Open any PRs there. You can find many examples at: https://github.com/CopilotKit/CopilotKit/tree/main/examples

---

## License

MIT
