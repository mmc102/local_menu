import os
import datetime
import requests
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from main import Base, Restaurant 

# Database setup
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)


def check_url(url: str) -> bool:
    """
    Checks if a URL is reachable by attempting both http and https versions.
    Follows redirects and returns True if status code is 200.
    """
    try:
        # First try the given URL
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return True
        print(f"Status {response.status_code} for {url}")
    except Exception as e:
        print(f"Error with {url}: {e}")

    # If the URL doesn't include a scheme, try both http and https
    if not url.startswith("http://") and not url.startswith("https://"):
        try:
            # Try https version first
            response = requests.get(f"https://{url}", timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return True
            # Fallback to http
            response = requests.get(f"http://{url}", timeout=10, allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            print(f"Both http and https failed for {url}: {e}")

    return False


def verify_restaurant_websites():
    total_urls = 0
    unsuccessful_urls = 0

    with Session(engine) as session:
        # Query all restaurants with a website
        restaurants = session.query(Restaurant).filter(Restaurant.website.isnot(None)).all()

        for restaurant in restaurants:
            total_urls += 1
            url = restaurant.website.strip()
            print(f"Checking URL: {url}")

            # Check the URL
            if not check_url(url):
                unsuccessful_urls += 1
                print(f"Restaurant '{restaurant.name}' has an invalid or unreachable URL: {url}")
                # Update url_verified_at to now
                restaurant.url_verified_at = datetime.datetime.utcnow()
                session.add(restaurant)  # Mark for update

        # Commit updates
        session.commit()
        print("URL verification completed and updates applied.")

    # Print stats
    print("\n--- URL Verification Stats ---")
    print(f"Total URLs checked: {total_urls}")
    print(f"Unsuccessful URLs: {unsuccessful_urls}")
    print(f"Successful URLs: {total_urls - unsuccessful_urls}")


if __name__ == "__main__":
    verify_restaurant_websites()
