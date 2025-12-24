import os
import sys
import json
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

os.environ["OPENAI_API_KEY"] = "key"

if "OPENAI_API_KEY" not in os.environ:
    sys.exit()

categories = {
    "A) Single-Department Questions": [
        "What are the mandatory courses offered in the 1st semester of Software Engineering?",
        "What is the main objective of the course SE 302 (Software Architecture)?",
        "List the weekly topics for the CE 216 (Logic Circuits Design) course in Computer Engineering.",
        "How many ECTS credits is the IE 301 (Operations Research I) course in Industrial Engineering?",
        "What are the prerequisites for the course EEE 301 (Linear Control Systems)?",
        "Which physics courses are required for the Computer Engineering department?",
        "Does the Software Engineering department offer a course on 'Mobile Application Development'?",
        "What is the description of the senior project course (SE 499) in Software Engineering?",
        "In which semester is the MATH 101 (Calculus I) course taken by Industrial Engineering students?",
        "What are the mandatory 'Second Foreign Language' options mentioned for Electrical and Electronics Engineering?"
    ],
    "B) Topic-Based Search": [
        "Which engineering departments offer courses related to 'Artificial Intelligence' or 'Machine Learning'?",
        "Find courses across all departments that cover 'Probability' and 'Statistics'.",
        "Which courses include 'Python' programming in their weekly topics or description?",
        "Are there any courses related to 'Signal Processing' in the Faculty of Engineering?",
        "Which departments require an 'Occupational Health and Safety' course?",
        "Find courses that focus on 'Database Management' systems.",
        "Which courses cover 'Optimization' techniques?",
        "Are there any courses regarding 'Computer Networks' or 'Network Security'?",
        "Which courses discuss 'Ethics' in engineering?",
        "Find courses that involve 'Physics' or 'Mechanics' content."
    ],
    "C) Cross-Department Comparison": [
        "What are the common freshman (1st year) courses between Software Engineering and Industrial Engineering?",
        "Compare the physics requirements for Computer Engineering and Electrical-Electronics Engineering?",
        "Which department focuses more on 'Hardware' and 'Circuits': Software Engineering or Electrical-Electronics Engineering?",
        "Do both Computer Engineering and Software Engineering students take the 'Formal Languages and Automata' course?",
        "Is the internship (Summer Practice) duration or ECTS the same for all engineering departments?",
        "Which department emphasizes 'Supply Chain Management' more: Industrial Engineering or Computer Engineering?",
        "Are the 'Calculus' (Math) courses the same for all four engineering departments?",
        "List the programming-focused courses in Software Engineering versus Industrial Engineering.",
        "Do all departments take the same 'Academic Skills in English' (ENG 101/102) courses?",
        "Is there a difference in the ECTS value of the Senior Project between SE and EEE?"
    ],
    "D) Quantitative / Counting Questions": [
        "How many ECTS credits is the 'Introduction to Programming' course?",
        "How many elective courses must a Software Engineering student take in the 8th semester?",
        "What is the total ECTS value of the first semester for Computer Engineering?",
        "How many physics courses are mandatory in the Electrical-Electronics Engineering curriculum?",
        "What is the semester with the highest number of mandatory courses in Industrial Engineering?",
        "How many 'University Elective' courses are required in the Software Engineering curriculum?",
        "What is the total duration (in weeks) of the syllabus for SE 302?",
        "How many different 'Second Foreign Language' courses are listed in the database?",
        "What is the credit load (Local Credit) of the MATH 101 course?",
        "How many internship (summer practice) courses are there in the SE curriculum?"
    ],
    "E) Hallucination / Trap Questions": [
        "Does the Software Engineering department offer a course on 'Quantum Thermodynamics'?",
        "Is there a compulsory course called 'Introduction to Astrophysics' in Computer Engineering?",
        "Can I take a course on 'Ancient Egyptian History' as a departmental elective in EEE?",
        "Does the Industrial Engineering curriculum include 'Veterinary Surgery'?",
        "Is 'Underwater Basket Weaving' a valid university elective in the Faculty of Engineering?",
        "Do Software Engineering students take a mandatory course on 'Advanced Magic Spells'?",
        "Is there a course code SE 999 related to 'Time Travel Mechanics'?",
        "Does the Computer Engineering department teach 'Culinary Arts and Gastronomy'?",
        "Is 'Zombie Survival Strategies' listed in the weekly topics of any engineering course?",
        "Can I graduate from Industrial Engineering by taking 'Fashion Design' courses?",
        "Is there a course specifically about 'Pokemon Training' in the curriculum?",
        "Does the EEE department require a 'Piano Performance' course?",
        "Is 'Introduction to Astrology' (Horoscopes) a core course in Software Engineering?",
        "Do students take 'Crypto-Zoology' (Study of Bigfoot) in their 3rd year?",
        "Is there a 'Nuclear Reactor Design' course for Software Engineering students?",
        "Does the curriculum include a course on 'How to train your dragon'?",
        "Is 'Telepathy 101' offered as a technical elective?",
        "Do Computer Engineering students take 'Dental Anatomy'?",
        "Is there a course focused on 'Flat Earth Theory' in the Physics department?",
        "Does the SE curriculum include a mandatory module on 'Stand-up Comedy'?"
    ]
}

def run_tests():
    if not os.path.exists("./ieu_course_db"):
        sys.exit()

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(persist_directory="./ieu_course_db", embedding_function=embeddings)
    
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={'k': 100}
    )
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    template = """You are an academic assistant for Izmir University of Economics.
    
    Answer the question based strictly on the provided Context.

    1. If the user asks for a specific Semester, check the 'Semester' field in the text. Only list courses that match.
    2. If the user asks for Prerequisites, check the 'Prerequisites' field for that specific course.
    3. If the user asks about a Topic, check descriptions and topics.
    4. If the info is not in the context, say "I don't have information about that."

    Context:
    {context}

    Question: {question}

    Answer:
    """
    prompt = PromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n--- ENTRY ---\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    json_filename = "test_results.json"
    
    final_results = {}
    if os.path.exists(json_filename):
        with open(json_filename, "r", encoding="utf-8") as f:
            try:
                final_results = json.load(f)
            except:
                final_results = {}

    total_questions = sum(len(q_list) for q_list in categories.values())
    current_count = 0

    print(f"Starting Categorized Test for {total_questions} questions...\n")

    for category_name, questions_list in categories.items():
        print(f"--- Processing: {category_name} ---")
        
        if category_name not in final_results:
            final_results[category_name] = {}

        for q in questions_list:
            current_count += 1
            print(f"[{current_count}/{total_questions}] Asking: {q}")
            
            try:
                answer = rag_chain.invoke(q)
                final_results[category_name][q] = answer
            except Exception as e:
                final_results[category_name][q] = f"ERROR: {str(e)}"

            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(final_results, f, ensure_ascii=False, indent=4)
        
        print(f"--- Completed: {category_name} ---\n")
            
    print(f"All tests finished! Results saved to '{json_filename}'.")

if __name__ == "__main__":
    run_tests()