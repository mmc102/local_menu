from fastapi import FastAPI, Depends, HTTPException, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from sqladmin import Admin, ModelView
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Initialize FastAPI app
app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="your_secret_key_here")

# Database setup
DATABASE_URL = "sqlite:///./restaurants.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for many-to-many relationship between restaurants and categories
restaurant_category = Table(
    "restaurant_category",
    Base.metadata,
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)

# SQLAlchemy model for restaurants
class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String, index=True)
    website = Column(String)
    clicks = relationship("Click", back_populates="restaurant")
    categories = relationship("Category", secondary=restaurant_category, back_populates="restaurants")

# SQLAlchemy model for categories
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    restaurants = relationship("Restaurant", secondary=restaurant_category, back_populates="categories")

# SQLAlchemy model for clicks
class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    restaurant = relationship("Restaurant", back_populates="clicks")


class SuggestedChanges(Base):
    __tablename__ = "suggested_changes"
    id = Column(Integer, primary_key=True, index=True)
    suggestion = Column(String, nullable=False)
    handled = Column(Boolean, nullable=False, default=False)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RestaurantAdmin(ModelView, model=Restaurant):
    column_list = [Restaurant.id, Restaurant.name, Restaurant.location, Restaurant.categories, Restaurant.website]

class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.restaurants]

class ClickAdmin(ModelView, model=Click):
    column_list = [Click.id, Click.restaurant]

class SuggestionAdmin(ModelView, model=SuggestedChanges):
    column_list = [SuggestedChanges.id, SuggestedChanges.handled, SuggestedChanges.suggestion]







admin = Admin(app, engine)
admin.add_view(RestaurantAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ClickAdmin)
admin.add_view(SuggestionAdmin)



# Routes
@app.get("/", response_class=HTMLResponse, methods=["GET", "HEAD"])
async def list_restaurants(request: Request, db: Session = Depends(get_db), categories: list[str] = Query(default=None), message: str = Query(default=None)):
    """
    Render the list of restaurants as an HTML page, optionally filtered by categories.
    """
    query = db.query(Restaurant)
    if categories:
        query = query.join(Restaurant.categories).filter(Category.name.in_(categories))
    restaurants = query.all()
    all_categories = db.query(Category).order_by(Category.name).all()
    print(categories)
    recently_viewed_ids = request.session.get("recently_viewed", [])
    recently_viewed_restaurants = (
       db.query(Restaurant).filter(Restaurant.id.in_(recently_viewed_ids)).all()
    )


    return templates.TemplateResponse(
        "restaurants.html",
        {
            "request": request,
            "message": message,
            "restaurants": restaurants,
            "categories": all_categories,
            "selected_categories": categories or [],
            "recently_viewed": recently_viewed_restaurants
        }
    )




@app.post("/suggestion")
async def submit_suggestion(suggestion: str = Form(...),db: Session = Depends(get_db)):
    """
    Submit a suggestion form
    """
    suggestion = SuggestedChanges(suggestion=suggestion)
    db.add(suggestion)
    db.commit()
    return RedirectResponse(url="/?message=Thanks+for+the+suggestion!", status_code=303)




@app.get("/restaurants/{restaurant_id}/menu")
async def redirect_to_menu(request: Request, restaurant_id: int, db: Session = Depends(get_db)):
    """
    Redirect to the menu link while incrementing the menu click count.
    """
    try:
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
        click = Click(restaurant_id=restaurant.id)
        db.add(click)
        db.commit()

        recently_viewed = request.session.get("recently_viewed", [])
        if restaurant_id not in recently_viewed:
            recently_viewed.append(restaurant_id)
            request.session["recently_viewed"] = recently_viewed[-10:]



        return RedirectResponse(url=restaurant.website)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Restaurant not found")
