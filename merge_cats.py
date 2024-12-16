import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from main import Base, Restaurant, Category, restaurant_category

# Database setup
DATABASE_URL = "sqlite:///./restaurants.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

# Mapping of categories to their merged group
CATEGORY_MERGE_MAP = {
    "Fast Food": "Comfort Food",
    "Pizza": "Comfort Food",
    "Barbeque": "Comfort Food",
    "Soul Food": "Comfort Food",
    "Soups/Salads/Sandwiches": "Casual Dining",
    "Lunch": "Casual Dining",
    "Buffet/Cafeteria Style": "Casual Dining",
    "Mediterranean/Middle Eastern": "Global Cuisine",
    "Creole/Caribbean/Cuban": "Global Cuisine",
    "Mexican/Latin/Southwest": "Global Cuisine",
    "Asian": "Global Cuisine",
    "Bakery/Ice Cream/Sweets": "Desserts & Sweets",
    "Breakfast and/or Brunch": "Breakfast & Brunch",
    "Restaurant": "Dining Experiences",
    "Fine Dining": "Dining Experiences",
    "Outdoor Dining/With View/Riverfront": "Dining Experiences",
    "Local": "Dining Experiences",
    "Locally Sourced Fare": "Dining Experiences",
    "Bars & Clubs": "Nightlife & Entertainment",
    "Live music": "Nightlife & Entertainment",
    "Wine Bar/Tapas": "Nightlife & Entertainment",
    "Entertainment": "Nightlife & Entertainment",
    "Pub/Bar": "Nightlife & Entertainment",
    "Breweries": "Beverages & Cafes",
    "Brewery/Distillery/Winery": "Beverages & Cafes",
    "Wineries/Distilleries": "Beverages & Cafes",
    "Coffeehouses": "Beverages & Cafes",
    "Tea Rooms": "Beverages & Cafes",
    "Rafting/Canoeing/Kayaking": "Activities & Attractions",
    "Amusement Places": "Activities & Attractions",
    "Clothing": "Shopping",
    "Specialty Shops": "Shopping"
}

def merge_categories():
    with Session(engine) as session:
        # Get all categories
        all_categories = session.query(Category).all()

        # Create or fetch merged categories
        merged_categories = {}
        for original_category in all_categories:
            merged_name = CATEGORY_MERGE_MAP.get(original_category.name, original_category.name)
            if merged_name not in merged_categories:
                # Create the merged category if it doesn't exist
                merged_category = session.query(Category).filter_by(name=merged_name).first()
                if not merged_category:
                    merged_category = Category(name=merged_name)
                    session.add(merged_category)
                    session.flush()  # Save to get the ID
                merged_categories[merged_name] = merged_category
            else:
                merged_category = merged_categories[merged_name]

            # Update restaurants associated with the original category
            for restaurant in original_category.restaurants:
                if merged_category not in restaurant.categories:
                    restaurant.categories.append(merged_category)

            # Remove the original category if it is being merged
            if original_category.name != merged_name:
                session.delete(original_category)

        session.commit()
        print("Categories have been successfully merged and updated.")

if __name__ == "__main__":
    merge_categories()
