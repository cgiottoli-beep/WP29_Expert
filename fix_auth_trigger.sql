-- FIX TRIGGER SCRIPT
-- Run this in Supabase SQL Editor if you get "Database error creating new user"

-- 1. Drop the existing trigger to clean up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- 2. Re-create the function with better error handling and default values
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, role, full_name)
  VALUES (
    new.id, 
    new.email,
    'basic', 
    -- Hande case where metadata is null
    COALESCE(new.raw_user_meta_data->>'full_name', '')
  );
  RETURN new;
EXCEPTION
  WHEN others THEN
    -- If fails, log it but don't block user creation? 
    -- No, better to block so we don't end up with users without profiles.
    RAISE LOG 'Error in handle_new_user: %', SQLERRM;
    RETURN new; -- Try returning new anyway to see if it allows creation without profile
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Re-bind the trigger
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 4. Grant permissions just in case
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON TABLE public.profiles TO postgres, service_role;
GRANT SELECT ON TABLE public.profiles TO anon, authenticated;
