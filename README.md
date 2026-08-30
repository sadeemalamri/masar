# 🌴 Masar (مسار)

A multi-agent Python + Gradio system that helps Saudi university students discover the most suitable career path for them, based on their major, education level, interests, skills, and development goal.

## 👥 Team

| Name | Role |
|---|---|
| Wasan Shaker | Idea Owner, Prototype Designer, Initial Prototype & First Programming Version |
| Sadeem Alamri | Programming |
| Bushra Alzeghabi | Programming |
| Tala Alghamdi | Programming |
| Jana Binjabi | Idea Presentation & Communication |

## ✨ Features

- **Agent 1 — Profile & Career Alignment Analyst**: Analyzes the student's profile and proposes an initial career path and learning roadmap.
- **Agent 2 — Recommendation Refiner & Career Strategist**: Reviews Agent 1's output, improves it, and ensures it's consistent with the selected duration.
- **Agent 3 — Educational Resource Hunter**: Suggests learning resources (only after user approval), and validates that links actually work before displaying them.
- **Human-in-the-Loop (HITL)**: Agent 3 only runs after the user explicitly approves the recommendation.
- **Guardrails**: Input validation, a maximum text length, and filtering for prompt-injection attempts.
- **Memory**: Keeps the last 5 recommendations within the user's session.
- **Bilingual interface (English / Arabic)** with a language switcher — defaults to English, and flips to a full Arabic RTL layout with one click. Built with Gradio, using a custom green theme.

## 🧱 Tech Stack

- Python + [Gradio](https://www.gradio.app/)
- [OpenAI API](https://platform.openai.com/) (`gpt-4o-mini` model)
- Link validation via `urllib`

## ⚙️ Running Locally

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd masar
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   - Copy `.env.example` to a file named `.env`
   - Add your key:
     ```
     OPENAI_API_KEY=sk-...
     ```

4. Run the app:
   ```bash
   python app.py
   ```

## ▶️ Running on Google Colab

The code automatically reads the key from **Colab Secrets** under the name `OPENAI_API_KEY`. To expose the app as a public link from Colab, change the last line in `app.py` to:
```python
demo.launch(share=True)
```

## 🔐 Security Note

Never commit your real OpenAI API key to GitHub. The `.env` file is already excluded via `.gitignore`.

## 📂 Project Structure

```
masar/
├── app.py            # Full application code (agents + UI)
├── requirements.txt  # Dependencies
├── .env.example      # Example environment variables file
├── .gitignore
└── README.md
```

## 📝 License

This is an educational project — add whichever license fits your needs (e.g. MIT).
