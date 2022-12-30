"""
    @package: smartcook
    @author: Noel Nagy
    @website: https://github.com/nagynooel
    ©2022 Noel Nagy - All rights reserved.
"""
# --- Helper file containing functions and flask decorators that are made for use mainly in app.py

from flask import render_template, redirect, flash, session

from flask_session import Session
from functools import wraps

from re import match, sub
from werkzeug.security import generate_password_hash, check_password_hash

from os import environ, path
from email.message import EmailMessage
import smtplib, ssl

from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from json import loads
from unicodedata import normalize


# -- Global variables
encryption_method = "pbkdf2:sha256:120000"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "avif", "gif"}


# -- Error handling
# Render error to user
def error(message, code=400):
    return render_template("error.html", e_code = code, message = message), code


# -- Decorators
# Decorator to only let logged in people access page
def logged_in_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("uid") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Decorator to only let people who are not logged in access the page
def signed_out_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("uid") is not None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


# -- Filters
# Remove leading 0s from string and return 0 if string is only 0
def remove_leading_zeros(value):
    value = value.lstrip("0")
    return "0" if value == "" else value


# -- Functions
# - Global
# Redirect user with an alert
def redirect_alert(redirect_to: str, alert_msg:str, alert_type="danger"):
    flash(alert_msg, "alert-" + alert_type)
    return redirect(redirect_to)

# Get the extension from the file name and check if it is allowed (for images)
def allowed_extension(filename, allowed=ALLOWED_IMAGE_EXTENSIONS):
    exstension = path.splitext(filename)[1][1:]
    return exstension in allowed

# Get the extension from the filename (includes the '.' character)
def get_file_extension(filename):
    return path.splitext(filename)[1]

# Create email message object
def create_msg(receiver: str, subject: str, plain: str, html: str):
    msg = EmailMessage()
    
    # Generic email headers
    msg["From"] = f'SmartCook <{environ.get("SMTP_EMAIL")}>'
    msg["To"] = receiver
    msg["Subject"] = subject
    
    # Set the plain text body
    msg.set_content(plain)
    
    # Set an alternative HTML body
    msg.add_alternative(html, subtype='html')
    
    return msg

# Send SSL email using credentials and SMTP host set in environ variables
def send_email(msg: EmailMessage):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(environ.get("SMTP_SERVER"), environ.get("SMTP_PORT"), context=context) as server:
        server.login(environ.get("SMTP_EMAIL"), environ.get("SMTP_PASSWORD"))
        server.sendmail(
            environ.get("SMTP_EMAIL"), msg["To"], msg.as_string()
        )


# - Recipes
# Import a recipe from the given url
# Returns False if unable to locate recipe
def import_from_url(url):
    # Send GET request to url and get all script tags with type ld+json
    html_doc = requests.get(url).content
    soup = BeautifulSoup(html_doc, 'html.parser')
    content = soup.find_all("script", type="application/ld+json")
    
    # Search for the recipe style tag
    for c in content:
        c = c.string
        if any(typ in c for typ in ['"@type":"Recipe"', '"@type": "Recipe"', '"@type":"recipe"', '"@type": "recipe"']):
            content = c
            break
    
    # Validate: Script tag exists
    if not content:
        return False
    
    # Get all information needed from the script tag
    content = content.string
    
    soup = BeautifulSoup(content, 'html.parser')
    content_inner = soup.find("script", type="application/ld+json")
    
    json = loads(content)
    
    recipe = {}
    
    # Append recipe dictionary if tag is defined
    needed_tags = {"name":"title", "description":"description", "prepTime":"preptime", "cookTime":"cooktime", "recipeYield":"servings", "recipeIngredient":"ingredients", "recipeInstructions":"instructions"}
    
    for key in needed_tags:
        if key in json:
            recipe[needed_tags[key]] = json[key]
    
    # Validate: output dictionary is not empty
    if not recipe:
        return False
    
    # Change & symbol to %26 to work with GET arguments
    if "title" in recipe and recipe["title"] != None:
        recipe["title"] = recipe["title"].replace('&', '%26')
    
    if "description" in recipe and recipe["description"] != None:
        recipe["description"] = recipe["description"].replace('&', '%26')
    
    # If prep and cook times are available change them to the applications format (hhmm)
    def format_time(key):
        if key in recipe:
            current_format = recipe[key].replace("PT", "")
            
            time = ""
            x = ""
            for c in current_format:
                if c == 'H':
                    time = x.zfill(2)
                    x = ""
                elif c == 'M':
                    if time == "":
                        time = f"00{x.zfill(2)}"
                    else:
                        time += x
                        x = ""
                else:
                    x += c
            
            recipe[key] = time
    
    format_time("preptime")
    format_time("cooktime")
    
    return recipe

