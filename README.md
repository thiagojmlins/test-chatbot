# Backend

This is an API built using FastAPI. The API allows users to:
- Send messages and receive chatbot replies.
- Edit and delete messages.
- Retrieve the chat history.
- Use JWT-based authentication to secure the API endpoints.

The API integrates with SQLite as the database and uses JWT for authentication. The chatbot replies are mocked to simulate an interaction with a chatbot service (such as OpenAI's GPT).

## Table of Contents
1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Project Structure](#project-structure)
4. [Setup and Installation](#setup-and-installation)
5. [Running the Application](#running-the-application)
6. [Authentication](#authentication)
7. [Testing the API](#testing-the-api)
8. [API Endpoints](#api-endpoints)

## Features
- **JWT Authentication**: Users must authenticate to interact with the API.
- **Message Management**: Users can send, edit, and delete messages, and retrieve chat history.
- **User Management**: Users can sign up and log in using their username and password.
- **SQLite Database**: Messages and user data are stored in an SQLite database.
- **Mocked Chatbot**: The chatbot replies are mocked for demonstration purposes.

## Technologies Used
- **FastAPI**: A modern, fast (high-performance) web framework for building APIs in Python.
- **SQLite**: A lightweight relational database.
- **SQLAlchemy**: ORM used to interact with the SQLite database.
- **Pydantic**: For data validation and serialization.
- **JWT (JSON Web Tokens)**: Used for secure authentication.
- **passlib**: Library for password hashing.
- **python-jose**: Used for handling JWT.
- **Pytest**: Testing framework used to test the API.

## Project Structure

```
├── app.py
├── auth.py
├── chatbot.py
├── database.py
├── models.py
├── requirements.txt
├── schemas.py
├── tests
│   ├── __init__.py
│   └── test_app.py
└── README.md
```

## Setup and Installation

### Prerequisites
- Python 3.9 or later.
- SQLite (comes installed with Python by default).
- [virtualenv](https://virtualenv.pypa.io/en/latest/) (optional, but recommended).

### Clone the Repository
```bash
git clone https://github.com/thiagojmlins/test-chatbot.git
cd chatbot-api
```

### Create a Virtual Environment and Activate it

#### For Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

#### For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### Install the dependencies

```bash
pip install -r requirements.txt
```

### Set up environment variables
```makefile
SECRET_KEY="your_secret_key"
```

## Running the application

### Run the FastAPI server
```bash
uvicorn app:app --reload
```

This will start the API server at `http://127.0.0.1:8000`.

### Interactive API Documentation

FastAPI provides interactive documentation at `http://127.0.0.1:8000/docs`.


## Authentication

### User Creation (Sign Up)

To create an user (sign up), send a `POST` request to `/users/` with the following JSON body:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

### Login and get a JWT token

To login and obtain the JWT token, send a `POST` request to `/token`:

- Endpoint: `/token``
- Method: `POST``
- Body (form data): `username=your_username` and `password=your_password`.

You will receive a response containing the `access_token`:

```json
{
  "access_token": "your_jwt_token",
  "token_type": "bearer"
}
```

### Using the token for authenticated requests

Include the token in the `Authorization` header when making authenticated requests:

```makefile
Authorization: Bearer your_jwt_token
```

## Testing the API

### Run unit tests

To run the unit tests using `pytest`:

```bash
pytest
```

## API endpoints

### Authentication Endpoints

1. #### Sign Up (User Creation)
    - `POST /users/`
    - Request body: `{ "username": "your_username", "password": "your_password" }`
    - Response: Created user.

2. #### Login (Get Token)
    - `POST /token`
    - Request body (form data): `{ "username": "your_username", "password": "your_password" }`
    - Response: `{ "access_token": "your_jwt_token", "token_type": "bearer" }`

### Message Management Endpoints (Require Authentication)

1. ### Send a Message
    - `POST /send_message`
    - Request body: `{ "content": "your_message" }`
    - Response: The message and the chatbot reply.

2. ### Edit a Message
    - `PUT /edit_message/{message_id}`
    - Request body: `{ "content": "updated_message_content" }`
    - Response: The updated message and updated reply.

3. ### Delete a Message
    - `DELETE /delete_message/{message_id}`
    - Response: The deleted message.

4. ### Get Chat History
    - `GET /history`
    - Response: A list of all messages and replies.


## License

This project is licensed under the MIT license.
