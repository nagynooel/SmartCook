"""
    @package: smartcook
    @author: Noel Nagy
    @website: https://github.com/nagynooel
    ©2022 Noel Nagy - All rights reserved.
"""
# --- Main app routing file

from flask import Flask, render_template, redirect, flash, request, session, url_for
from flask_session import Session

import mysql.connector
from os import environ, path
from glob import glob

from secrets import token_urlsafe

from helper import error, logged_in_only, signed_out_only, redirect_alert, allowed_image_extension, get_file_extension, validate_email, generate_hash, check_hash, create_msg, send_email, list_all_recipes, remove_recipe, check_expiration, remove_leading_zeros
from werkzeug.utils import secure_filename

from random import randint


# -- Globale variables
ALLOWED_MEASUREMENTS = ["g","dag","kg","cup","pinch","pc(s)"]

# -- Configure application
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = environ.get("APP_SECRET_KEY")

# Register filter to remove leading 0
app.jinja_env.filters["no_leading_zero"] = remove_leading_zeros

# - Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# - Image Upload
app.config['UPLOAD_FOLDER'] = "./static/user_uploads/"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# - Database connection
db = mysql.connector.connect(
    host = environ.get("DATABASE_HOST"),
    user = environ.get("DATABASE_USER"),
    password = environ.get("DATABASE_PASSWORD"),
    database = environ.get("DATABASE_NAME")
)

c = db.cursor(buffered=True)


# -- Handlers
# Pass the glob function for every request
@app.context_processor
def handle_context():
    return dict(glob=glob)


# -- Routes
# Dashboard
@app.route('/')
@logged_in_only
def index():
    recipes = list_all_recipes(c)
    
    return render_template("dashboard.html", recipes=recipes)


