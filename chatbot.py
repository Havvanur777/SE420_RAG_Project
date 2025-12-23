import os
import sys
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

os.environ["OPENAI_API_KEY"] = "key"

if "OPENAI_API_KEY" not in os.environ:
    sys.exit()

def start_chat():
    if not os.path.exists("./ieu_course_db"):
        sys.exit()

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(persist_directory="./ieu_course_db", embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    template = """You are an intelligent assistant for Izmir University of Economics.
    Answer the question based ONLY on the following context:

    {context}

    Question: {question}

    If you don't know the answer based on the context, just say "I don't have information about that."
    """
    prompt = PromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("Ready. Type 'exit' to quit.")
    while True:
        q = input("You: ")
        if q.lower() in ['exit', 'quit']: break
        
        try:
            print("AI: ", end="", flush=True)
            for chunk in rag_chain.stream(q):
                print(chunk, end="", flush=True)
            print("\n")
        except Exception as e:
            print(e)

if __name__ == "__main__":
    start_chat()