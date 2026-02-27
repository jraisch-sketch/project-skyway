import type { School } from '@/lib/types';

export const DISCIPLINE_LABELS: Record<string, string> = {
  road: 'Road',
  mtb: 'MTB',
  cyclocross: 'Cyclocross',
  track: 'Track',
};

const DISCIPLINE_KEYS = Object.keys(DISCIPLINE_LABELS) as Array<keyof School>;

export function getDisciplineLabels(school: School): string[] {
  return DISCIPLINE_KEYS.filter((key) => Boolean(school[key])).map((key) => DISCIPLINE_LABELS[key as string]);
}
