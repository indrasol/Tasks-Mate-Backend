-- Create daily_timesheets table
CREATE TABLE public.daily_timesheets (
    id SERIAL PRIMARY KEY,
    org_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    user_id UUID NOT NULL,
    entry_date DATE NOT NULL,
    in_progress TEXT,
    completed TEXT,
    blocked TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT daily_timesheets_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(org_id),
    CONSTRAINT daily_timesheets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id),
    CONSTRAINT daily_timesheets_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
    
    -- Unique constraint to prevent duplicate entries for same org/project/user/date
    CONSTRAINT daily_timesheets_unique_entry UNIQUE (org_id, project_id, user_id, entry_date)
);

-- Create indexes for better query performance
CREATE INDEX idx_daily_timesheets_org_id ON public.daily_timesheets(org_id);
CREATE INDEX idx_daily_timesheets_project_id ON public.daily_timesheets(project_id);
CREATE INDEX idx_daily_timesheets_user_id ON public.daily_timesheets(user_id);
CREATE INDEX idx_daily_timesheets_entry_date ON public.daily_timesheets(entry_date);
CREATE INDEX idx_daily_timesheets_org_date ON public.daily_timesheets(org_id, entry_date);

-- Add comments for documentation
COMMENT ON TABLE public.daily_timesheets IS 'Daily timesheet entries for tracking team member progress';
COMMENT ON COLUMN public.daily_timesheets.org_id IS 'Organization ID';
COMMENT ON COLUMN public.daily_timesheets.project_id IS 'Project ID';
COMMENT ON COLUMN public.daily_timesheets.user_id IS 'User ID from auth.users';
COMMENT ON COLUMN public.daily_timesheets.entry_date IS 'Date of the timesheet entry';
COMMENT ON COLUMN public.daily_timesheets.in_progress IS 'In progress tasks and notes';
COMMENT ON COLUMN public.daily_timesheets.completed IS 'Completed tasks and notes';
COMMENT ON COLUMN public.daily_timesheets.blocked IS 'Blocked tasks and reasons';

-- Enable Row Level Security
ALTER TABLE public.daily_timesheets ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only access timesheets from organizations they belong to
CREATE POLICY "Users can view timesheets from their organizations" ON public.daily_timesheets
    FOR SELECT USING (
        org_id IN (
            SELECT org_id 
            FROM public.organization_members 
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- Users can insert/update their own timesheets or if they have appropriate role
CREATE POLICY "Users can manage their own timesheets" ON public.daily_timesheets
    FOR ALL USING (
        user_id = auth.uid() OR
        org_id IN (
            SELECT org_id 
            FROM public.organization_members 
            WHERE user_id = auth.uid() 
            AND is_active = true 
            AND role IN ('owner', 'admin', 'manager')
        )
    );
