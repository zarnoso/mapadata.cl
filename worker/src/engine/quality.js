export function scoreLead(lead) {
  let score = 35;
  if (lead.name) score += 10;
  if (lead.address) score += 15;
  if (lead.phone) score += 15;
  if (lead.website) score += 15;
  if (lead.google_place_id) score += 10;
  if (lead.category) score += 5;
  if (lead.rating) score += 5;
  return Math.min(score, 100);
}
