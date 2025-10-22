from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os
import re
import time

# === CONFIG ===
output_file = "questions.txt"
quiz_url = "https://www.erpprep.com/user/244745/myresults"  # <-- Replace with your quiz URL

# === SETUP SELENIUM ===
chrome_options = Options()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Open browser
driver.get(quiz_url)
print(f"🌐 Chrome opened and navigated to: {quiz_url}")
print("Log in manually if needed.")
print("When ready, type 'run' and press Enter to scrape the page.")
print("Type 'exit' to quit at any time.\n")

# === MAIN LOOP ===
while True:
    cmd = input("👉 Type 'run' to scrape (or 'exit' to quit): ").strip().lower()
    if cmd == "exit":
        print("👋 Exiting and closing browser...")
        driver.quit()
        break
    elif cmd != "run":
        continue

    # === LOAD EXISTING QUESTIONS ===
    existing_questions = set()
    existing_data = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = f.readlines()

    for line in existing_data:
        line = line.strip()
        if line.startswith("Question "):
            parts = line.split(":", 1)
            if len(parts) > 1:
                question_text = parts[1].strip()
                existing_questions.add(question_text)


    # === SCRAPE CURRENT PAGE ===
    soup = BeautifulSoup(driver.page_source, "html.parser")

    dl = soup.find("dl", class_="quiz-report")
    new_questions = []
    if dl:
        for dt in dl.find_all("dt"):
            next_dd = dt.find_next_sibling("dd")
            if not next_dd or not next_dd.find("table"):
                continue

            # Extract question text
            p_tags = dt.find_all("p")
            if not p_tags:
                continue

            question_text = " ".join([p.get_text(" ", strip=True) for p in p_tags])
            question_text = " ".join(question_text.split())

            # Skip duplicates
            if question_text in existing_questions:
                continue
            existing_questions.add(question_text)

            # Extract options and correct answers
            options = []
            correct_answers = []
            rows = next_dd.find_all("tr")
            for idx, row in enumerate(rows, start=1):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                text = cells[1].get_text(strip=True)
                options.append(text)

                img = cells[0].find("img")
                if img and any(x in img["src"] for x in ["correct.png", "should.png"]):
                    correct_answers.append(f"Option {idx}")

            new_questions.append({
                "question": question_text,
                "options": options,
                "correct": correct_answers
            })

    # === COMBINE OLD + NEW QUESTIONS ===
    total_existing = len(re.findall(r"^Question ", "".join(existing_data), re.M))
    total_questions = total_existing + len(new_questions)

    # === REWRITE FILE ===
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Total Questions: {total_questions}\n\n")

        # Write old questions
        question_counter = 1
        for line in existing_data:
            if line.startswith("Total Questions:"):
                continue
            if line.startswith("Question "):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    # Properly formatted Question line
                    f.write(f"Question {question_counter}: {parts[1].strip()}\n")
                    question_counter += 1
                else:
                    # Malformed line, skip or log it
                    print(f"⚠️ Skipping malformed question line: {line.strip()}")
            else:
                f.write(line)


        # Append new questions
        for q in new_questions:
            f.write(f"Question {question_counter}: {q['question']}\n")
            for idx, opt in enumerate(q['options'], start=1):
                f.write(f"Option {idx}: {opt}\n")
            f.write(f"Correct Answers: {', '.join(q['correct']) if q['correct'] else 'None'}\n\n")
            question_counter += 1

    print(f"✅ Added {len(new_questions)} new questions (total now {total_questions}) to {output_file}\n")