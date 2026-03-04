
try:
    from app import app
    with app.test_request_context():
        found = False
        for rule in app.url_map.iter_rules():
            if "reveal" in rule.rule:
                print(f"Rule: {rule.rule}, Methods: {list(rule.methods)}")
                found = True
        if not found:
            print("No 'reveal' route found in app.url_map")
except Exception as e:
    print(f"Error checking routes: {e}")
