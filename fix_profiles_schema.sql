-- FIX PROFILES SCHEMA (SAFE VERSION)
-- Run this to add missing columns without deleting the table or policies.

-- 1. Add missing columns safely
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS full_name TEXT,
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'basic';

-- 2. Ensure Role Constraint exists
DO $$ 
BEGIN 
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
    ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check CHECK (role IN ('basic', 'advanced', 'collaborator', 'admin'));
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- 3. Update the Trigger Function (to handle future signups)
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, role, full_name)
  VALUES (
    new.id, 
    new.email,
    'basic', 
    COALESCE(new.raw_user_meta_data->>'full_name', '')
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    -- Don't overwrite role if it exists, unless it's null
    role = COALESCE(public.profiles.role, 'basic'); 
  RETURN new;
EXCEPTION
  WHEN others THEN
    RAISE LOG 'Error in handle_new_user: %', SQLERRM;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Re-bind trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 4. FORCE ADMIN UPDATE
-- This ensures your user gets the 'admin' role and email set
INSERT INTO public.profiles (id, email, role, full_name)
SELECT id, email, 'admin', 'Admin User'
FROM auth.users
WHERE email = 'cgiottoli@gmail.com'
ON CONFLICT (id) DO UPDATE SET 
    role = 'admin',
    email = EXCLUDED.email;
