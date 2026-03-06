from pymongo import MongoClient
db = MongoClient('mongodb://localhost:27017/')['smarter_blinkit']
r = db.products.delete_many({})
print(f'Deleted {r.deleted_count} products')
print(f'Remaining: {db.products.count_documents({})}')
