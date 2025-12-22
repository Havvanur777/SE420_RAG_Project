import requests
from bs4 import BeautifulSoup
import json
import time
import re

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

            if "objective" in header_text or "dersin amacı" in header_text:
                course_info["objectives"] = content_text
            elif "description" in header_text or "tanımı" in header_text:
                course_info["description"] = content_text
            elif "prerequisite" in header_text or "ön-koşul" in header_text or "ön koşul" in header_text:
                course_info["prerequisites"] = content_text

        target_table = soup.find('table', id='weeks')
        if not target_table:
            all_tables = soup.find_all('table')
            for table in all_tables:
                headers = table.find_all(['th', 'td'])
                header_texts = [h.get_text(strip=True).lower() for h in headers[:10]]
                if (any("week" in h for h in header_texts) or any("hafta" in h for h in header_texts)) and \
                   (any("topics" in h for h in header_texts) or any("subjects" in h for h in header_texts) or any("konular" in h for h in header_texts)):
                        target_table = table
                        break
        
        if target_table:
            rows = target_table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    week_raw = cols[0].get_text(strip=True).replace('.', '').replace('\xa0', '')
                    topics = cols[1].get_text(strip=True)
                    if week_raw.isdigit():
                         course_info["weekly_topics"].append(f"Week {week_raw}: {topics}")
                    elif ("review" in week_raw.lower() or "final" in week_raw.lower()) and len(topics) > 2:
                         course_info["weekly_topics"].append(f"Note: {topics}")

        return course_info

    except Exception as e:
        return course_info 

