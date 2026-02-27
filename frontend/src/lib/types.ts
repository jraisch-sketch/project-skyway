export type School = {
  id: number;
  name: string;
  team_type: string;
  conference: string;
  school_website: string;
  athletic_dept_website: string;
  cycling_website: string;
  city: string;
  state: string;
  latitude: number | null;
  longitude: number | null;
  road: boolean;
  mtb: boolean;
  cyclocross: boolean;
  track: boolean;
  cycling_program_status: string;
  logo: string | null;
};

export type SchoolDetail = School & {
  street_address: string;
  zip_code: string;
  address_complete: string;
  geocode_status: string;
  school_website: string;
  athletic_dept_website: string;
  cycling_website: string;
  roster_male: number | null;
  roster_female: number | null;
  program_strengths: string;
  avg_cost: string;
  acceptance_rate: string;
  graduation_rate: string;
  enrollment: string;
  institution_control: string;
  institution_level: string;
  locale: string;
  head_coach: string;
  instagram: string;
  facebook: string;
  twitter: string;
};

export type FilterOptions = {
  team_types: string[];
  conferences: string[];
  states: string[];
  disciplines: string[];
  sort_options: string[];
};

export type FavoriteSchool = {
  id: number;
  school: School;
  visibility: 'private' | 'public';
  created_at: string;
};

export type ConferenceSummary = {
  id: number;
  name: string;
  long_name: string;
  acronym: string;
  description: string;
  team_count: number;
};

export type CmsBlock = {
  type: string;
  text?: string;
  title?: string;
  level?: number;
  href?: string;
  style?: 'ordered' | 'unordered';
  items?: string[];
  caption?: string;
  headers?: string[];
  rows?: string[][];
};

export type CmsWidget = {
  id: number;
  name: string;
  slug: string;
  title: string;
  body: CmsBlock[];
};

export type CmsWidgetPlacement = {
  id: number;
  slot: 'content_top' | 'content_bottom' | 'sidebar' | 'home';
  sort_order: number;
  widget: CmsWidget;
};

export type CmsNavItem = {
  id: number;
  title: string;
  page_slug: string;
  external_url: string;
  open_new_tab: boolean;
  sort_order: number;
  children: CmsNavItem[];
};

export type CmsNavigation = {
  id: number;
  name: string;
  slug: string;
  description: string;
  items: CmsNavItem[];
};

export type CmsPage = {
  id: number;
  title: string;
  slug: string;
  summary: string;
  body: CmsBlock[];
  template: 'standard' | 'wide';
  show_title: boolean;
  show_sidebar_navigation: boolean;
  parent_slug: string;
  navigation: CmsNavigation | null;
  widgets: CmsWidgetPlacement[];
  updated_at: string;
};
