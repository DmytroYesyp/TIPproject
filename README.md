# TIPproject

Gemini 2.5 Flash app creation

https://g.co/gemini/share/b5a3837044af

## Overview

TIPproject is a robust, real-time chat application built with FastAPI and PostgreSQL, leveraging WebSockets for instant message delivery. It provides core functionalities for user management, chat room organization, and seamless communication. The application is designed with a clear separation of concerns, ensuring maintainability and scalability.

## Features

* **User Authentication**: Secure user registration and login using JWT (JSON Web Tokens) with password hashing (bcrypt).
* **Role-Based Authorization**: Differentiates between regular users and administrators for access control (e.g., room deletion).
* **Chat Room Management**:
    * Create new public chat rooms.
    * List all available chat rooms.
    * Retrieve details for specific chat rooms.
    * Delete chat rooms (administrator-only).
* **Real-time Messaging (WebSockets)**:
    * Instantaneous message sending and receiving within chat rooms.
    * Automatic loading of recent message history upon joining a room.
    * Dynamic display of active users within each chat room.
* **Database Integration**: Persistent storage of users, rooms, and messages using PostgreSQL and SQLAlchemy ORM.

## Technology Stack

The application is built using the following technologies:

* **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
    * **Description**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
* **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
    * **Description**: A lightning-fast ASGI server, perfect for running FastAPI applications.
* **Database**: [PostgreSQL](https://www.postgresql.org/)
    * **Description**: A powerful, open-source object-relational database system known for its reliability, feature robustness, and performance.
* **ORM (Object-Relational Mapper)**: [SQLAlchemy](https://www.sqlalchemy.org/)
    * **Description**: The Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
* **PostgreSQL Adapter**: [psycopg2-binary](https://pypi.org/project/psycopg2-binary/)
    * **Description**: PostgreSQL adapter for Python, required by SQLAlchemy to connect to PostgreSQL.
* **Password Hashing**: [Passlib](https://passlib.readthedocs.io/en/stable/) with [bcrypt](https://pypi.org/project/bcrypt/)
    * **Description**: Provides cryptographic password hashing functions for secure password storage and verification.
* **JSON Web Tokens (JWT)**: [Python-Jose](https://python-jose.readthedocs.io/en/latest/)
    * **Description**: A comprehensive JWT implementation for Python, used for authentication tokens.
* **Data Validation/Serialization**: [Pydantic](https://pydantic-docs.helpmanual.io/)
    * **Description**: Data validation and settings management using Python type hints, tightly integrated with FastAPI for schema definition and request/response validation.
* **Real-time Communication**: [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
    * **Description**: A communication protocol that provides full-duplex communication channels over a single TCP connection, enabling real-time chat.
* **CORS Middleware**: `fastapi.middleware.cors.CORSMiddleware`
    * **Description**: Handles Cross-Origin Resource Sharing (CORS) policies, allowing web browsers to make requests to the API from different origins (e.g., a separate frontend application).

## Setup and Installation

Follow these steps to get the application running locally.

### Prerequisites

* Python 3.8+
* PostgreSQL installed and running
* `psql` command-line tool or a GUI client like pgAdmin (optional, for database management)