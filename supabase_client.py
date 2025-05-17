from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kwmaeacwhglzzngzwzwr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3bWFlYWN3aGdsenpuZ3p3endyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzM5MjY5NCwiZXhwIjoyMDYyOTY4Njk0fQ.Zi4T4TE3caWQPWFhhSiAyI5L6HbabAkaA42-NdS53cI")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
