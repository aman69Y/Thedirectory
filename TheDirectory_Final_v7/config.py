import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY','change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL','sqlite:///the_directory.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GIPHY_API_KEY = os.environ.get('GIPHY_API_KEY','')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    DEFAULT_AVATAR = "https://i.redd.it/why-are-the-blank-profile-pictures-different-v0-x6pug5d3kose1.jpg?width=225&format=pjpg&auto=webp&s=4d79be6d668557f3469afaf57478b2b7ffb78bcf"
