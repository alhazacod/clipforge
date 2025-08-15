import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os

def scrape_reddit_post(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title_tag = soup.find("h1", id=lambda x: x and x.startswith("post-title-t3_"))
    title = title_tag.get_text(strip=True) if title_tag else "No title found"

    # Extract post body
    body_div = soup.find("div", class_="text-neutral-content", slot="text-body")
    body_text = body_div.get_text("\n", strip=True) if body_div else "No body found"

    # Save post content to script.txt
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(title + "\n\n")
        f.write(body_text)

    print("Post saved to script.txt")

    # Append to history.csv
    date_str = datetime.now().strftime("%Y-%m-%d")
    csv_exists = os.path.isfile("history.csv")

    with open("history.csv", "a", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not csv_exists:
            writer.writerow(["Date", "Title", "Link"])
        writer.writerow([date_str, title, url])

    print("Entry added to history.csv")


if __name__ == "__main__":
    reddit_url = input("Enter Reddit post URL: ").strip()
    scrape_reddit_post(reddit_url)
