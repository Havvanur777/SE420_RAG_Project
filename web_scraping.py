import requests
from bs4 import BeautifulSoup
import json
import time

departments = [
    {
        "name": "Software Engineering",
        "code": "SE",
        "url": "https://ects.ieu.edu.tr/new/akademik.php?section=se.cs.ieu.edu.tr&sid=curr_before_2025&lang=en"
    },
    {
        "name": "Computer Engineering",
        "code": "CE",
        "url": "https://ects.ieu.edu.tr/new/akademik.php?section=ce.cs.ieu.edu.tr&sid=curr_before_2025&lang=en"
    },
    {
        "name": "Electrical and Electronics Engineering",
        "code": "EEE",
        "url": "https://ects.ieu.edu.tr/new/akademik.php?section=ete.cs.ieu.edu.tr&sid=curr_before_2025&lang=en"
    },
    {
        "name": "Industrial Engineering",
        "code": "IE",
        "url": "https://ects.ieu.edu.tr/new/akademik.php?section=is.cs.ieu.edu.tr&sid=curr_before_2025&lang=en"
    }
]

all_courses_data = []

def get_course_details(course_url):

    course_info = {
        "objectives": "Not specified",
        "description": "Not specified",
        "prerequisites": "None",
        "weekly_topics": []
    }
    
    try:

        if not course_url.startswith("http"):
            course_url = "https://ects.ieu.edu.tr/new/" + course_url

        response = requests.get(course_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        all_rows = soup.find_all('tr')
        for row in all_rows:
            cells = row.find_all('td')
            if len(cells) < 2: continue 
            
            header_text = cells[0].get_text(strip=True).lower()
            content_text = cells[1].get_text(strip=True)

            if "course objective" in header_text or "dersin amacı" in header_text:
                course_info["objectives"] = content_text
            elif "course description" in header_text or "ders tanımı" in header_text:
                course_info["description"] = content_text
            elif "prerequisite" in header_text or "ön koşul" in header_text or "ön-koşul" in header_text:
                course_info["prerequisites"] = content_text

        weeks_table = soup.find('table', id='weeks')
        
        if weeks_table:
            rows = weeks_table.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) >= 2:
                    week_num = cols[0].get_text(strip=True)
                    topics = cols[1].get_text(strip=True)
                    
                    if week_num.isdigit():
                        course_info["weekly_topics"].append(f"Week {week_num}: {topics}")

        return course_info

    except Exception as e:
        print(f"    ! Details could not be captured ({course_url}): {e}")
        return course_info 

def scrape_department(dept):
    print(f"--- {dept['name']} searching ---")
    
    try:
        response = requests.get(dept['url'])
        soup = BeautifulSoup(response.content, 'html.parser')

        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            if not rows: continue
            
            semester_val = "Unknown"
            type_val = "Elective" 

            first_row_text = rows[0].get_text(strip=True)
            
            if "Semester" in first_row_text or "Dönem" in first_row_text:
                semester_val = first_row_text 
                type_val = "Mandatory"
            elif "Elective" in first_row_text or "Seçmeli" in first_row_text:
                semester_val = "Elective Pool"
                type_val = "Elective"

            for row in rows:
                cols = row.find_all('td')

                if len(cols) >= 7: 
                    try:
                        course_code = cols[0].text.strip()
                        
                        if "Code" in course_code or "Kod" in course_code:
                            continue

                        if len(course_code) < 3: continue

                        course_name = cols[2].text.strip()    
                        local_credit = cols[5].text.strip()  
                        ects = cols[6].text.strip()      

                        link_tag = cols[0].find('a')
                        if link_tag:
                            detail_url = link_tag['href']
                            details_data = get_course_details(detail_url)
                        else:
                            details_data = {
                                "objectives": "", "description": "", 
                                "prerequisites": "", "weekly_topics": []
                            }
                            detail_url = ""

                        course_obj = {
                            "department": dept['name'],
                            "course_code": course_code,
                            "course_name": course_name,
                            "semester": semester_val,
                            "type": type_val,  
                            "ects": ects,
                            "local_credit": local_credit,
                            "objectives": details_data["objectives"],
                            "description": details_data["description"],
                            "prerequisites": details_data["prerequisites"],
                            "weekly_topics": details_data["weekly_topics"],
                            "url": detail_url
                        }
                        
                        all_courses_data.append(course_obj)
                        print(f"Added: {course_code} | {type_val} | {semester_val}")
                        
                    except Exception as e:
                        continue 

    except Exception as e:
        print(f"Error: {e}")

for dept in departments:
    scrape_department(dept)
    time.sleep(1) 
    
filename = 'ieu_courses_final.json'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(all_courses_data, f, ensure_ascii=False, indent=4)

print(f"\nProcess Completed! A total of {len(all_courses_data)} courses have been saved to '{filename}'.")