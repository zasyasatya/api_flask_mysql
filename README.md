
# API With Flask
## Source: https://github.com/firmangel8/api_flask
Demonstrate how to create simple CRUD API with Flask, this repository dedicated for lecturer activities.


## Features
- Basic CRUD
- Authetication and Authorization with JWT

Please clone this project and make sure to follow all instruction below:

## Requirements
- Python 3.7+
- Flask
- flask_jwt_extended
- flask_bcrypt
- python-dotenv
- mysql-connector-python
- Flask-Cors
- firebase-admin


## Preparation
**Import Database Dump**
- Please run DDL Script `stuff/DDL.txt` and DML Script `stuff/DML.txt`

**Import Postman Collection**
- Please import the collection in the postman, the file located in the directory `stuff/api_flask.postman_collection.json`

## Installation
### Step 1: Clone the repository
```
git clone https://github.com/zasyasatya/api_flask_mysql.git
cd api_flask_mysql
```

### Step 2: Installation package
- `pip install -r requirements.txt`

## How to Run with Debugging Mode
**Run this command in the root project directory **
- `flask run --debug`