# SmartCook
**Created by: [Noel Nagy](https://github.com/nagynooel)**

**Creation Date: 2022.11.12 - 2022.12.30**

## Description:
SmartCook is an online cookbook. It allows you to collect all your recipes in place and has several cool features! One of them is the import feature.
You can save recipes from XML files or even webpages. These functionalities have limitations at this time, but are made to work with the most common websites/standards.
The importing from URL function uses [Google's standard recipe data structure](https://developers.google.com/search/docs/appearance/structured-data/recipe) as a base and only supports websites with simular structures.
The XML files supported should look simular to [this](https://www.wpultimaterecipe.com/docs/import-export-xml/).

## Setting up the website:
In order to start using this website first you need to download all files from the [GitHub repository](https://github.com/nagynooel/SmartCook) or clone it.

Next you will need to set up a mysql database. If you would like to host it locally I recomend you XAMPP.
Once you got the databse running you need to set up a few environment variables and install the modules in the requirements.txt file.

### Environment Variables:
```
# -- Virtual environment variables
# - Database
DATABASE_HOST = 127.0.0.1
DATABASE_USER = root
DATABASE_PASSWORD
DATABASE_NAME = smartcook

# - Mail
SMTP_EMAIL = 
SMTP_PASSWORD = 
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# - App
APP_SECRET_KEY = 
```

These are all necessary to run the application correctly.
Even the values, that I filled can be changed to anything to your liking. These are just some default settings.
If you would like to use the [Gmail SMTP server](https://kinsta.com/blog/gmail-smtp-server/) here is a nice guide for you to get started.

For the secret key you can generate any string randomly.

After these variables are set up and the modules installed you can run the **reset_databse.py** file. This will create all the neecsarry tables.
If you did all the steps above correctly, you can run the flask webapplication and start using it!

## Features:
**Account Related:**
* Basic Register, Login, Logout functionality with email confirmation
* Password Reset/Forgotten Password with token system and email confirmation
* Changeable Profile Picture
* Account Termination

**CookBook Related:**
* Recipe Creation with image
* Importing Recipes from other websites with URL
* Importing Recipes from XML file
* Exporting Recipes to XML
* Viewing and Deleting existing recipes
* Randomized Recipe Selection if user can't decide what to cook

## Sources:
The project uses some images that are not (or not entirely) made by me. Here are the links for those files:
* Chef Hat - [https://www.svgrepo.com/svg/191863/chef](https://www.svgrepo.com/svg/191863/chef)
* No Image Selected - [https://en.wikipedia.org/wiki/File:No_Image_%282879926%29_-_The_Noun_Project.svg](https://en.wikipedia.org/wiki/File:No_Image_%282879926%29_-_The_Noun_Project.svg)
* No Profile Picture - [https://freesvg.org/users-profile-icon](https://freesvg.org/users-profile-icon)

## Inspirations:
Here are some websites, that helped me get the project done and gave me ideas:
* Database Design - [https://dev.to/amckean12/designing-a-relational-database-for-a-cookbook-4nj6](https://dev.to/amckean12/designing-a-relational-database-for-a-cookbook-4nj6)
* Scraping Websites for recipes - [https://www.benawad.com/scraping-recipe-websites/](https://www.benawad.com/scraping-recipe-websites/)
* Recipe XML format - [https://www.wpultimaterecipe.com/docs/import-export-xml/](https://www.wpultimaterecipe.com/docs/import-export-xml/)