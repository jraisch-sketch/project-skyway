import type { School } from '@/lib/types';

export const DISCIPLINE_LABELS: Record<string, string> = {
  road: 'Road',
  mtb_xc: 'MTB XC',
  mtb_st: 'MTB Short Track',
  mtb_enduro: 'MTB Enduro',
  mtb_downhill: 'MTB Downhill',
  mtb_slalom: 'MTB Slalom',
  cyclocross: 'Cyclocross',
};

const DISCIPLINE_KEYS = Object.keys(DISCIPLINE_LABELS) as Array<keyof School>;

export function getDisciplineLabels(school: School): string[] {
  return DISCIPLINE_KEYS.filter((key) => Boolean(school[key])).map((key) => DISCIPLINE_LABELS[key as string]);
}
