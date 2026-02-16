export const CONFERENCE_COLORS: Record<string, string> = {
  Atlantic: '#E15759',
  Eastern: '#59A14F',
  'Inter Mountain': '#F28E2B',
  Midwest: '#4E79A7',
  'North Central': '#B07AA1',
  Northwest: '#76B7B2',
  'Rocky Mountain': '#9C755F',
  'South Central': '#EDC948',
  Southeast: '#FF9DA7',
  Southwest: '#AF7AA1',
};

export const DEFAULT_CONFERENCE_COLOR = '#7A8A99';

export function colorForConference(conference: string): string {
  return CONFERENCE_COLORS[conference] || DEFAULT_CONFERENCE_COLOR;
}
