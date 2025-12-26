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
    
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={'k': 150}
    )
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    template = """You are an expert academic advisor for Izmir University of Economics.
    You have access to a comprehensive list of course data below.
    
    Your goal is to answer the student's question by analyzing the provided Context.
    
    INSTRUCTIONS FOR DIFFERENT QUESTION TYPES:
    
    1. SPECIFIC COURSE DETAILS (e.g., "Objective of SE 311"):
       - Search specifically for the block starting with "Code: SE 311".
       - Do not confuse it with other courses that list SE 311 as a prerequisite.
       - Extract the requested info (Objective, ECTS, etc.) accurately.

    2. SEMESTER LISTING (e.g., "1st Semester courses"):
       - Scan all courses in the context.
       - Identify courses where the 'Semester' field explicitly matches the requested period (e.g., "1. Semester", "1. Year Fall").
       - List all matching courses found.

    3. COUNTING/QUANTITATIVE (e.g., "How many elective courses..."):
       - Manually count the entries in the context that meet the criteria.
       - Provide the final count and list a few examples.

    4. COMPARISON (e.g., "Compare Math requirements of CE vs EEE"):
       - Find the math courses for both departments in the context.
       - Analyze and explain the differences or similarities.

    5. TOPIC SEARCH (e.g., "Courses about Mechanics"):
       - Scan descriptions and topics for the keyword.
       - List the courses that contain this content.

    If you absolutely cannot find the answer in the context after a thorough search, state "I don't have information about that."

    Context:
    {context}

    Question: {question}

    Answer:
    """
    prompt = PromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n--- COURSE ENTRY ---\n".join(doc.page_content for doc in docs)

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