from main import agent_executor
def chat_bot():
    print("Welcome to Ralton Hotel's Virtual Assistant! (type 'exit' to quit)")
    chat_history = []
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("\nBefore you go, we’d love your feedback! 💬")
                print("Please take a moment to fill this short feedback form:")
                print("➡️ Feedback Form: https://forms.gle/tLBy3Tw4icJZDao99")
                print("\nThank you for chatting with us. Have a great day!")
                break
            result = agent_executor.invoke({
                "chat_history": chat_history,
                "input": user_input
            })
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": result["output"]})

            print("Bot:", result["output"])
        except Exception as e:
            print("Error occurred:", e)

if __name__ == "__main__":
    chat_bot()

