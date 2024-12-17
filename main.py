from fastapi import FastAPI, Depends, HTTPException, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from passlib.context import CryptContext



load_dotenv()

app = FastAPI()



SECRET_KEY = os.environ["SECRET_KEY"]
assert SECRET_KEY, "need to have a secret key env var set"

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

DATABASE_URL = "sqlite:///./restaurants.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

restaurant_category = Table(
    "restaurant_category",
    Base.metadata,
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False) 

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String, index=True)
    website = Column(String)
    clicks = relationship("Click", back_populates="restaurant")
    categories = relationship("Category", secondary=restaurant_category, back_populates="restaurants")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Restaurant(name={self.name})>"

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    restaurants = relationship("Restaurant", secondary=restaurant_category, back_populates="categories")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Category(name={self.name})>"

class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    restaurant = relationship("Restaurant", back_populates="clicks")

    def __str__(self):
        return self.restaurant.name

    def __repr__(self):
        return f"<Click on link for(name={self.restaurant.name})>"




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
    form_include_relationships = True



class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.restaurants]

class ClickAdmin(ModelView, model=Click):
    column_list = [Click.id, Click.restaurant]

class SuggestionAdmin(ModelView, model=SuggestedChanges):
    column_list = [SuggestedChanges.id, SuggestedChanges.handled, SuggestedChanges.suggestion]


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.verify_password(password):
            print("login failed")
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid username or password"},
                status_code=401
            )

        request.session["user_id"] = user.id
        request.session["is_admin"] = user.is_admin
        print(user.is_admin)
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        print(request.session)
        return request.session.get("is_admin") == True



admin_auth = AdminAuth(secret_key=SECRET_KEY) 
admin = Admin(app, engine, authentication_backend=admin_auth)


admin.add_view(RestaurantAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ClickAdmin)
admin.add_view(SuggestionAdmin)



# Routes
@app.head("/")
@app.get("/", response_class=HTMLResponse)
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

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=401
        )

    request.session["user_id"] = user.id
    request.session["is_admin"] = user.is_admin
    return RedirectResponse(url="/admin" if user.is_admin else "/", status_code=303)



@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.post("/suggestion")
async def submit_suggestion(suggestion: str = Form(...),db: Session = Depends(get_db)):
    """
    Submit a suggestion form
    """
    suggestion = SuggestedChanges(suggestion=suggestion)
    db.add(suggestion)
    db.commit()
    return RedirectResponse(url="/?message=Thanks+for+the+suggestion!", status_code=303)


@app.get("/suggestion")
async def get_suggestion_form(request: Request):

    """
    Gets the suggestion form
    """
    return templates.TemplateResponse("suggestions.html", {"request": request})


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
