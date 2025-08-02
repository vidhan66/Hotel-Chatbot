import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

# Mark completed with optional amount
def mark_completed_with_amount(table, request_id, amount=None, amount_column=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if amount is not None and amount_column:
                cur.execute(
                    f"UPDATE {table} SET status = 'completed', amount = %s WHERE request_id = %s",
                    (amount, request_id)
                )
            else:
                cur.execute(
                    f"UPDATE {table} SET status = 'completed' WHERE request_id = %s",
                    (request_id,)
                )
            conn.commit()

# Generic food order handler
def show_orders(table, label):
    st.subheader(f"{label} Orders")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT order_id, user_id, room_no, order_time FROM {table} WHERE status != 'completed'")
            rows = cur.fetchall()
            for r in rows:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
                col1.write(f"ID: {r[0]}")
                col2.write(f"User: {r[1]}")
                col3.write(f"Room: {r[2]}")
                col4.write(f"Time: {r[3]}")
                if col5.button(f"Done {r[0]}", key=f"{table}_{r[0]}"):
                    mark_completed_with_amount(table, r[0])
                    st.success(f"{label} order {r[0]} marked completed.")
                    st.rerun()

# Requests that need amount (Laundry / Travel)
def show_requests_with_amount(table, label, amount_column):
    st.subheader(f"{label} Requests")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT request_id, user_id, room_no, request_time FROM {table} WHERE status != 'completed'")
            rows = cur.fetchall()
            for r in rows:
                col1, col2, col3 = st.columns(3)
                col1.write(f"ID: {r[0]} | Room: {r[2]}")
                col2.write(f"User: {r[1]} | Time: {r[3]}")
                amount = col3.number_input(f"{label} Amount for {r[0]}", key=f"amount_{table}_{r[0]}", min_value=0)
                if st.button(f"Mark {r[0]} Done", key=f"done_{table}_{r[0]}"):
                    if amount > 0:
                        mark_completed_with_amount(table, r[0], amount, amount_column)
                        st.success(f"{label} request {r[0]} marked completed with ₹{amount}.")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid amount before marking done.")

# Requests without amount (Cleaning)
def show_requests(table, label):
    st.subheader(f"{label} Requests")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT request_id, user_id, room_no, request_time FROM {table} WHERE status != 'completed'")
            rows = cur.fetchall()
            for r in rows:
                col1, col2, col3 = st.columns(3)
                col1.write(f"ID: {r[0]} | Room: {r[2]}")
                col2.write(f"User: {r[1]} | Time: {r[3]}")
                if col3.button(f"Done {r[0]}", key=f"{table}_{r[0]}"):
                    mark_completed_with_amount(table, r[0])
                    st.success(f"{label} request {r[0]} marked completed.")
                    st.rerun()

# Room Manager
def manage_rooms():
    st.subheader("Room Management")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT room_no, user_id FROM rooms")
            rows = cur.fetchall()
            for r in rows:
                st.write(f"Room {r[0]} → User {r[1]}")

            with st.form("Add Room"):
                new_room = st.text_input("Room No")
                new_user = st.text_input("User ID")
                if st.form_submit_button("Add Room"):
                    cur.execute("INSERT INTO rooms (room_no, user_id) VALUES (%s, %s)", (new_room, new_user))
                    conn.commit()
                    st.success("Room added!")
                    st.rerun()

# Billing Summary
def show_billing():
    st.subheader("Billing Summary")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM billing")
            rows = cur.fetchall()
            for r in rows:
                st.write(f"User {r[1]} | Room {r[2]} | Food: ₹{r[3]} | Laundry: ₹{r[4]} | Travel: ₹{r[5]} | Other: ₹{r[6]} | Total: ₹{r[7]}")

# Streamlit App
st.title("🏨 Hotel Staff Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧾 Food", "🧺 Laundry", "🧹 Cleaning", "🚗 Travel", "🏠 Rooms & Billing"
])

with tab1:
    show_orders("food_orders", "Food")

with tab2:
    show_requests_with_amount("laundry_requests", "Laundry", "amount")

with tab3:
    show_requests("cleaning_requests", "Cleaning")

with tab4:
    show_requests_with_amount("travel_service", "Travel", "amount")

with tab5:
    manage_rooms()
    show_billing()
