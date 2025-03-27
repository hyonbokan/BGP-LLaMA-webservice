# BGP-LLaMA Webservice

## Overview
**BGP-LLaMA Webservice** is an AI-powered web application designed for **BGP routing analysis and anomaly detection**. It integrates an **instruction fine-tuned LLaMA model** and **GPT-4o-mini** for automated BGP analysis, providing real-time and historical insights in a user-friendly interface.

The system allows users to interact with an **LLM-powered chatbot**, receive **natural language BGP insights**, and execute **extracted code for deeper analysis**.

## Demo
🔗 **Live Web App**: [BGP-LLaMA](https://llama.cnu.ac.kr/)  

## System Requirements
### Recommended Server Configuration:
- **OS**: Ubuntu 20.04+ / Debian 11+  
- **Python**: 3.9+  
- **Node.js**: 16+  
- **PostgreSQL**: 14+  
- **Hugging Face Transformers**: Required for LLaMA integration  
- **CUDA**: GPU acceleration  
- **Nginx**: Reverse proxy  
- **Daphne**: ASGI server for asgi views and WebSockets
- **Docker & Docker Compose:**: Containerized deployment

## Key Technology

### Backend:
- Django (ASGI) – Framework for handling API endpoints, WebSockets, and LLM interactions.
- Daphne – ASGI server to support WebSockets.
- FastAPI - Handles SSE-based communication with the LLM.
- PostgreSQL – Database for storing conversation ID and chat history
- Hugging Face Transformers – Model integration for BGP-LLaMA.
- OpenAI API – Integrated GPT-4o-mini for alternative chatbot responses.
- SSE (Server-Sent Events) – Real-time streaming responses from FastAPI.
- WebSockets **(Legacy)** – Real-time interaction support with Django consumers  (code stored in [here](./app_1/consumers/)).

### Frontend
- React – High-performance UI framework.
- Redux Toolkit – State management for seamless user interaction.
- Material-UI (MUI) – Consistent and modern UI design.
- Axios – Handles API requests.
- SSE – Used for LLM interaction in production.
- TypeScript – Ensures type safety in the React app.
- WebSockets **(Legacy)** – Live interaction with the LLM.

### DevOps
- Nginx – Reverse proxy for ASGI-based WebSockets, FastAPI SSE, and API calls.
- Daphne – ASGI server for handling Django WebSocket connections.
- Certbot – SSL certificate management for HTTPS.
- Docker – Containerization for scalable deployment.
- Docker Compose – Orchestration of services including PostgreSQL, Nginx, Daphne, and FastAPI.