def scrape_pool_page(pool_url, target_id_str, dept_name, source_code, label_type):
    print(f"  -> Entering Pool Page... Filtering ONLY for Section ID: {target_id_str}")
    
    try:
        if not pool_url.startswith("http"):
            pool_url = "https://ects.ieu.edu.tr/new/" + pool_url
            
        response = requests.get(pool_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')

        collecting = False
        target_normalized = str(int(target_id_str)) if target_id_str.isdigit() else target_id_str

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                row_text_raw = row.get_text(strip=True).upper()
                
                if "POOL" in row_text_raw and re.search(r'\d', row_text_raw):
                    if (target_id_str in row_text_raw) or (f"POOL {target_normalized}" in row_text_raw):
                        collecting = True
                    else:
                        collecting = False
                    continue 

                if collecting:
                    cols = row.find_all('td')
                    if len(cols) >= 6: 
                        try:
                            p_code = cols[0].text.strip()
                            if "Code" in p_code or len(p_code) < 2: continue
                            
                            p_name = cols[1].text.strip() 
                            if len(p_name) < 3: p_name = cols[2].text.strip()

                            p_ects = cols[-1].text.strip()
                            
                            p_link = cols[0].find('a')
                            p_details = {"objectives": "", "description": f"{label_type} Course", "prerequisites": "", "weekly_topics": []}
                            p_url = ""
                            
                            if p_link:
                                p_url = p_link['href']
                                p_details = get_course_details(p_url)

                            pool_obj = {
                                "department": dept_name,
                                "course_code": p_code,
                                "course_name": p_name,
                                "semester": f"From Pool {target_id_str}", 
                                "type": label_type,           
                                "ects": p_ects,
                                "local_credit": "-", 
                                "objectives": p_details["objectives"],
                                "description": p_details["description"],
                                "prerequisites": p_details["prerequisites"],
                                "weekly_topics": p_details["weekly_topics"],
                                "url": p_url
                            }
                            all_courses_data.append(pool_obj)
                            print(f"    -> Added: {p_code} | {label_type}")

                        except: continue
    except Exception as e:
        print(f"  ! Pool Error: {e}")

def scrape_department(dept):
    print(f"--- Scanning {dept['name']} ---")
    
    processed_pools = set()

    try:
        response = requests.get(dept['url'])
        soup = BeautifulSoup(response.content, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        lang_pattern = re.compile(r'course_code=(FR|GER|ITL|SPN|RUS|CHN|JPN|GR)\s?(\d+)', re.IGNORECASE)
        
        for link in all_links:
            href = link['href']
            
            match = lang_pattern.search(href)
            if match:
                lang_code = f"{match.group(1).upper()} {match.group(2)}"
                unique_key = f"{dept['name']}_{lang_code}"
                
                lang_url = href
                if not lang_url.startswith("http"):
                    lang_url = "https://ects.ieu.edu.tr/new/" + lang_url
                
                details = get_course_details(lang_url)
                
                lang_obj = {
                    "department": dept['name'],
                    "course_code": lang_code,
                    "course_name": f"{lang_code} Language Course", 
                    "semester": "Language Selection",
                    "type": "Mandatory",
                    "ects": "2", 
                    "local_credit": "2",
                    "objectives": details["objectives"],
                    "description": details["description"],
                    "prerequisites": details["prerequisites"],
                    "weekly_topics": details["weekly_topics"],
                    "url": lang_url
                }
                
                exists = False
                for item in all_courses_data:
                    if item["course_code"] == lang_code and item["department"] == dept['name']:
                        exists = True
                        break
                
                if not exists:
                    all_courses_data.append(lang_obj)
                    print(f"    -> Scraped Language: {lang_code}")

        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            
            first_row_text = ""
            if rows:
                first_row_text = rows[0].get_text(strip=True)
                if len(first_row_text) < 3:
                    prev = table.find_previous(['h3', 'h4', 'div', 'strong'])
                    if prev: first_row_text = prev.get_text(strip=True)
            
            semester_val = "Unknown"
            table_category = "Unknown"

            if "Semester" in first_row_text or "Yarıyıl" in first_row_text:
                semester_val = first_row_text
                table_category = "Curriculum"
            elif "Pool" in first_row_text or "Havuz" in first_row_text or "Elective" in first_row_text:
                semester_val = "Elective Table"
                table_category = "ElectiveList"
            else:
                continue 

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7: 
                    try:
                        course_code = cols[0].text.strip()
                        if "Code" in course_code or len(course_code) < 2: continue
                        course_name = cols[2].text.strip()
                        local_credit = cols[5].text.strip()  
                        ects = cols[6].text.strip()      
                        
                        link_tag = cols[0].find('a')
                        detail_url = ""
                        if link_tag: detail_url = link_tag['href']

                        hover_text = ""
                        if link_tag and link_tag.get('data-content'): 
                            hover_text = link_tag.get('data-content')
                        elif link_tag and link_tag.get('data-original-title'): 
                            hover_text = link_tag.get('data-original-title')
                        elif link_tag and link_tag.get('title'): 
                            hover_text = link_tag.get('title')
                        elif cols[0].get('data-content'): 
                            hover_text = cols[0].get('data-content')
                        
                        if hover_text: hover_text = BeautifulSoup(hover_text, "html.parser").get_text(separator=", ")

                        final_type = "Unknown"
                        
                        if table_category == "Curriculum":
                            if "ELEC" in course_code or "XX" in course_code:
                                final_type = "Elective - Placeholder"
                            elif "SFL" in course_code:
                                final_type = "Mandatory" 
                            elif "POOL" in course_code and link_tag:
                                id_match = re.search(r'(\d+)', course_code)
                                if id_match:
                                    target_id = id_match.group(1)
                                    if target_id not in processed_pools:
                                        scrape_pool_page(detail_url, target_id, dept['name'], course_code, "Mandatory - Pool Selection")
                                        processed_pools.add(target_id)
                                    else:
                                        print(f"    -> Skipping Duplicate Pool: {target_id}")
                                continue 
                            else:
                                final_type = "Mandatory"
                        
                        elif table_category == "ElectiveList":
                            if "POOL" in course_code and link_tag:
                                id_match = re.search(r'(\d+)', course_code)
                                if id_match:
                                    target_id = id_match.group(1)
                                    if target_id not in processed_pools:
                                        scrape_pool_page(detail_url, target_id, dept['name'], course_code, "Mandatory - Pool Selection")
                                        processed_pools.add(target_id)
                                    else:
                                        print(f"    -> Skipping Duplicate Pool: {target_id}")
                                continue 
                            else:
                                final_type = "Elective"

                        details_data = {"objectives": "", "description": "", "prerequisites": "", "weekly_topics": []}
                        
                        if final_type == "Mandatory":
                             if link_tag: details_data = get_course_details(detail_url)
                             if hover_text: details_data["description"] += f" [Note: {hover_text}]"

                        elif final_type == "Elective - Placeholder":
                             details_data["description"] = "Check the Elective Tables below for options."
                             if hover_text: details_data["description"] += f" Options: {hover_text}"
                             details_data["objectives"] = "Elective Slot"
                             
                        elif final_type == "Elective":
                             if link_tag: details_data = get_course_details(detail_url)

                        course_obj = {
                            "department": dept['name'],
                            "course_code": course_code,
                            "course_name": course_name,
                            "semester": semester_val,
                            "type": final_type, 
                            "ects": ects,
                            "local_credit": local_credit,
                            "objectives": details_data["objectives"],
                            "description": details_data["description"],
                            "prerequisites": details_data["prerequisites"],
                            "weekly_topics": details_data["weekly_topics"],
                            "url": detail_url
                        }
                        
                        all_courses_data.append(course_obj)
                        print(f"Added: {course_code} | {final_type}")

                    except Exception as e:
                        continue 

    except Exception as e:
        print(f"Department Error: {e}")

for dept in departments:
    scrape_department(dept)
    time.sleep(1) 
    
filename = 'ieu_courses_final.json'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(all_courses_data, f, ensure_ascii=False, indent=4)

print(f"\nProcess Completed! A total of {len(all_courses_data)} courses have been saved to '{filename}'.")