import { mapadata } from '../supabaseAdmin.js';

export async function hasActiveEntitlement(userId) {
  if (!userId) return false;

  const { data, error } = await mapadata()
    .from('entitlements')
    .select('*')
    .eq('user_id', userId)
    .eq('status', 'active')
    .limit(1);

  if (error) throw error;
  return Boolean(data && data.length);
}
