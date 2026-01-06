-- ENABLE ADMIN UPDATES
-- Run this to allow Admins to change other users' roles.

-- 1. Create Policy: Admins can UPDATE all profiles
CREATE POLICY "Admins can update all profiles"
ON public.profiles FOR UPDATE
USING (
  (SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin'
)
WITH CHECK (
  (SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin'
);
