def validate_branch_code(code):
    from supabase_client import supabase
    response = supabase.table("branches").select("code").execute()
    branch_codes = [item['code'] for item in response.data]
    return code.upper() in branch_codes

def hash_image(uploaded_file):
    import hashlib
    return hashlib.md5(uploaded_file.getvalue()).hexdigest()
