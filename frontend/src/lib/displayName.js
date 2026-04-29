/**
 * Render a profile's display name regardless of whether the backend returned
 * the pre-match shape (first_name + last_initial) or the post-match shape
 * (first_name + last_name). Both work transparently.
 */
export function formatName(profile) {
  if (!profile) return '';
  const last = profile.last_name || profile.last_initial || '';
  return [profile.first_name, last].filter(Boolean).join(' ');
}
