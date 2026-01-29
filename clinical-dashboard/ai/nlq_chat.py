import streamlit as st
from ai.gemini_client import gemini_call

def nlq_interface():
    st.markdown("<h2>💬 Natural Language Query</h2>", unsafe_allow_html=True)
    st.write("Ask any question about the filtered dataset.")

    query = st.text_input("Your question:")
    if st.button("Ask"):
        if not query.strip():
            st.warning("Enter a question.")
            return
        
        prompt = f"""
        You are a clinical data analyst. Answer the following question using the dataset context:

        Question: {query}

        Be factual, concise, and reference data patterns logically.
        """
        result = gemini_call(prompt)
        st.write(result)
