import json

def clean_text(text):
    if not text:
        return "Not specified"
    if isinstance(text, list):
        return "; ".join([t for t in text if t])
    return str(text).strip()

def create_rag_documents(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rag_documents = []
        
        for course in data:
            meta_info = (
                f"Course Code: {clean_text(course.get('course_code'))}\n"
                f"Course Name: {clean_text(course.get('course_name'))}\n"
                f"Department: {clean_text(course.get('department'))}\n"
                f"Type: {clean_text(course.get('type'))}\n"
                f"Semester: {clean_text(course.get('semester'))}\n"
                f"ECTS: {clean_text(course.get('ects'))}\n"
            )
            
            content_info = (
                f"Objectives: {clean_text(course.get('objectives'))}\n"
                f"Description: {clean_text(course.get('description'))}\n"
                f"Prerequisites: {clean_text(course.get('prerequisites'))}\n"
                f"Weekly Topics: {clean_text(course.get('weekly_topics'))}"
            )
            
            full_text = f"{meta_info}\n---\n{content_info}"
            
            rag_doc = {
                "id": course.get('course_code'),
                "text_content": full_text,
                "metadata": {
                    "source": course.get('url'),
                    "department": course.get('department'),
                    "type": course.get('type'),
                    "code": course.get('course_code')
                }
            }
            
            rag_documents.append(rag_doc)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_documents, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully processed {len(rag_documents)} courses.")
        print(f"Saved to: {output_file}")
        
        if len(rag_documents) > 0:
            print("\n--- Example Chunk ---")
            print(rag_documents[0]['text_content'][:500] + "...")

    except Exception as e:
        print(f"Error: {e}")

create_rag_documents('ieu_courses_final.json', 'ieu_rag_ready.json')