# - Recipe functions
# Create new recipe
@app.route('/new_recipe', methods=["GET", "POST"])
@logged_in_only
def new_recipe():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        title = request.form.get("title")
        description = request.form.get("description")
        
        # Throw error if number fields are not numbers
        try:
            prep_hour = int(request.form.get("prep_hour"))
            prep_minute = int(request.form.get("prep_minute"))
            cook_hour = int(request.form.get("cook_hour"))
            cook_minute = int(request.form.get("cook_minute"))
            
            serving = int(request.form.get("serving"))
        except:
            return redirect_alert("/new_user", "Please input only numbers to number fields!")
        
        ingredients = []
        
        # Get all data of the ingredients and validate them
        for quantity in request.form.getlist("quantity"):
            if not quantity or not quantity.isnumeric():
                return redirect_alert("/new_recipe", "Please write only numeric characters in quantity fields!")
            
            ingredients.append({"quantity":quantity})
        
        for i, measurement in enumerate(request.form.getlist("measurement")):
            if measurement not in ALLOWED_MEASUREMENTS:
                return redirect_alert("/new_recipe", "Measurement not allowed!")
            
            ingredients[i]["measurement"] = measurement
        
        for i, ingredient_name in enumerate(request.form.getlist("ingredient-name")):
            if not ingredient_name:
                return redirect_alert("/new_recipe", "Please fill out all required fields!")
            if len(ingredient_name) > 100:
                return redirect_alert("/new_recipe", "Ingredient name too long! (Maximum 100 characters per ingredient name is allowed.)")
            
            ingredients[i]["ingredient-name"] = ingredient_name
        
        instructions = []
        
        # Get steps and validate them
        for i, instruction in enumerate(request.form.getlist("step-text")):
            if not instruction:
                return redirect_alert("/new_recipe", "Please fill out all required fields!")
            if len(instruction) > 1000:
                return redirect_alert("/new_recipe", "Instruction too long! (Maximum 1000 characters per instruction is allowed.)")
            
            instructions.append({"number":i+1, "instruction":instruction})
        
        # - Validate inputs
        # Validate: all required fields are filled out
        if not title or prep_hour is None or prep_minute is None or cook_hour is None or cook_minute is None or serving is None:
            return redirect_alert("/new_recipe", "Please fill out all required fields!")
        
        # Validate: title and description not longer than allowed (255 and 1000 char respectively)
        if len(title) > 255 or len(description) > 1000:
            return redirect_alert("/new_recipe", "Title or description is longer than allowed!")
        
        # Validate: correct time format
        if not 0 <= prep_hour <= 99 or not 0 <= cook_hour <= 99 or not 0 <= prep_minute <= 59 or not 0 <= cook_minute <= 59:
            return redirect_alert("/new_recipe", "Please enter a valid preparation and cook time!")
        
        # Check: if recipe image was uploaded (optional)
        # Validate: exstension is allowed
        
        # possible values:
        # False = no file uploaded or file did not meet requirements
        # File object = image is uploaded and meets requirements
        recipe_image = False
        
        if "image-file" in request.files and request.files['image-file'].filename != "":
            # Save image to variable
            recipe_image = request.files['image-file']
            
            # Secure filename
            recipe_image.filename = secure_filename(recipe_image.filename)
            
            if not allowed_image_extension(recipe_image.filename):
                return redirect_alert("/new_recipe", "Image file extension not allowed.")
        
        # - Create recipe
        # Recipes Table
        # Create recipe in database
        try:
            c.execute("INSERT INTO recipes (user_id, title, description, preparation_time, cook_time, servings) VALUES (%s, %s, %s, %s, %s, %s);", (session["uid"], title, description, f"{str(prep_hour).zfill(2)}{str(prep_minute).zfill(2)}", f"{str(cook_hour).zfill(2)}{str(cook_minute).zfill(2)}", serving))
            c.execute("SELECT LAST_INSERT_ID();")
            
            recipe_id = c.fetchone()[0]
            
            # Create ingredients, measurement units and link ingredients with recipe (via recipe_ingredients table)
            for ingredient in ingredients:
                # Get ingredient id (and upload ingredient if not in database)
                ing_name = ingredient["ingredient-name"]
                c.execute("SELECT id FROM ingredients WHERE name = %s;", (ing_name,))
                
                ing_id = c.fetchone()
                if not ing_id:
                    c.execute("INSERT INTO ingredients (name) VALUES (%s);", (ing_name,))
                    c.execute("SELECT LAST_INSERT_ID();")
                    ing_id = c.fetchone()[0]
                else:
                    ing_id = ing_id[0]
                
                # Get measurement id (and upload measurement if not in database)
                ing_measurement = ingredient["measurement"]
                c.execute("SELECT id FROM measurement_units WHERE unit = %s;", (ing_measurement,))
                
                measurement_id = c.fetchone()
                if not measurement_id:
                    c.execute("INSERT INTO measurement_units (unit) VALUES (%s);", (ing_measurement,))
                    c.execute("SELECT LAST_INSERT_ID();")
                    measurement_id = c.fetchone()[0]
                else:
                    measurement_id = measurement_id[0]
                
                # Link ingredient with recipe (recipe_ingredients table)
                c.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, measurement_id) VALUES (%s, %s, %s, %s);", (recipe_id, ing_id, ingredient["quantity"], measurement_id))
                
            
            # Create instructions in database
            for instruction in instructions:
                c.execute("INSERT INTO instructions (recipe_id, step_number, instruction) VALUES (%s, %s, %s);", (recipe_id, instruction["number"], instruction["instruction"]))
            
            # If image was uploaded save it to /user-uploads/recipe_images/ with the recipe id as filename
            if recipe_image != False:
                recipe_image.filename = str(recipe_id) + get_file_extension(recipe_image.filename)
                recipe_image.save(path.join(app.config['UPLOAD_FOLDER'] + "recipe_images/", recipe_image.filename))
            
            db.commit()
            
        except Exception as e:
            # If any part of the upload goes wrong roll back to last commit in database
            db.rollback()
            return error(f"Something went wrong with uploading your recipe to our database! Error: {e}", code=500)
        
        
        return redirect_alert(f"/recipes/{recipe_id}", "Recipe successfully created!", "success")
        
    # -- GET request
    return render_template("recipes/new_recipe.html")

# Show all of the users recipes (My Recipes page)
@app.route("/recipes")
@logged_in_only
def show_all_recipes():
    recipes = list_all_recipes(c)
    
    return render_template("recipes/my_recipes.html", recipes=recipes)

