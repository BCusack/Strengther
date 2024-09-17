import streamlit as st
import pandas as pd
from main import get_data
import time

st.set_page_config(page_title="Perpetual Futures Change from Open", layout="wide")

@st.cache_data(ttl=1)  # Cache the data for 1 second to avoid excessive API calls
def fetch_data():
    return get_data()

def color_change(val):
    color = 'green' if val >= 0 else 'red'
    return f'color: {color}'

def main():
    st.title("Perpetual Futures Change from Open")

    placeholder = st.empty()

    while True:
        with placeholder.container():
            start_time = time.time()

            data = fetch_data()
            
            st.subheader("All Pairs")
            
            # Last update time
            end_time = time.time()
            execution_time = end_time - start_time
            st.text(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')} (Execution time: {execution_time:.2f} seconds)")
            
            # Display all pairs
            st.dataframe(
                data.style.map(color_change, subset=['change_from_open'])
                    .format({'change_from_open': '{:.2f}%', 'absChange': '{:.2f}%'}),
                use_container_width=True,
                height=600  # Adjust this value to fit your needs
            )

        # Wait for 1 second before the next update
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
