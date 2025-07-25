from langchain_core.output_parsers import JsonOutputParser
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
import psycopg2
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY2")

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

class Food_order(BaseModel):
    room_no : int
    order_text : str
    order_time: Optional[str] = None

class Laundry_request(BaseModel):
    room_no : int
    clothes_count : int
    request_time : Optional[str] = None

class Cleaning_request(BaseModel):
    room_no : int
    request_time : Optional[str] = None

class Travel_service(BaseModel):
    room_no : int
    travel_type : str
    destination : str
    request_time : Optional[str] = None

class Billing(BaseModel):
    room_no : int

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
    - For any other query give the reception number.
    
    If the user ask for any details which will need number, always use ask_hotel_info tool.
    Redirect unrelated queries via the general_chat tool. Always assume user is at Ralton Hotel, Shillong.
    """),
    MessagesPlaceholder(variable_name ="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

with open("tourist_places.txt", "r", encoding="utf-8") as file:
    tourist_places = file.read()

ITEM_PRICES = {
    "paneer butter masala": 180,
    "bpm": 180,
    "tawa roti": 10,
    "roti": 10,
    "aloo sabji": 90,
    "dal fry": 100,
    "dal": 100,
    "salad": 0,
}

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",
    temperature=0.8
)

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

def get_active_user_id_by_room(room_no: int, conn) -> int:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT user_id FROM rooms 
            WHERE room_no = %s AND check_out IS NULL
            ORDER BY user_id DESC LIMIT 1
        """, (room_no,))
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"No active user found in room {room_no}")
def insert_into_db(query, values):
    with conn.cursor() as cur:
        cur.execute(query, values)
        conn.commit()


@tool
def order_food(data: Food_order) -> str:
    """Parses user's food order and inserts or updates rows in food_orders table."""
    prompt = PromptTemplate.from_template("""
    You are a hotel assistant. The user will give a food order in natural language.
    Your task is to extract all items and create a SINGLE combined order entry with total amount calculation.

    Available items and prices: {available_items}

    Respond only with valid JSON in this exact format, no extra text or markdown:
    {{
        "combined_items": "item1 x quantity1, item2 x quantity2",
        "total_quantity": total_count_of_all_items,
        "total_amount": calculated_total_amount_using_prices_above
    }}
    Example:
    User: I want 2 dal and 3 roti
    (Assuming dal costs 50 and roti costs 10)
    Response: {{
        "combined_items": "dal x2, roti x3",
        "total_quantity": 5,
        "total_amount": 130
    }}
    User: {order_text}
    """)
    parser = JsonOutputParser()
    chain = prompt | llm | parser

    try:
        room_no, text = data.room_no, data.order_text.lower()
        user_id = get_active_user_id_by_room(room_no, conn)

        available_items_str = ", ".join([f"{item}: ₹{price}" for item, price in ITEM_PRICES.items()])
        llm_response = chain.invoke({
            "order_text": text,
            "available_items": available_items_str
        })

        if not all(key in llm_response for key in ["combined_items", "total_quantity", "total_amount"]):
            return "Error: Incomplete order information received."

        combined_item_name = llm_response.get("combined_items", "").strip()
        total_quantity = int(llm_response.get("total_quantity", 0))
        total_amount = float(llm_response.get("total_amount", 0))

        if not combined_item_name or total_quantity <= 0 or total_amount <= 0:
            available_items = ", ".join(ITEM_PRICES.keys())
            return f"Could not create valid order. Available items: {available_items}"

        with conn.cursor() as cur:

            cur.execute("""
                SELECT order_id, item_name, quantity, amount FROM food_orders
                WHERE user_id = %s AND room_no = %s AND status = 'ordered'
                ORDER BY order_time DESC LIMIT 1
            """, (user_id, room_no))
            existing_row = cur.fetchone()

            if existing_row:
                order_id, existing_item_name, existing_qty, existing_amount = existing_row

                updated_item_name = f"{existing_item_name}, {combined_item_name}"
                updated_quantity = existing_qty + total_quantity
                updated_amount = existing_amount + total_amount

                cur.execute("""
                    UPDATE food_orders SET item_name = %s, quantity = %s, amount = %s
                    WHERE order_id = %s
                """, (updated_item_name, updated_quantity, updated_amount, order_id))

                result = f"✅ Updated order: {combined_item_name} (Total items: {updated_quantity}, Total: ₹{updated_amount})"
            else:

                cur.execute("""
                    INSERT INTO food_orders (user_id, room_no, item_name, quantity, amount, status, order_time)
                    VALUES (%s, %s, %s, %s, %s, 'ordered', COALESCE(%s, NOW()))
                """, (user_id, room_no, combined_item_name, total_quantity, total_amount, data.order_time))

                result = f"🆕 Order placed: {combined_item_name} (Total items: {total_quantity}, Total: ₹{total_amount})"

            conn.commit()
        return result

    except Exception as e:
        print(f"General Error: {e}")
        conn.rollback()
        return f"There was an error placing your order: {str(e)}"