# Show recipe with the given id
@app.route("/recipes/<int:recipe_id>")
@logged_in_only
def recipe(recipe_id):
    # - Validate id
    # Validate: ID is given
    if not recipe_id:
        return redirect("/recipes")
    
    c.execute("SELECT user_id FROM recipes WHERE id = %s;", (recipe_id,))
    # Validate: recipe exists and is created by current user
    recipe_user_id = c.fetchone()
    
    if not recipe_user_id:
        return redirect_alert("/recipes", "Recipe with given id does not exist!")
    
    if recipe_user_id[0] != session["uid"]:
        return redirect_alert("/recipes", "You don't have access to the recipe with given id!")
    
    # - Get needed information of the recipe from the database
    # General recipe information
    c.execute("SELECT title, description, preparation_time, cook_time, servings FROM recipes WHERE id = %s;", (recipe_id,))
    query = c.fetchone()
    
    title = query[0]
    description = "None" if query[1] == "" else query[1]
    preparation_time = query[2]
    cook_time = query[3]
    servings = query[4]
    
    # Get image if it was uploaded else put no-image-selected.svg
    recipe_image = "img/no-image-selected.svg"
    
    if glob(f"{app.config['UPLOAD_FOLDER']}recipe_images/{recipe_id}.*"):
        extension = path.splitext(glob(f"{app.config['UPLOAD_FOLDER']}recipe_images/{recipe_id}.*")[0])[1]
        recipe_image = f"user_uploads/recipe_images/{recipe_id}{extension}"
    
    # Ingredients
    c.execute("SELECT ingredient_id, quantity, measurement_id FROM recipe_ingredients WHERE recipe_id = %s;", (recipe_id,))
    query = c.fetchall()
    
    ingredients = []
    
    for ingredient in query:
        ingredient_id = ingredient[0]
        ingredient_quantity = ingredient[1]
        ingredient_measurement_id = ingredient[2]
        
        temp_ingredient = {}
        
        temp_ingredient["quantity"] = ingredient_quantity
        
        c.execute("SELECT name FROM ingredients WHERE id = %s;", (ingredient_id,))
        temp_ingredient["name"] = c.fetchone()[0]
        
        c.execute("SELECT unit FROM measurement_units WHERE id = %s;", (ingredient_measurement_id,))
        temp_ingredient["unit"] = c.fetchone()[0]
        
        ingredients.append(temp_ingredient)
    
    # instructions
    c.execute("SELECT step_number, instruction FROM instructions WHERE recipe_id = %s;", (recipe_id,))
    query = c.fetchall()
    
    instructions = []
    
    for instruction in query:
        temp_instruction = {}
        
        temp_instruction["step_number"] = instruction[0]
        temp_instruction["instruction"] = instruction[1]
        
        instructions.append(temp_instruction)
    
    return render_template("recipes/recipe_viewer.html", recipe_id=recipe_id, title=title, description=description, prep_time=preparation_time, cook_time=cook_time, servings=servings, recipe_image=recipe_image, ingredients=ingredients, instructions=instructions)

@app.route("/remove/<int:recipe_id>")
@logged_in_only
def remove_recipe_page(recipe_id):
    # Check if next url is givem
    # Else set default (dashboard)
    next = request.args.get("next")
    
    if not next:
        next = ""
    
    # - Validate input
    # Valdiate: recipe with given id exists
    c.execute("SELECT user_id FROM recipes WHERE id = %s;", (recipe_id,))
    
    user_id = c.fetchone()
    
    if not user_id:
        return redirect_alert("/" + next, "Recipe with given ID not found!")
    
    # Validate: recipe belongs to the user
    user_id = user_id[0]
    
    if user_id != session["uid"]:
        return redirect_alert("/" + next, "Recipe with given ID does not belong to user!")
    
    # Remove recipe
    remove_recipe(c, db, recipe_id)
    
    return redirect_alert("/" + next, "Recipe deleted successfully!", "success")

