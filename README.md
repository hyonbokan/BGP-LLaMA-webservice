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
- **CUDA**: (for GPU acceleration)  
- **Nginx**: Reverse proxy  
- **Daphne**: ASGI server for handling WebSockets

## Key Technology

### Backend:
- Django (ASGI) – Framework for handling API endpoints, WebSockets, and LLM interactions.
- Daphne – ASGI server to support WebSockets.
<!-- - PostgreSQL – Database for storing user interactions and logs. -->
<!-- Redis – Used for session caching and performance optimization. -->
- Hugging Face Transformers – Model integration for BGP-LLaMA.
- OpenAI API – Integrated GPT-4o-mini for alternative chatbot responses.
- WebSockets – Real-time interaction between users and LLM.
<!-- Celery & Redis – Task queue for executing background tasks. -->

### Frontend
- React – High-performance UI framework.
- Redux Toolkit – State management for seamless user interaction.
- Material-UI (MUI) – Consistent and modern UI design.
- Axios – Handles API requests.
- WebSockets – Live interaction with the LLM.
- TypeScript – Ensures type safety in the React app.

### DevOps
- Nginx – Reverse proxy for ASGI-based WebSockets and API calls.
- Daphne – ASGI server for handling WebSocket connections.
- Certbot – SSL certificate management for HTTPS.
- Docker (**Future Plan**) – Containerization for scalable deployment.