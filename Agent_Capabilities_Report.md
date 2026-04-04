# Autonomous Browser Agent: Capabilities & Operational Scope Report

## 1. Executive Summary
This document outlines the current operational capabilities, technical features, and limitations of the **Autonomous Browser Agent**. The agent is built on a multi-modal, agentic architecture leveraging **LangGraph** for orchestration, **Playwright** for web automation, **Set-of-Marks (SOM)** vision processing for DOM interaction, and a **Multi-LLM Router** (Gemini, Groq, SambaNova, Ollama) for resilient decision-making.

The agent is designed to act as a highly autonomous, Tier-1 automated researcher and data extraction engine, capable of executing complex, multi-step natural language instructions across the internet.

---

## 2. Core Capabilities

### 2.1 Autonomous Web Navigation & Interaction
* **Dynamic Routing:** Navigates to target websites based on natural language prompts (e.g., "Go to Amazon", "Open HackerNews").
* **Smart Interaction:** Locates and interacts with complex UI elements (buttons, search bars, dropdowns) using a combination of Accessibility Trees and Vision-language models (VLM).
* **Set-of-Marks Vision Integration:** Injects bounding boxes over interactive elements on the screen, allowing the LLM to "see" the page layout and interact with elements that lack semantic HTML tags.

### 2.2 Advanced Data Extraction & Synthesis
* **Unstructured Data Scraping:** Extracts raw text, tables, and lists from webpages regardless of the underlying structural layout.
* **Structured Output Formatting:** Utilizes a dedicated "Formatting Agent" to convert scraped, unstructured data into clean JSON, CSV, or Markdown tables based on a defined schema.
* **Document Preparation:** Can browse multiple sources, synthesize the acquired knowledge, and compile professional summary reports or research documents entirely autonomously.

### 2.3 Cross-Site Workflows (Macro-Planning)
* **Multi-Site Reasoning:** The agent utilizes a recursive execution loop. It can plan and execute workflows requiring data from multiple disconnected platforms.
* **Comparative Analysis:** Capable of searching for a product on Website A, extracting the price, navigating to Website B, extracting the competitor price, and returning the optimal purchase recommendation.

### 2.4 Web Research Engine
* **Automated Web Search:** Integrated directly with the `TavilySearch` API, granting the agent the ability to execute its own background internet searches to discover URLs, verify facts, or gather broad market intelligence before taking action inside the browser.

---

## 3. Practical Use-Case Alignments

Based on the current architecture, the agent is highly proficient at the following real-world tasks:
1. **Market Intelligence:** *"Search for AI/ML internship opportunities on Naukri and Glassdoor, extract the top 10 listings, and format them in a table with links and requirements."*
2. **E-Commerce Monitoring:** *"Compare the price of the Sony WH-1000XM5 headphones across Amazon and BestBuy, and tell me the cheapest option."*
3. **Data Aggregation:** *"Go to HackerNews, find the top 5 articles discussing Artificial Intelligence, visit each link, and summarize the key takeaways."*

---

## 4. Current Limitations & Friction Points

To ensure realistic operational expectations, the following limitations must be noted:

### 4.1 Authentication & "Action" Gateways
While the agent can fill out standard forms (e.g., Name, Email), applying for jobs or completing e-commerce checkouts autonomously is bottlenecked by:
* **CAPTCHA & Bot Protections:** Hard blocks like Cloudflare turnstile or Google reCAPTCHA cannot currently be bypassed.
* **Multi-Factor Authentication (MFA):** SSO (Single Sign-On) flows or SMS verification flows require human-in-the-loop intervention.
* **Complex File Uploads:** The current toolset does not bridge operating-system-level file selection dialogs (e.g., uploading a local PDF resume to Workday).

### 4.2 Application State & Complex DOMs
* **Infinite Scrolling:** Highly aggressive lazy-loading (e.g., Twitter feeds, Instagram) limits the agent's ability to extract data beyond the initial viewport + standard scroll range.
* **Shadow DOM Access:** Sites that heavily obfuscate their elements using deeply nested Shadow DOMs may occasionally confuse the vision processor.

---

## 5. Technical Highlights
* **Resilience via API Rotation:** The agent features a seamless LLM fallback router. If rate-limits (HTTP 429) or model unavailability (HTTP 404) are encountered, the agent automatically pivots to alternative providers (e.g., from Gemini to Groq) without dropping the browser session.
* **Asynchronous API Integration:** The system is wrapped in a production-ready FastAPI backend, allowing for background execution and real-time WebSocket status updates for long-running browser tasks.