@app.route("/random_recipe")
@logged_in_only
def random_recipe():
    # Validate: user has recipes
    c.execute("SELECT id FROM recipes WHERE user_id = %s;", (session["uid"],))
    
    recipe_ids = c.fetchall()
    
    if not recipe_ids:
        return redirect_alert("/", "You have no recipes yet!")
    
    # Generate a random number from 0 to the number of recipes user has
    random_num = randint(0, len(recipe_ids) - 1)
    
    return redirect(f"/recipes/{ recipe_ids[random_num][0] }")


# - Login and new user functionality
# Register new user
@app.route("/register", methods=["GET","POST"])
@signed_out_only
def register():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        username = request.form.get("username")
        email = request.form.get("email").lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")
        
        # - Validate inputs
        # Validate: all fields are filled out
        if not username or not email or not password or not confirm_password:
            return redirect_alert(f"/register?username={username}&email={email}", "Please fill out all fields!")
        
        # Validate: terms accepted
        if not request.form.get("terms-check"):
            return redirect_alert(f"/register?username={username}&email={email}", "Please read and accept terms and conditions to proceed!")
        
        # Validate: email format is valid
        if not validate_email(email):
            return redirect_alert(f"/register?username={username}", "E-mail address is not valid!")
        
        # Confirm: username is not already in database
        c.execute("SELECT username FROM users WHERE UPPER(username) = %s;", (username.upper(),))
        query = c.fetchone()
        
        if query is not None:
            return redirect_alert(f"/register?email={email}", "Username already exists!")
        
        # Confirm: email is not already in database
        c.execute("SELECT email FROM users WHERE email = %s;", (email,))
        query = c.fetchone()
        
        if query is not None:
            return redirect_alert(f"/register?username={username}", "E-mail address is already registered!")
        
        # Validate: password and confirm_password fields match
        if password != confirm_password:
            return redirect_alert(f"/register?username={username}&email={email}", "Passwords do not match!")
        
        # - Register user
        salt, hash = generate_hash(password)
        
        try:
            c.execute("INSERT INTO users (username, email, hash, salt) VALUES (%s, %s, %s, %s);", (username, email, hash, salt))
            c.execute("SELECT LAST_INSERT_ID();")
            db.commit()
        except Exception as e:
            return error(f"Something went wrong with registering you to our database! Error: {e}", code=500)
        
        # Log user in
        uid = c.fetchone()[0]
        
        session["uid"] = uid
        session["username"] = username
        
        return redirect_alert("/", "Registration is successful!", "success")
    
    # -- GET request
    # Autofill data from url
    username = request.args.get("username").strip() if request.args.get("username") else ""
    email = request.args.get("email").strip() if request.args.get("email") else ""
    
    return render_template("register.html", username=username, email=email)


# Log in to existing account
@app.route("/login", methods=["GET","POST"])
@signed_out_only
def login():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        username = request.form.get("username")
        password = request.form.get("password")
        
        # - Validate inputs
        # Validate: fields are not empty
        if not username or not password:
            return redirect_alert(f"/login", "Please fill out all fields!")
        
        # Get: hashed password and user id from users table
        c.execute("SELECT hash, salt, id FROM users WHERE UPPER(username) = %s;", (username.upper(),))
        query = c.fetchone()
        
        # Validate: user exists
        if not query:
            return redirect_alert(f"/login", "Incorrect username or password!")
        
        # Split query into variables
        hash, salt, uid = query
        
        # Validate: password matches hash
        if not check_hash(hash, salt, password):
            return redirect_alert(f"/login", "Incorrect username or password!")
        
        # - Log user in
        session["uid"] = uid
        session["username"] = username
        
        return redirect("/")
    
    # -- GET request
    return render_template("login.html")


# Log out from account
@app.route("/logout")
def logout():
    session.clear()
    
    return redirect("/login")


