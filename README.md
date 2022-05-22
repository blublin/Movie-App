Final project - Movie App

Ben Lublin
Maria Gorbunova

CIS 41B Adv Python
Mar 23, 2021

Current Issue:
Python Library PIL (Python Image Library) is discontinued. Requires updated to Pillow (PIL Fork).


Overview:
The intention of the project was to create a (mostly) single window app that allows users to search for and track movies. They can search for movies online through an API or view stored movies from their own list by searching a database file.
On the backend are the api and database calls, data sorting and routing.
On the frontend are all the tkinter windows and widgets to try and create a clean environment to search and browse movies.

Included with the project:
backend.py - API, sqlite database
MovieApp.py - frontend GUI
Avatars(folder) - png image files for users to pick from
placeholder.jpeg - for movies that don't have an image
search_button_30px.png - Image for search button because that's how cool people roll!

Created by project:
moviesDB.db - sqlite3 database storing movie data (including poster images in byte form in a BLOB column)
.user_profile - folder to store user profile [This can be deleted to reset the user creation process]
.user_profile/username.txt - stores username in 1 line
.user_profile/user_avatar.png - a copy of the avatar the user chooses
