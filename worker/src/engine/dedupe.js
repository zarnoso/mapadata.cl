import { normalizeText } from '../utils/text.js';

export class DedupeSet {
  constructor() {
    this.keys = new Set();
  }

  keyForLead(lead) {
    if (lead.google_place_id) return `place:${lead.google_place_id}`;
    if (lead.website) return `web:${normalizeText(lead.website)}`;
    if (lead.phone) return `phone:${normalizeText(lead.phone)}`;
    return `name-address:${normalizeText(lead.name)}:${normalizeText(lead.address)}`;
  }

  has(lead) {
    return this.keys.has(this.keyForLead(lead));
  }

  add(lead) {
    this.keys.add(this.keyForLead(lead));
  }
}
