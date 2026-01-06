-- FIX INFINITE RECURSION IN RLS
-- Run this to fix the "infinite recursion" error (42P17)

-- 1. Create a secure function to check admin status WITHOUT triggering RLS
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.profiles
    WHERE id = auth.uid() AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 
-- SECURITY DEFINER means this runs with the permissions of the creator (postgres), bypassing RLS

-- 2. Drop the recursive policies
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can update all profiles" ON public.profiles;

-- 3. Re-create policies using the safe function
CREATE POLICY "Admins can view all profiles"
ON public.profiles FOR SELECT
USING (
  public.is_admin()
);

CREATE POLICY "Admins can update all profiles"
ON public.profiles FOR UPDATE
USING (
  public.is_admin()
)
WITH CHECK (
  public.is_admin()
);

-- 4. Ensure basic users can still read their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" 
ON public.profiles FOR SELECT 
USING (
  auth.uid() = id
);