@tool
def request_laundry(data: Laundry_request) -> str:
    "Handles laundry requests in database"
    query = """
        INSERT INTO laundry_requests (user_id, room_no, clothes_count, request_time)
        VALUES (%s, %s, %s, COALESCE(%s, NOW()))
    """
    room_no , clothes_count , request_time = data.room_no,data.clothes_count,data.request_time
    user_id = get_active_user_id_by_room(room_no, conn)
    insert_into_db(query, (user_id, room_no, clothes_count, request_time))
    return "✅ Laundry request submitted."

@tool
def request_cleaning(data: Cleaning_request) -> str:
    "Handles cleaning requests in database"
    query = """
        INSERT INTO cleaning_requests (user_id, room_no, request_time)
        VALUES (%s, %s, COALESCE(%s, NOW()))
    """
    room_no, request_time = data.room_no, data.request_time
    user_id = get_active_user_id_by_room(room_no, conn)
    insert_into_db(query, (user_id, room_no, request_time))
    return "✅ Room cleaning scheduled."

@tool
def book_travel(data: Travel_service) -> str:
    "Handles travel services in database"
    query = """
        INSERT INTO travel_service (user_id, room_no, travel_type, destination, request_time)
        VALUES (%s, %s, %s, %s, COALESCE(%s, NOW()))
    """
    room_no, travel_type, destination, request_time = data.room_no, data.travel_type, data.destination,data.request_time
    user_id = get_active_user_id_by_room(room_no, conn)
    insert_into_db(query, (user_id, room_no, travel_type, destination, request_time))
    return f"✅ Travel request to {data.destination} booked."

@tool
def generate_bill(data: Billing) -> str:
    "Generetes bills using database"
    try:
        with conn.cursor() as cur:
            room = int(data.room_no)
            uid = get_active_user_id_by_room(room,conn)
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM food_orders WHERE user_id = %s AND status = 'completed'
            """, (uid,))
            food_total = cur.fetchone()[0]
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM laundry_requests WHERE user_id = %s AND status = 'completed'
            """, (uid,))
            laundry_total = cur.fetchone()[0]
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM travel_service WHERE user_id = %s AND status = 'completed'
            """, (uid,))
            travel_total = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO billing (user_id, room_no, food_total, laundry_total, travel_total)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    food_total = EXCLUDED.food_total,
                    laundry_total = EXCLUDED.laundry_total,
                    travel_total = EXCLUDED.travel_total
            """, (uid, room, food_total, laundry_total, travel_total))
            conn.commit()
        return f"✅ Billing updated:\n🧆 Food: ₹{food_total}\n Laundry: ₹{laundry_total}\n Travel: ₹{travel_total}"
    except Exception as e:
        conn.rollback()
        return f"Error generating bill: {e}"

@tool
def ask_hotel_info(query: str) -> str:
    """Search hotel services,tourist place, and famous dishes info."""
    return hotel_chain.invoke(query)

@tool
def general_chat(message: str) -> str:
    """Responds to general conversation or small talk and user queries for which other tools are not useful."""
    return str(llm.invoke(message))

@tool(args_schema=DestinationInput)
def travel_fare_estimation(destination : str) -> str:
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

    format_prompt = prompt.format(destination = destination)
    return hotel_chain.invoke(format_prompt)

tools = [order_food, request_laundry, request_cleaning, book_travel,
         generate_bill, ask_hotel_info, travel_fare_estimation, general_chat]

agent_executor = AgentExecutor(
    agent=create_tool_calling_agent(llm=llm, prompt=system_prompt, tools=tools),
    tools=tools, verbose=True
)

