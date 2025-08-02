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

def manage_rooms():
    st.subheader("Room Management")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, room_no, check_in, check_out, no_of_person, amount FROM rooms")
            rows = cur.fetchall()
            st.markdown("### Current Rooms")
            for r in rows:
                st.write(
                    f"User ID: {r[0]} → Room: {r[1]} | Check-in: {r[2]} | Check-out: {r[3]} | "
                    f"Persons: {r[4]} | Amount: ₹{r[5]}"
                )

    with st.form("Add Room"):
        st.markdown("### Add New Room Entry")
        room_no = st.text_input("Room No")
        check_in = st.date_input("Check-in Date")
        check_out = st.date_input("Check-out Date")
        no_of_person = st.number_input("Number of Persons", min_value=1, step=1)
        amount = st.number_input("Room Amount (₹)", min_value=0, step=100)

        if st.form_submit_button("Add Room"):
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO rooms (room_no, check_in, check_out, no_of_person, amount)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING user_id
                    """, (room_no, check_in, check_out, no_of_person, amount))
                    new_id = cur.fetchone()[0]
                    conn.commit()
                    st.success(f"Room {room_no} added with User ID {new_id}.")
                    st.rerun()


def show_billing():
    st.subheader("Billing Summary")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM billing")
            rows = cur.fetchall()
            for r in rows:
                st.write(
                    f"User {r[1]} | Room {r[2]} | "
                    f"Food: ₹{r[3]} | Laundry: ₹{r[4]} | Travel: ₹{r[5]} | Other: ₹{r[6]} | "
                    f"Room Charges: ₹{r[7]} | Total: ₹{r[8]}"
                )

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
