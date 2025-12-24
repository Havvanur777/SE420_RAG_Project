import json
import os
import sys
import shutil
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

os.environ["OPENAI_API_KEY"] = "key"

if "OPENAI_API_KEY" not in os.environ:
    sys.exit()

def create_db():
    if os.path.exists("./ieu_course_db"):
        shutil.rmtree("./ieu_course_db")

    if not os.path.exists('ieu_courses_final.json'):
        return

    with open('ieu_courses_final.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    for course in data:
        content = (
            f"Code: {course.get('course_code', '')}\n"
            f"Name: {course.get('course_name', '')}\n"
            f"Semester: {course.get('semester', '')}\n"
            f"Dept: {course.get('department', '')}\n"
            f"Type: {course.get('type', '')}\n"
            f"Prerequisites: {course.get('prerequisites', '')}\n"
            f"ECTS: {course.get('ects', '')}\n"
            f"Desc: {course.get('description', '')}\n"
            f"Topics: {course.get('weekly_topics', '')}"
        )
        meta = {
            "code": course.get('course_code', 'Unknown'),
            "dept": course.get('department', 'Unknown')
        }
        documents.append(Document(page_content=content, metadata=meta))

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./ieu_course_db"
    )

    print("Database created.")

if __name__ == "__main__":
    create_db()