# Import recipe from xml
def import_xml(file_object):
    # Read the XML file and extract all necessary data
    # Uses templates/recipes/recipe.xml as template
    soup = BeautifulSoup(file_object.read(), "xml")
    recipe = {}
    
    # Get general values
    tags = ["title", "description"]
    
    for tag in tags:
        element = soup.find(tag)
        
        if element != None:
            recipe[tag] = sub("\n +", "\n", sub(" +", " ", element.text.strip()))
    
    tags = ["prepTime", "cookTime", "servings"]
    
    for tag in tags:
        element = soup.find(tag)
        
        if element != None:
            recipe[tag.lower()] = sub(" +", " ", element.get("quantity").strip())
    
    # Get ingredients
    ingredients = soup.find_all("ingredient")
    
    if ingredients != None:
        recipe["ingredients"] = []
        for ingredient in ingredients:
            recipe["ingredients"].append({"quantity":ingredient.get("quantity"), "unit":ingredient.get("unit"), "name":ingredient.get("name")})
    
    # Get instructions
    instructions = soup.find_all("instruction")
    
    if instructions != None:
        recipe["instructions"] = []
        for instruction in instructions:
            recipe["instructions"].append(sub("\n +", "\n",sub(" +", " ", instruction.text.strip())))
    
    return recipe

# Generate the redirect url for the new recipe page with the given parameters
def new_recipe_get_request(recipe):
    # Format the get request with the given parameters
    get_request = "?"
    
    for key in recipe:
        get_request += f"{key}={recipe[key]}&"
    
    return "/new_recipe" + get_request

# Returns a list containing all recipes by the user
def list_all_recipes(c):
    c.execute("SELECT id, title, description, preparation_time, cook_time FROM recipes WHERE user_id = %s ORDER BY creation_date DESC;", (session["uid"],))
    
    query = c.fetchall()
    
    if not query:
        return None
    
    recipes = [list(recipe) for recipe in query]
    
    return recipes

# Remove recipe with the given id from the database
# Returns True if successful
def remove_recipe(c, db, recipe_id: int):
    try:
        c.execute("DELETE FROM recipe_ingredients WHERE recipe_id = %s;", (recipe_id,))
        c.execute("DELETE FROM instructions WHERE recipe_id = %s;", (recipe_id,))
        c.execute("DELETE FROM recipes WHERE id = %s;", (recipe_id,))
    except Exception as e:
        return error(f"Something went wrong with removing the recipe from the database. Error: {e}", 500)
    
    db.commit()
    return True


# - Registration
# Validate: email address format - returns bool
def validate_email(email: str):
    format = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    if match(format,email):
        return True
    return False

# Generate hash from password
def generate_hash(password: str):
    werkzeug_hash = generate_password_hash(password, method=encryption_method, salt_length=5).split("$")
    salt = werkzeug_hash[1]
    hash = werkzeug_hash[2]
    return (salt, hash)

# - Login
# Check if the hash matches the password
def check_hash(hash: str, salt: str, password: str):
    return check_password_hash(f"{encryption_method}${salt}${hash}", password)

# - Password reset
# Check if given expiration date "expired" or not - returns True if expired otherwise False
def check_expiration(expiration, exp_timezone=timezone.utc):
    expiration_date = expiration.replace(tzinfo=exp_timezone)
    current_datetime = datetime.now(exp_timezone)
    
    # Throw error if token already expired
    if current_datetime > expiration_date:
        return True
    
    return False