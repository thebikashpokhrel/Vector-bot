import requests
from bs4 import BeautifulSoup


def login_and_get_cookie(username: str, password: str) -> str:
    login_url = "http://pulchowk.elibrary.edu.np/Account/Login"
    payload = {"Username": username, "Password": password}

    try:
        # Send POST request to login
        response = requests.post(login_url, data=payload)

        # Check if login was successful
        if response.status_code == 200:
            print("Login successful!")
            # Extract the session cookie
            session_cookie = response.cookies.get("ASP.NET_SessionId")
            return session_cookie
        else:
            print("Failed to login. Status code:", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during login: {e}")
        return None


def get_book_issue_info(session_cookie: str) -> list[dict]:
    book_issue_url = "http://pulchowk.elibrary.edu.np/Book/BookIssue"

    # Set up the cookie jar with the session cookie
    cookies = requests.cookies.RequestsCookieJar()
    cookies.set("ASP.NET_SessionId", session_cookie)

    try:
        # Send GET request to book issue endpoint
        response = requests.get(book_issue_url, cookies=cookies)

        # Check if the request was successful
        if response.status_code == 200:
            print("Book issue info retrieved successfully!")
            # Parse the HTML response using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the table
            table = soup.find("table", {"class": "table table-striped"})
            if not table:
                print("Table not found in the response.")
                return None

            # Extract headers
            headers = [th.text.strip() for th in table.find("thead").find_all("th")]

            # Extract rows
            rows = table.find("tbody").find_all("tr")

            # Convert rows into a list of dictionaries
            data = []
            for row in rows:
                cells = row.find_all("td")
                row_data = {
                    headers[i]: cell.text.strip() for i, cell in enumerate(cells)
                }
                data.append(row_data)

            return data
        else:
            print(
                "Failed to retrieve book issue info. Status code:", response.status_code
            )
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching book issue info: {e}")
        return None


def format_book_issue_data(book_issue_data: list[dict]) -> str:
    if not book_issue_data:
        return "No book issue data available."

    formatted_message = "```Library Book Issue Information:\n\n"
    for book in book_issue_data:
        formatted_message += (
            f"Accession No.: {book['Accession No.']}\n"
            f"Title: {book['Title']}\n"
            f"Issue Date: {book['Issue Date']}\n"
            f"Return Date: {book['Return Date']}\n"
            f"Over Due: {book['Over Due']}\n\n"
        )
    formatted_message += "```"
    return formatted_message
