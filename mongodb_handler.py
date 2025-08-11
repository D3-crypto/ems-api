"""
MongoDB Connection Handler for Employee Management System (EMS) API

This module provides direct MongoDB connection for storing employee and pandit data
while Django uses SQLite for its internal operations (migrations, sessions, etc.)
"""

import pymongo
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)

class MongoDBHandler:
    _instance = None
    _client = None
    _database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            connection_string = config('MONGODB_CONNECTION_STRING', default='mongodb://localhost:27017')
            database_name = config('MONGODB_DATABASE_NAME', default='EMS')
            
            self._client = pymongo.MongoClient(connection_string)
            self._database = self._client[database_name]
            
            # Test connection
            self._client.server_info()
            logger.info(f"Connected to MongoDB database: {database_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_database(self):
        """Get the MongoDB database instance"""
        if self._database is None:
            self.connect()
        return self._database
    
    def get_collection(self, collection_name):
        """Get a specific collection from the database"""
        return self.get_database()[collection_name]
    
    def close_connection(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

# Global instance
mongo_handler = MongoDBHandler()
