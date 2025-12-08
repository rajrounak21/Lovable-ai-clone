# Lovable-ai Clone

**An Autonomous Multi-Agent AI Web Architect**

This project is a powerful AI development tool capable of planning, architecting, coding, and reviewing full-stack web applications from natural language prompts. Inspired by Lovable.dev, it enforces premium design standards (Tailwind CSS, Dark Mode, Glassmorphism) automatically.

## 🚀 Features

*   **Autonomous Multi-Agent Workflow**: four specialized agents (Planner, Architect, Coder, Reviewer,Previewer) collaborate to build software.
*   **Self-Healing Code**: The Reviewer Agent detects bugs, quality issues, and logic errors (e.g., duplicate events) and fixes them before delivery.
*   **Premium UI Generation**: Built-in prompts enforce a high-quality aesthetic using Tailwind CSS and modern UI patterns.
*   **Live Preview**: Integrated FastAPI backend serves a real-time preview of the generated application.
*   **Project Download**: One-click ZIP download of the entire generated codebase.

## 🛠️ Tech Stack

*   **Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful multi-agent system)
*   **Framework**: [LangChain](https://www.langchain.com/)
*   **LLMs**: GPT-4o / GPT-4o-mini (via OpenAI), openai/gpt-oss-120b (via Groq)
*   **Backend**: FastAPI
*   **Frontend**: Tailwind CSS (CDN), Jinja2 Templates

## 📦 structure

```
├── app_builder/        # Core Agent Logic
│   ├── graph.py        # LangGraph State Machine
│   ├── states.py       # Agent states what they need to do at each step
│   ├── prompts.py      # System Prompts (Design System enforced)
│   └── tools.py        # File I/O and Analysis Tools
├── templates/          # UI Templates
│   └── index.html      # Main App Builder Interface
├── generated_project/  # Output directory for AI-created apps
├── main.py             # FastAPI Entrypoint
└── requirements.txt    # Dependencies
```

## ⚡ Getting Started

### Prerequisites

*   Python 3.10+
*   OpenAI API Key (Set in `.env`)
*   Groq API Key (Optional, for specific models)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/rajrounak21/Lovable-ai-clone.git
    cd Lovable-ai-clone
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment**:
    Create a `.env` file in the root:
    ```env
    OPENAI_API_KEY=your_key_here
    GROQ_API_KEY=your_key_here
    ```

### Usage

1.  **Run the Server**:
    ```bash
    python main.py
    ```

2.  **Open the Builder**:
    Navigate to `http://127.0.0.1:8000` in your browser.

3.  **Generate an App**:
    *   Enter a prompt (e.g., "Create a modern Weather Dashboard").
    *   Watch the agents plan and build your app in the terminal.
    *   View the result in the live preview window.
    *   Click **Download ZIP** to save your project.

## 🛡️ License

This project is open-source and available under the MIT License.

## 💡 Example Prompts

Try these prompts to test the capabilities of the agent:

*   **Todo Web Application**: "Build a beautiful Todo App with dark mode, where I can add, edit, delete, and filter tasks."
*   **Modern Calculator**: "Create a fully functional Calculator with a glassmorphism UI, supporting basic arithmetic operations."
*   **BMI Calculator**: "Build a BMI Calculator that takes height and weight inputs, calculates the index, and shows the health category with a colorful gauge."

