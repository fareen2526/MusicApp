# Fareen Alam - Header Comment
# helpers.py is additional Python code that has to do with the user's login information. 

import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """
    Render a custom error message (apology) to the user.

    Args:
        message (str): The error message to display.
        code (int): The HTTP status code (default is 400).

    Returns:
        Renders the 'apology.html' template with the error message and status code.
    """
    def escape(s):
        """
        Escape special characters in a string to make it safe for use in URLs.

        Args:
            s (str): The string to escape.

        Returns:
            The escaped string.
        """
        # Replace special characters with their URL-safe equivalents
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    # Render the apology template with the status code and escaped message
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorator to ensure that a route requires a logged-in user.

    If the user is not logged in (i.e., no 'user_id' in session), 
    they are redirected to the login page.

    Args:
        f (function): The route function to decorate.

    Returns:
        The decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is logged in by checking the session
        if session.get("user_id") is None:
            # Redirect to the login page if not logged in
            return redirect("/login")
        # Otherwise, proceed with the original function
        return f(*args, **kwargs)
    return decorated_function


def usd(value):
    """
    Format a numeric value as a USD currency string.

    Args:
        value (float or int): The numeric value to format.

    Returns:
        A string formatted as USD (e.g., "$1,234.56").
    """
    return f"${value:,.2f}"


def is_int(s):
    """
    Check if a string can be converted to an integer.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string can be converted to an integer, False otherwise.
    """
    try:
        # Attempt to convert the string to an integer
        int(s)
        return True
    except ValueError:
        # Return False if conversion fails (e.g., non-numeric string)
        return False