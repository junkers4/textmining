#Usage working on local IDE not on online env like github 
# coded for persons not organizations(but working for both just change att in csv)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import sys
import os
from datetime import datetime, timedelta

# Funkce pro převod relativního času na datum
def parse_relative_time(relative_time, current_date=None):
    if not current_date:
        current_date = datetime.now()
    
    relative_time = relative_time.lower().strip()
    try:
        if "před" in relative_time:
            relative_time = relative_time.replace("před ", "")
            if "hodin" in relative_time:
                hours = int(relative_time.split()[0])
                return current_date - timedelta(hours=hours)
            elif "dny" in relative_time or "dnem" in relative_time:
                days = int(relative_time.split()[0])
                return current_date - timedelta(days=days)
            elif "týdn" in relative_time:
                weeks = int(relative_time.split()[0])
                return current_date - timedelta(weeks=weeks)
            elif "měsíc" in relative_time:
                months = int(relative_time.split()[0])
                return current_date - timedelta(days=months * 30)  # Přibližně
            elif "rok" in relative_time or "lety" in relative_time:
                years = int(relative_time.split()[0])
                return current_date - timedelta(days=years * 365)  # Přibližně
            else:
                return current_date  # Pokud formát nerozpoznáme
        return current_date
    except:
        return current_date  # Vracíme aktuální datum jako fallback

# Funkce na uložení recenzí do CSV
def save_to_csv(reviews_data, filename='recenzie.csv'):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Hviezdičky", "Miesto", "Adresa", "Text", "Datum"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(reviews_data)
    print(f"Recenzie boli uložené do súboru '{filename}'.")

# Nastavení Chrome options
options = Options()
# options.add_argument('--headless')  # Zakomentované, aby si videl prehliadač
options.add_argument('--disable-dev-shm-usage')

# Inicializace drivera
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL stránky s recenziami
url = "https://www.google.com/maps/contrib/110841734452676392342/reviews/@50.613718,15.7289722,9z/data=!4m3!8m2!3m1!1e1?hl=cs&entry=ttu&g_ep=EgoyMDI1MDUxMi4wIKXMDSoASAFQAw%3D%3D"
driver.get(url)

# Handle the consent popup by clicking "Odmítnout vše"
try:
    reject_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Odmítnout vše']]"))
    )
    reject_button.click()
    print("Consent popup rejected by clicking 'Odmítnout vše'.")
except Exception as e:
    print("Consent popup not found or already handled:", e)

# Čekání na načítání stránky
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "fontBodyMedium"))
    )
    print("Stránka načítaná. Můžeš skrolovat. Pro ukončení napiš 'koniec' nebo stiskni Ctrl+C.")
except Exception as e:
    print("Chyba při čekání na stránku:", e)
    driver.quit()
    sys.exit(1)

# Seznam už nalezených recenzí
seen_reviews = set()
reviews_data = []  # Seznam pro ukládání recenzí jako slovníky

try:
    while True:
        # Nalezení všech viditelných recenzí (kontajner recenzie)
        review_containers = driver.find_elements(By.CLASS_NAME, "jftiEf")  # Kontajner pro celou recenzi

        new_reviews = []  # Dočasný seznam pro nové recenze v této iteraci
        for container in review_containers:
            # Kliknutí na tlačítko "Víc", pokud existuje
            try:
                more_button = container.find_element(By.CLASS_NAME, "w8nwRe")
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(0.5)  # Krátké čekání na rozbalení textu
            except:
                pass  # Pokud tlačítko "Víc" neexistuje, pokračujeme

            # Text recenze
            review_text_element = container.find_elements(By.CLASS_NAME, "wiI7pd")
            review_text = review_text_element[0].text.strip() if review_text_element else "(žádný text)"

            # Počet hvězdiček
            try:
                stars_element = container.find_element(By.CLASS_NAME, "kvMYJc")
                stars = stars_element.get_attribute("aria-label").strip()
                stars = stars.split()[0]  # Např. "5 hvězdiček" -> "5"
            except:
                stars = "Nenalezeno"

            # Název místa
            try:
                place_element = container.find_element(By.CLASS_NAME, "d4r55")
                place = place_element.text.strip()
            except:
                place = "Nenalezeno"

            # Adresa
            address = "Nenalezeno"
            try:
                address_element = container.find_element(By.CLASS_NAME, "RfnDt")
                address = address_element.text.strip()
            except:
                try:
                    address_element = container.find_element(By.CLASS_NAME, "I06YTe")
                    address = address_element.text.strip()
                except:
                    pass

            # Čas recenze
            try:
                time_element = container.find_element(By.CLASS_NAME, "rsqaWe")
                relative_time = time_element.text.strip()
                review_date = parse_relative_time(relative_time).strftime('%Y-%m-%d')
            except:
                relative_time = "Nenalezeno"
                review_date = datetime.now().strftime('%Y-%m-%d')  # Fallback na aktuální datum

            # Unikátní identifikátor recenze
            review_id = (place, stars, review_text, relative_time)

            # Kontrola, zda je recenze nová
            if review_id not in seen_reviews:
                print(f"Recenze {len(seen_reviews) + 1}:")
                print(f"  Hvězdičky: {stars}")
                print(f"  Místo: {place}")
                print(f"  Adresa: {address}")
                print(f"  Datum: {review_date} ({relative_time})")
                print(f"  Text: {review_text}")
                print("-" * 50)
                
                seen_reviews.add(review_id)
                new_reviews.append({
                    "Hviezdičky": stars,
                    "Miesto": place,
                    "Adresa": address,
                    "Text": review_text,
                    "Datum": review_date
                })

        # Uložení nových recenzí do CSV
        if new_reviews:
            reviews_data.extend(new_reviews)
            save_to_csv(new_reviews)

        # Krátká pauza na manuální skrolování
        time.sleep(2)

        # Kontrola, zda chceš skončit
        try:
            user_input = input("Pokračovat? (napiš 'koniec' pro ukončení): ").strip().lower()
            if user_input == "koniec":
                print(f"Celkový počet nalezených recenzí: {len(seen_reviews)}")
                break
        except KeyboardInterrupt:
            print("\nManuálně přerušeno (Ctrl+C).")
            print(f"Celkový počet nalezených recenzí: {len(seen_reviews)}")
            break

except Exception as e:
    print("Chyba při získávání recenzí:", e)

finally:
    # Zavření prohlížeče
    driver.quit()
    if reviews_data:
        print(f"Celkový počet uložených recenzí: {len(reviews_data)}")
    else:
        print("Žádné recenze nebyly uloženy.")