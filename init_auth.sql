-- AUTHENTICATION & PROFILES SETUP
-- Run this in Supabase SQL Editor

-- 1. Create a table for public profiles (linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT,
  role TEXT NOT NULL DEFAULT 'basic' CHECK (role IN ('basic', 'advanced', 'collaborator', 'admin')),
  full_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. Create Policy: Everyone can read their OWN profile
CREATE POLICY "Users can view own profile" 
ON public.profiles FOR SELECT 
USING (auth.uid() = id);

-- 4. Create Policy: Admins can view ALL profiles
-- Note: This requires a recursive check or a simple check if we trust the role column.
-- For simplicity, we assume the backend/service role handles admin tasks, 
-- but if we want frontend admin features, we need this:
CREATE POLICY "Admins can view all profiles"
ON public.profiles FOR SELECT
USING (
  (SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin'
);

-- 5. Trigger to auto-create profile on Sign Up
-- This ensures every new user gets a 'basic' role by default
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, role, full_name)
  VALUES (
    new.id, 
    new.email,
    'basic', -- Default role
    new.raw_user_meta_data->>'full_name'
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger binding
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 6. Helper to manually upgrade a user to Admin (Run manually if needed)
-- UPDATE public.profiles SET role = 'admin' WHERE email = 'YOUR_EMAIL';
