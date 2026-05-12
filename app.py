"""FastAPI application entry point for the user management API.

This module defines the main FastAPI application instance and exposes two endpoints: `list_users` for retrieving all users and `create_user` for adding a new user. The application is configured with default settings and serves as the root router for user-related operations.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import UserCreate, UserOut

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

_users: list[UserOut] = []


@app.get("/users", response_model=list[UserOut])
def list_users():
    """Get all users (GET /users).

    Returns the full list of users stored in the in-memory collection.

    Returns:
        A list of UserOut objects representing every registered user.
    """
    return _users


@app.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate):
    """Create a new user (POST /users).

    Checks whether the provided email is already taken. If not, creates a new
    UserOut instance with an auto-incremented ID and returns it.

    Args:
        payload: The user creation payload containing the email address.

    Returns:
        The newly created user as a UserOut response model.

    Raises:
        HTTPException: 409 if the email is already registered.
    """
    if any(u.email == payload.email for u in _users):
        raise HTTPException(status_code=409, detail="email taken")
    new = UserOut(id=len(_users) + 1, email=payload.email)
    _users.append(new)
    return new