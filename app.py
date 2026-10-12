"""Streamlit UI for the shopping assistant agent.

Run with:  streamlit run app.py
"""
import uuid

import streamlit as st

from main import build_agent
from cart.cart_tools import create_cart, get_cart_items
from product.product_tools import get_categories

st.set_page_config(page_title="Shopping Assistant", page_icon="🛒", layout="wide")


# ---------- helpers ----------
def extract_text(message) -> str:
    """Agent content can be a plain string or a list of content blocks."""
    content = message.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block["text"])
        elif isinstance(block, str):
            parts.append(block)
    return "\n".join(parts)


def init_session():
    """One cart + one agent + one conversation thread per browser session."""
    cart_id = create_cart()
    st.session_state.cart_id = cart_id
    st.session_state.agent = build_agent(cart_id)
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []


@st.cache_data(show_spinner=False)
def load_categories():
    return get_categories.invoke({})


if "agent" not in st.session_state:
    init_session()

# ---------- sidebar ----------
with st.sidebar:
    st.divider()
    st.header("🛒 Your Cart")


    @st.fragment
    def cart_panel():
        cart = get_cart_items.invoke({"cart_id": st.session_state.cart_id})
        if not cart.get("success"):
            st.caption(cart.get("message", "Cart unavailable."))
        elif not cart["items"]:
            st.caption("Your cart is empty.")
        else:
            for item in cart["items"]:
                st.markdown(
                    f"**{item['product_name']}**  \n"
                    f"{item['quantity']} × ${item['price']:.2f} = "
                    f"${item['net_price']:.2f}"
                )
            st.divider()
            st.metric("Total", f"${cart['total_price']:.2f}")
        st.button("🔄 Refresh cart", on_click=st.rerun)


    cart_panel()

    st.divider()
    if st.button("🗑️ New chat (new cart)", use_container_width=True):
        init_session()
        st.rerun()

# ---------- chat ----------
st.title("🛒 Shopping Assistant")
st.caption("Search products, read review summaries, and manage your cart.")

if not st.session_state.messages:
    st.info(
        "Try: *What categories do you have?* · *Show me organic honey under $20* · "
        "*Which mango is the best rated?* · *Add 2 of the first one to my cart*"
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("What would you like to search for today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        
        try:
            spinner_placeholder = st.empty()
            spinner_placeholder.markdown("⏳ Thinking...")
            response = st.session_state.agent.stream_events(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"configurable": {"thread_id": st.session_state.thread_id}},
                version = 'v3'
            )
            answer = ""
            message_placeholder = st.empty()
            for kind, item in response.interleave('messages'):
                if kind == "messages":
                    for token in item.text:
                        spinner_placeholder.empty()
                        answer += token
                        message_placeholder.markdown(answer)
            message_placeholder.markdown(answer)
        except Exception as e:
            st.error(f"⚠️ Something went wrong: {e}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    # Cart may have changed – rerun so the sidebar cart refreshes.
    st.rerun()