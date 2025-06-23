import streamlit as st
from main import normalize_entities, chain

st.set_page_config(page_title="Financial GraphRAG Chatbot", layout="centered")

st.title("🧠📊 Financial GraphRAG Chatbot")
st.write("Ask any financial question about the Inventories of the group companies!")

# Input form
user_query = st.text_input("Enter your question:", "")

if st.button("Ask"):
    if not user_query.strip():
        st.warning("Please enter a question.")
    else:
        # Normalize query
        with st.spinner("Normalizing your question..."):
            normalized = normalize_entities(user_query)
        if normalized is None or normalized.canonicalized_query is None:
            st.error("Could not extract structured query from your question. Please rephrase and try again.")
        else:
            st.info(f"Canonicalized Query: {normalized.canonicalized_query}")
            with st.spinner("Searching the knowledge graph..."):
                try:
                    result = chain.run({"query": normalized.canonicalized_query})
                    st.success("Answer:")
                    st.write(result)
                except Exception as e:
                    st.error(f"Error: {e}")

# Optional: Show the raw normalized object for debugging
with st.expander("Show normalized query and cypher query"):
    if user_query:
        normalized_obj = normalize_entities(user_query)
        st.subheader("Normalized Entities")
        st.json(normalized_obj.model_dump_json())
        if normalized_obj and normalized_obj.canonicalized_query:
            st.subheader("Generated Cypher Query (canonicalized):")
            st.code(normalized_obj.canonicalized_query, language='cypher')

