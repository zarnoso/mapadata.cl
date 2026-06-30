export function buildFerreteriaValparaisoPlan({ limit = 20 } = {}) {
  return {
    industry: 'ferreteria',
    commune: 'Valparaíso',
    region: 'Valparaíso',
    targetLimit: limit,
    queries: [
      'ferretería Valparaíso Chile',
      'ferreterias Valparaiso Chile',
      'ferretería en Valparaíso',
      'tienda de herramientas Valparaíso Chile',
      'herramientas Valparaíso Chile',
      'materiales de construcción Valparaíso Chile',
      'venta materiales de construcción Valparaíso Chile',
      'pinturas ferretería Valparaíso Chile',
      'pernos Valparaíso Chile',
      'quincallería Valparaíso Chile',
      'gasfitería ferretería Valparaíso Chile',
      'electricidad ferretería Valparaíso Chile',
      'ferretería Playa Ancha Valparaíso Chile',
      'ferretería Cerro Alegre Valparaíso Chile',
      'ferretería Cerro Barón Valparaíso Chile',
      'ferretería Cerro Placeres Valparaíso Chile',
      'ferretería Avenida Argentina Valparaíso Chile',
      'ferretería Avenida Pedro Montt Valparaíso Chile',
      'ferretería Barrio Puerto Valparaíso Chile',
      'ferretería El Almendral Valparaíso Chile',
      'ferretería Placilla Valparaíso Chile',
      'ferretería Curauma Valparaíso Chile',
      'ferretería Rodelillo Valparaíso Chile',
      'ferretería Laguna Verde Valparaíso Chile'
    ]
  };
}

export function inferRubroFromQuery(query = '') {
  const q = query.toLowerCase();
  if (q.includes('herramient')) return 'Herramientas';
  if (q.includes('materiales')) return 'Materiales de construcción';
  if (q.includes('pintura')) return 'Pinturas';
  if (q.includes('perno')) return 'Pernos';
  if (q.includes('quincaller')) return 'Quincallería';
  if (q.includes('gasfiter')) return 'Gasfitería';
  if (q.includes('electric')) return 'Electricidad';
  return 'Ferretería';
}
