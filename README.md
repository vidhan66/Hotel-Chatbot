# 🏨 Ralton Hotel Virtual Assistant 🤖

A conversational AI assistant for Ralton Hotel, Shillong. This chatbot helps guests with hotel services, local tourist information, fare estimation, and more – all through text or voice input.

---

## 🚀 Features

- ✅ Query hotel services (check-in/out time, food, laundry, cleaning)
- 🗺️ Recommend tourist attractions & local dishes
- 🚕 Estimate taxi fare to destinations
- 🗣️ Voice input supported via microphone
- 📋 Feedback collection via Google Forms

---

## 📸 Demo

> 🔹 *Short video showing chatbot in action (Streamlit + voice/text chat)*

---

## 🧠 Tech Stack

| Layer              | Tool / Framework                         |
|--------------------|-------------------------------------------|
| LLM                | Gemini 2.0 Flash (Google API)             |
| Embeddings         | `BAAI/bge-small-en-v1.5` (Hugging Face)   |
| Vector Store       | ChromaDB                                  |
| Backend Logic      | LangChain Agents + Tools                  |
| UI                 | Streamlit                                 |
| Voice Input        | SpeechRecognition (Google Web Speech API) |
| Deployment         | Localhost           |

---

## 🛠️ Setup Instructions

1. Clone the repo  
   ```bash
   git clone https://github.com/vidhan66/Hotel-Chatbot.git
   cd Hotel-Chatbot

2. API Key Setup

This project requires a Google Generative AI API key (Gemini Flash 2.0) for response generation.

* Steps to Generate:
1. Go to [Google AI for Developers](https://ai.google.dev/gemini-api/docs/models).
2. Sign in with your Google account.
3. Select "Gemini 2.0 Flash" model and click on try it on Google AI Studio.
4. Create a new API key under **"Get API Key"** section.
5. Copy the API key.
    ```bash
    GOOGLE_API_KEY=your_key

3. Install dependencies
    ``` bash
    pip install -r requirements.txt

4. Run the chatbot:
   * CLI version: ```bash python cli.py
   * Streamlit version: ```bash streamlit run app.py
  
## 👥 Use Cases
- A guest wants to know the check-out time or food menu.
- A tourist asks for recommendations near the hotel.
- Someone needs help booking a taxi to Laitlum Canyon.
- A user wants to provide feedback after their stay.
- 
## 🔍 Limitations & Future Enhancements
- Currently only supports English.
- No real-time user account system or database integration.
- Future: Add booking database and payment system.

## 🔒 Note on Data Privacy
No sensitive user data is collected. Google Forms used for feedback/bookings are not linked to response sheets.

## 👤 Author

- **Vidhan Bansal**
-  GitHub: (https://github.com/vidhan66)
-  LinkedIn:(https://www.linkedin.com/in/vidhan-bansal-9bb784290/)