# Send email with reset link
@app.route("/reset_password", methods=["GET", "POST"])
@signed_out_only
def reset_password():
    # -- POST request
    if request.method == "POST":
        # - Get user input
        email = request.form.get("email").lower()
        
        # - Validate input
        # Validate: field not empty
        if not email:
            return redirect_alert("/reset_password", "Please fill out email field!")
        
        # Validate: email format is valid
        if not validate_email(email):
            return redirect_alert(f"/reset_password", "E-mail address is not valid!")
        
        # Validate: email is registered
        c.execute("SELECT username, id FROM users WHERE email = %s;", (email,))
        query = c.fetchone()
        
        if not query:
            return redirect_alert(f"/reset_password", "Email is not registered!")
        
        username, uid = query
        
        # - Generate reset token and store it in the database
        # Create uniqe token
        unique = False
        token = ""
        
        while not unique:
            token = token_urlsafe(64)
            
            c.execute("SELECT token FROM password_reset_tokens WHERE token = %s;", (token,))
            
            if c.fetchone() is None:
                unique = True
        
        # Insert token into database
        try:
            c.execute("INSERT INTO password_reset_tokens (token, user_id) VALUES (%s, %s);", (token, uid))
            db.commit()
        except Exception as e:
            return error(f"Something went wrong with creating your reset token in our database! Error: {e}", code=500)
        
        c.execute("SELECT expiration_date FROM password_reset_tokens WHERE token = %s;", (token,))
        expiration_date = c.fetchone()[0]
        url = f"{request.url_root}new_password?token={token}"
        
        # - Send password reset email
        try:
            msg = create_msg(email, "Password Reset", render_template("email/reset_password.txt", username=username, url=url, expiration_date=expiration_date), render_template("email/reset_password.html", username=username, url=url, expiration_date=expiration_date))
            
            send_email(msg)
        except Exception() as e:
            return error(f"Something went wrong with sending you the password reset email! Error: {e}", code=500)
        
        return redirect_alert("/reset_password", "Password reset email successfully sent!", "success")
        
    # -- GET request
    return render_template("reset_password.html")


# Create new password
@app.route("/new_password", methods=["GET", "POST"])
@signed_out_only
def new_password():
    # Validate given token
    # Returns true if valid else returns error message
    def validate_token(token: str):
        # Validate: Token is defined
        if not token:
            return "Token not set!"
        
        # Validate: Token exists
        c.execute("SELECT expiration_date, used FROM password_reset_tokens WHERE token = %s;", (token,))
        query = c.fetchone()
        
        if not query:
            return "Token is invalid!"
        
        # Validate: Token not expired
        expiration, used = query
        
        if check_expiration(expiration):
            return "Token expired! Please request a new one."
        
        # Validate: Token not used
        if used != 0:
            return "Token already used!"
        
        return True
    
    # -- POST request
    if request.method == "POST":
        # - Get user input
        token = request.form.get("token")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # - Validate inputs
        # Validate: token with nested function 
        token_valid = validate_token(token)
        
        if token_valid != True:
            return redirect_alert("/reset_password", token_valid)
        
        # Validate: fields are not empty
        if not new_password or not confirm_password:
            return redirect_alert(f"/new_password?token={token}", "Please fill out all fields!")
        
        # Validate: passwords match
        if new_password != confirm_password:
            return redirect_alert(f"/new_password?token={token}", "Passwords do not match!")
        
        # - Update user password
        # Get user ID
        c.execute("SELECT user_id FROM password_reset_tokens WHERE token = %s;", (token,))
        query = c.fetchone()
        
        if not query:
            return redirect_alert("/reset_password", "Token is invalid!")
        
        uid = query[0]
        
        # Hash password
        salt, hash = generate_hash(new_password)
        
        # Update password and set token status to used
        try:
            c.execute("UPDATE users SET hash = %s, salt = %s WHERE id = %s;", (hash, salt, uid))
            c.execute("UPDATE password_reset_tokens SET used = True WHERE token = %s;", (token,))
            
            db.commit()
        except Exception() as e:
            return error(f"Something went wrong with changing your password in our database! Error: {e}", code=500)
        
        return redirect_alert("/login", "Password successfully changed!", "success")
    
    # -- GET request
    # - Get token
    token = request.args.get("token")
    
    # Validate: token with nested function 
    token_valid = validate_token(token)
    
    if token_valid != True:
        return redirect_alert("/reset_password", token_valid)
    
    # Token validated user can access new password page
    return render_template("new_password.html", token=token)


# !! DELETE ON PRODUCTION !!
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)