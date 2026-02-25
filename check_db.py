from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['feedback_platform_db']
feedbacks = list(db.feedback.find().sort([('_id', -1)]).limit(5))
for f in feedbacks:
    print(f"ID: {f['_id']}, DESC: {f.get('description')}, TX: {f.get('tx_hash', 'MISSING')}")
