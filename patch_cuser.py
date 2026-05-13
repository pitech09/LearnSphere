import re

path = '.venv/lib/python3.14/site-packages/cuser/compat.py'
try:
    with open(path, 'r') as f:
        content = f.read()
    new_content = re.sub(r'lazy\(get_user_model,\s*AUTH_USER_MODEL\)',
                         'lazy(get_user_model, object)',
                         content)
    with open(path, 'w') as f:
        f.write(new_content)
    print("Patched cuser/compat.py successfully")
except FileNotFoundError:
    print("cuser/compat.py not found – skipping")
