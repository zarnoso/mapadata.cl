"""Catálogo de comunas de Chile — 346 comunas, 16 regiones. Verificado por conteo."""

COMUNAS_POR_REGION = {
    "Arica y Parinacota": ["Arica", "Camarones", "General Lagos", "Putre"],
    "Tarapacá": ["Alto Hospicio", "Camiña", "Colchane", "Huara", "Iquique", "Pica", "Pozo Almonte"],
    "Antofagasta": ["Antofagasta", "Calama", "María Elena", "Mejillones", "Ollagüe", "San Pedro de Atacama", "Sierra Gorda", "Taltal", "Tocopilla"],
    "Atacama": ["Alto del Carmen", "Caldera", "Chañaral", "Copiapó", "Diego de Almagro", "Freirina", "Huasco", "Tierra Amarilla", "Vallenar"],
    "Coquimbo": ["Andacollo", "Canela", "Combarbalá", "Coquimbo", "Illapel", "La Higuera", "La Serena", "Los Vilos", "Monte Patria", "Ovalle", "Paihuano", "Punitaqui", "Río Hurtado", "Salamanca", "Vicuña"],
    "Valparaíso": ["Algarrobo", "Cabildo", "Calera", "Calle Larga", "Cartagena", "Casablanca", "Catemu", "Concón", "El Quisco", "El Tabo", "Hijuelas", "Isla de Pascua", "Juan Fernández", "La Cruz", "La Ligua", "Limache", "Llaillay", "Los Andes", "Nogales", "Olmué", "Panquehue", "Papudo", "Petorca", "Puchuncaví", "Putaendo", "Quillota", "Quilpué", "Quintero", "Rinconada", "San Antonio", "San Esteban", "San Felipe", "Santa María", "Santo Domingo", "Valparaíso", "Villa Alemana", "Viña del Mar", "Zapallar"],
    "O'Higgins": ["Chimbarongo", "Chépica", "Codegua", "Coinco", "Coltauco", "Doñihue", "Graneros", "La Estrella", "Las Cabras", "Litueche", "Lolol", "Machalí", "Malloa", "Marchigüe", "Nancagua", "Navidad", "Olivar", "Palmilla", "Paredones", "Peralillo", "Peumo", "Pichidegua", "Pichilemu", "Placilla", "Pumanque", "Quinta de Tilcoco", "Rancagua", "Rengo", "Requínoa", "San Fernando", "San Francisco de Mostazal", "San Vicente de Tagua Tagua", "Santa Cruz"],
    "Maule": ["Cauquenes", "Chanco", "Colbún", "Constitución", "Curepto", "Curicó", "Empedrado", "Hualañé", "Licantén", "Linares", "Longaví", "Maule", "Molina", "Parral", "Pelarco", "Pelluhue", "Pencahue", "Rauco", "Retiro", "Romeral", "Río Claro", "Sagrada Familia", "San Clemente", "San Javier de Loncomilla", "San Rafael", "Talca", "Teno", "Vichuquén", "Villa Alegre", "Yerbas Buenas"],
    "Ñuble": ["Bulnes", "Chillán Viejo", "Chillán", "Cobquecura", "Coelemu", "Coihueco", "El Carmen", "Ninhue", "Ñiquén", "Pemuco", "Pinto", "Portezuelo", "Quillón", "Quirihue", "Ránquil", "San Carlos", "San Fabián", "San Ignacio", "San Nicolás", "Treguaco", "Yungay"],
    "Biobío": ["Alto Biobío", "Antuco", "Arauco", "Cabrero", "Cañete", "Chiguayante", "Concepción", "Contulmo", "Coronel", "Curanilahue", "Florida", "Hualpén", "Hualqui", "Laja", "Lebu", "Los Álamos", "Los Ángeles", "Lota", "Mulchén", "Nacimiento", "Negrete", "Penco", "Quilaco", "Quilleco", "San Pedro de la Paz", "San Rosendo", "Santa Bárbara", "Santa Juana", "Talcahuano", "Tirúa", "Tomé", "Tucapel", "Yumbel"],
    "Araucanía": ["Angol", "Carahue", "Cholchol", "Collipulli", "Cunco", "Curacautín", "Curarrehue", "Ercilla", "Freire", "Galvarino", "Gorbea", "Lautaro", "Loncoche", "Lonquimay", "Los Sauces", "Lumaco", "Melipeuco", "Nueva Imperial", "Padre las Casas", "Perquenco", "Pitrufquén", "Pucón", "Purén", "Renaico", "Saavedra", "Temuco", "Teodoro Schmidt", "Toltén", "Traiguén", "Victoria", "Vilcún", "Villarrica"],
    "Los Ríos": ["Corral", "Futrono", "La Unión", "Lago Ranco", "Lanco", "Los Lagos", "Mariquina", "Máfil", "Paillaco", "Panguipulli", "Río Bueno", "Valdivia"],
    "Los Lagos": ["Ancud", "Calbuco", "Castro", "Chaitén", "Chonchi", "Cochamó", "Curaco de Vélez", "Dalcahue", "Fresia", "Frutillar", "Futaleufú", "Hualaihué", "Llanquihue", "Los Muermos", "Maullín", "Osorno", "Palena", "Puerto Montt", "Puerto Octay", "Puerto Varas", "Puqueldón", "Purranque", "Puyehue", "Queilén", "Quellón", "Quemchi", "Quinchao", "Río Negro", "San Juan de la Costa", "San Pablo"],
    "Aysén": ["Aisén", "Chile Chico", "Cisnes", "Cochrane", "Coyhaique", "Guaitecas", "Lago Verde", "O'Higgins", "Río Ibáñez", "Tortel"],
    "Magallanes": ["Antártica", "Cabo de Hornos", "Laguna Blanca", "Natales", "Porvenir", "Primavera", "Punta Arenas", "Río Verde", "San Gregorio", "Timaukel", "Torres del Paine"],
    "Metropolitana de Santiago": [
        "Alhué", "Buin", "Calera de Tango", "Cerrillos", "Cerro Navia", "Colina", "Conchalí",
        "Curacaví", "El Bosque", "El Monte", "Estación Central", "Huechuraba", "Independencia",
        "Isla de Maipo", "La Cisterna", "La Florida", "La Granja", "La Pintana", "La Reina",
        "Lampa", "Las Condes", "Lo Barnechea", "Lo Espejo", "Lo Prado", "Macul", "Maipú",
        "María Pinto", "Melipilla", "Ñuñoa", "Padre Hurtado", "Paine", "Pedro Aguirre Cerda",
        "Peñaflor", "Peñalolén", "Pirque", "Providencia", "Pudahuel", "Puente Alto",
        "Quilicura", "Quinta Normal", "Recoleta", "Renca", "San Bernardo", "San Joaquín",
        "San José de Maipo", "San Miguel", "San Pedro", "San Ramón", "Santiago", "Talagante",
        "Tiltil", "Vitacura"
    ],
}

