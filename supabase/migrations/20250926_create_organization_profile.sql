-- Create organization_profile table for storing organization mission, vision, and values

CREATE TABLE public.organization_profile (
  id text NOT NULL DEFAULT gen_random_uuid()::text,
  org_id text NOT NULL,
  vision text,
  mission text,
  core_values jsonb DEFAULT '[]'::jsonb,
  company_culture text,
  founding_year integer,
  industry text,
  company_size text CHECK (company_size IN ('startup', 'small', 'medium', 'large', 'enterprise')),
  headquarters text,
  website_url text,
  sustainability_goals text,
  diversity_commitment text,
  community_involvement text,
  created_by text,
  last_updated_by text,
  created_at timestamp with time zone DEFAULT now() NOT NULL,
  updated_at timestamp with time zone DEFAULT now() NOT NULL,
  CONSTRAINT organization_profile_pkey PRIMARY KEY (id),
  CONSTRAINT organization_profile_org_id_unique UNIQUE (org_id),
  CONSTRAINT organization_profile_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE,
  CONSTRAINT organization_profile_founding_year_check CHECK (founding_year >= 1800 AND founding_year <= 2030),
  CONSTRAINT organization_profile_vision_length_check CHECK (char_length(vision) <= 1000),
  CONSTRAINT organization_profile_mission_length_check CHECK (char_length(mission) <= 1000),
  CONSTRAINT organization_profile_company_culture_length_check CHECK (char_length(company_culture) <= 2000),
  CONSTRAINT organization_profile_industry_length_check CHECK (char_length(industry) <= 100),
  CONSTRAINT organization_profile_headquarters_length_check CHECK (char_length(headquarters) <= 200),
  CONSTRAINT organization_profile_sustainability_goals_length_check CHECK (char_length(sustainability_goals) <= 1500),
  CONSTRAINT organization_profile_diversity_commitment_length_check CHECK (char_length(diversity_commitment) <= 1500),
  CONSTRAINT organization_profile_community_involvement_length_check CHECK (char_length(community_involvement) <= 1500)
);

-- Create indexes for better performance
CREATE INDEX idx_organization_profile_org_id ON public.organization_profile(org_id);
CREATE INDEX idx_organization_profile_created_at ON public.organization_profile(created_at);
CREATE INDEX idx_organization_profile_updated_at ON public.organization_profile(updated_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.organization_profile ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Policy: Organization members can view organization profiles
CREATE POLICY "Organization members can view organization profiles" ON public.organization_profile
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.organization_members om 
      WHERE om.org_id = organization_profile.org_id 
      AND om.user_id = auth.uid()::text
      AND om.role IN ('member', 'admin', 'owner')
    )
  );

-- Policy: Organization owners and admins can create organization profiles
CREATE POLICY "Organization owners and admins can create organization profiles" ON public.organization_profile
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.organization_members om 
      WHERE om.org_id = organization_profile.org_id 
      AND om.user_id = auth.uid()::text
      AND om.role IN ('admin', 'owner')
    )
  );

-- Policy: Organization owners and admins can update organization profiles
CREATE POLICY "Organization owners and admins can update organization profiles" ON public.organization_profile
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.organization_members om 
      WHERE om.org_id = organization_profile.org_id 
      AND om.user_id = auth.uid()::text
      AND om.role IN ('admin', 'owner')
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.organization_members om 
      WHERE om.org_id = organization_profile.org_id 
      AND om.user_id = auth.uid()::text
      AND om.role IN ('admin', 'owner')
    )
  );

-- Policy: Organization owners can delete organization profiles
CREATE POLICY "Organization owners can delete organization profiles" ON public.organization_profile
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM public.organization_members om 
      WHERE om.org_id = organization_profile.org_id 
      AND om.user_id = auth.uid()::text
      AND om.role = 'owner'
    )
  );

-- Add a trigger to update the updated_at column
CREATE OR REPLACE FUNCTION update_organization_profile_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_organization_profile_updated_at
  BEFORE UPDATE ON public.organization_profile
  FOR EACH ROW
  EXECUTE FUNCTION update_organization_profile_updated_at();

-- Add comments for documentation
COMMENT ON TABLE public.organization_profile IS 'Stores organization profiles including mission, vision, values, and company information';
COMMENT ON COLUMN public.organization_profile.id IS 'Primary key for the organization profile';
COMMENT ON COLUMN public.organization_profile.org_id IS 'Foreign key to organizations table';
COMMENT ON COLUMN public.organization_profile.vision IS 'Organization vision statement (max 1000 chars)';
COMMENT ON COLUMN public.organization_profile.mission IS 'Organization mission statement (max 1000 chars)';
COMMENT ON COLUMN public.organization_profile.core_values IS 'JSON array of core values with title, description, icon, order';
COMMENT ON COLUMN public.organization_profile.company_culture IS 'Description of company culture (max 2000 chars)';
COMMENT ON COLUMN public.organization_profile.founding_year IS 'Year the organization was founded (1800-2030)';
COMMENT ON COLUMN public.organization_profile.industry IS 'Industry sector (max 100 chars)';
COMMENT ON COLUMN public.organization_profile.company_size IS 'Company size category (startup, small, medium, large, enterprise)';
COMMENT ON COLUMN public.organization_profile.headquarters IS 'Headquarters location (max 200 chars)';
COMMENT ON COLUMN public.organization_profile.website_url IS 'Organization website URL';
COMMENT ON COLUMN public.organization_profile.sustainability_goals IS 'Sustainability and environmental goals (max 1500 chars)';
COMMENT ON COLUMN public.organization_profile.diversity_commitment IS 'Diversity and inclusion commitment (max 1500 chars)';
COMMENT ON COLUMN public.organization_profile.community_involvement IS 'Community involvement and social impact (max 1500 chars)';
COMMENT ON COLUMN public.organization_profile.created_by IS 'User ID who created the profile';
COMMENT ON COLUMN public.organization_profile.last_updated_by IS 'User ID who last updated the profile';
COMMENT ON COLUMN public.organization_profile.created_at IS 'Timestamp when the profile was created';
COMMENT ON COLUMN public.organization_profile.updated_at IS 'Timestamp when the profile was last updated';
