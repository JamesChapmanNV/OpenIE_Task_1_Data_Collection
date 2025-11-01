"""
Database connectors for OIE Search.
Provides access to Postgres and MongoDB backends for seed iteration
and query generation.
"""

from .postgres_runner import generate_queries_postgres
from .mongo_runner import generate_queries_mongo

__all__ = ["generate_queries_postgres", "generate_queries_mongo"]

