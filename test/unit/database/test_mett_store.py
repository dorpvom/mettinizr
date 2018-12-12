from database.mett_store import MettStore
from mongomock import MongoClient


def mock_store(monkeypatch):
    monkeypatch.setattr('database.mett_store.MongoClient', MongoClient)
    return MettStore()
