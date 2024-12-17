import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from main import Base, Restaurant, Category
import os

# Database setup
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

def seed_database(json_file_path):
    with open(json_file_path, "r") as file:
        data = json.load(file)

    restaurants_data = data.get("docs", []).get("docs")
    with Session(engine) as session:
        for restaurant in restaurants_data:
            # Handle categories
            category_name = restaurant.get("primary_category", {}).get("subcatname", "Unknown")
            category = session.query(Category).filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                session.add(category)
                session.flush()  # Flush to get the category ID

            # Handle restaurant
            new_restaurant = Restaurant(
                name=restaurant.get("title"),
                city="Chattanooga"
                location=restaurant.get("address1", "Unknown"),
                website=restaurant.get("weburl", ""),
            )
            new_restaurant.categories.append(category)
            session.add(new_restaurant)

        session.commit()
        print(f"Seeded {len(restaurants_data)} restaurants into the database.")

if __name__ == "__main__":
    # Replace with your JSON file path
    json_file_path = "restaurants.json"
    seed_database(json_file_path)
