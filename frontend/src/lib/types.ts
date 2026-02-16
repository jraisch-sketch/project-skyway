export type School = {
  id: number;
  name: string;
  team_type: string;
  conference: string;
  city: string;
  state: string;
  latitude: number | null;
  longitude: number | null;
  road: boolean;
  mtb_xc: boolean;
  mtb_st: boolean;
  mtb_enduro: boolean;
  mtb_downhill: boolean;
  mtb_slalom: boolean;
  cyclocross: boolean;
  cycling_program_status: string;
  logo: string | null;
};

export type SchoolDetail = School & {
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
