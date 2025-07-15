from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel

class DestinationInput(BaseModel):
    destination: str

system_prompt = ChatPromptTemplate.from_messages([
    ("system","""
    You are a helpful assistant for Ralton Hotel in Shillong.

    Only handle:
    - Tourist and Famous dishes recommendations
    - Travel Options
    - Hotel services (check in/check out time, last kitchen order time,food, laundry, cleaning)
    - Fare estimation
    - Never invent or assume website URLs, links, phone numbers, or email addresses.
    - Only respond with links if they are explicitly retrieved from data or given via tools.
     
    
    If the user ask for any details which will need number, always use ask_hotel_info tool.
    Redirect unrelated queries via the general_chat tool. Always assume user is at Ralton Hotel, Shillong.
    """),
    MessagesPlaceholder(variable_name ="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

with open("tourist_places.txt", "r", encoding="utf-8") as file:
    tourist_places = file.read()

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",
    temperature=0.8,
    google_api_key="Your_api_key"
)


# Load hotel services & tourist data
loader1 = TextLoader("hotel_services.txt",encoding="utf-8")
loader2 = TextLoader("tourist_places.txt")
loader3 = TextLoader("famous_dish.txt")
docs1 = loader1.load()
docs2 = loader2.load()
docs3 = loader3.load()
docs = docs1 + docs2 + docs3

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(splits, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
hotel_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever,verbose = True)

@tool
def ask_hotel_info(query: str) -> str:
    """Search hotel services,tourist place, and famous dishes info."""
    return hotel_chain.invoke(query)

@tool
def general_chat(message: str) -> str:
    """Responds to general conversation or small talk and user queries for which other tools are not useful."""
    return str(llm.invoke(message))

@tool
def get_booking_form(request_type: str) -> str:
    """Returns Google Form link for requested booking type (food,cleaning,laundry)."""
    if "food" in request_type.lower():
        return "https://forms.gle/Fz9YMS53CjNtirw77"
    elif "cleaning" in request_type.lower():
        return "https://forms.gle/Wiqpeanqhtzw2HFk9"
    elif "laundry" in request_type.lower():
        return "https://forms.gle/WWduUjDkS6VyyWcu6"
    else:
        return "Please contact reception for this service."

@tool
def travel_fare_estimation(input : DestinationInput) -> str:
    """Estimates travel options and taxi fare to a tourist spot based on distance and terrain from tourist_places.txt"""
    prompt = PromptTemplate(
        template="""
    You are a helpful travel assistant at Ralton Hotel in Shillong.

    A guest wants to visit **{destination}**. Based on the retrieved information (such as distance, description, terrain), provide a useful travel recommendation.

    Your response should include:
    - A **clear suggestion to use hotel-arranged taxi** as the first option.
    - The **approximate distance** and **estimated travel time** from the hotel.
    - A **reasonable taxi fare estimate** (use ₹20–25/km as base rate, and adjust slightly for uphill or remote areas).

    Only **if the guest specifically asks**, you may briefly mention alternative modes (shared taxi, public bus, walking) — but **do NOT include fare** for them. Mention if they are unreliable or uncomfortable.

    If you cannot find relevant information about the destination, say:  
    _"Sorry, I couldn't find travel details for that place."_

    Respond naturally and helpfully. Example format:

    **Estimated fare to [place]: ₹[amount]**  
    Optional: *Distance and travel time if relevant*

    """,
    input_variables=["destination"]
    )

    format_prompt = prompt.format(destination = input.destination)
    return hotel_chain.invoke(format_prompt)

tools = [ask_hotel_info, get_booking_form, travel_fare_estimation, general_chat]

agent_executor = AgentExecutor(
    agent=create_tool_calling_agent(llm=llm, prompt=system_prompt, tools=tools),
    tools=tools, verbose=True
)