# Verificación estricta de conteo (asserts)
COMUNAS_RM = COMUNAS_POR_REGION["Metropolitana de Santiago"]
COMUNAS_CHILE_346 = [c for lista in COMUNAS_POR_REGION.values() for c in lista]

assert len(COMUNAS_RM) == 52, f"RM esperado 52, obtenido {len(COMUNAS_RM)}"
assert len(COMUNAS_CHILE_346) == 346, f"Chile esperado 346, obtenido {len(COMUNAS_CHILE_346)}"
assert len(set(COMUNAS_CHILE_346)) == 346, "Hay comunas duplicadas"


def resolver_comunas(param_comunas):
    """Resuelve el valor de scraping_jobs.comunas a una lista final de zonas.

    Acepta:
    - None o vacío → retorna COMUNAS_RM (default)
    - "TODO_CHILE" | "CHILE" | "ALL" → retorna las 346 comunas
    - "REGION_METROPOLITANA" | "RM" → retorna las 52 comunas de RM
    - Nombre de región (ej. "Valparaíso") → retorna comunas de esa región
    - CSV string: "Santiago, Providencia, Vitacura"
    - Postgres ARRAY: ['Santiago', 'Providencia']
    - Un string con una sola comuna: "Santiago"
    """
    if not param_comunas:
        return COMUNAS_RM

    if isinstance(param_comunas, str):
        val = param_comunas.strip().upper()
        if val in ("TODO_CHILE", "CHILE", "ALL"):
            return COMUNAS_CHILE_346
        if val in ("REGION_METROPOLITANA", "RM"):
            return COMUNAS_RM
        # Nombre de región
        for region, comunas in COMUNAS_POR_REGION.items():
            if region.upper() == val:
                return comunas
        # CSV string
        if "," in param_comunas:
            comunas = [c.strip() for c in param_comunas.split(",") if c.strip()]
            return comunas if comunas else COMUNAS_RM
        # Una sola comuna
        return [param_comunas.strip()]

    if isinstance(param_comunas, list):
        limpias = [str(c).strip() for c in param_comunas if str(c).strip()]
        if not limpias:
            return COMUNAS_RM
        primero = limpias[0].upper()
        if primero == "TODO_CHILE":
            return COMUNAS_CHILE_346
        if primero in ("REGION_METROPOLITANA", "RM"):
            return COMUNAS_RM
        return limpias

    return COMUNAS_RM
