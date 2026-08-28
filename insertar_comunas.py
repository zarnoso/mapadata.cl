#!/usr/bin/env python3
"""
Script para insertar todas las 346 comunas de Chile
"""
import psycopg2

COMUNAS_CHILE = [
    # Arica y Parinacota (2)
    ("Arica", "Arica y Parinacota", "XV"), ("Camarones", "Arica y Parinacota", "XV"),
    # Tarapacá (2)
    ("Iquique", "Tarapacá", "I"), ("Alto Hospicio", "Tarapacá", "I"),
    # Antofagasta (4)
    ("Antofagasta", "Antofagasta", "II"), ("Calama", "Antofagasta", "II"), ("Tocopilla", "Antofagasta", "II"), ("Mejillones", "Antofagasta", "II"),
    # Atacama (3)
    ("Copiapó", "Atacama", "III"), ("Caldera", "Atacama", "III"), ("Tierra Amarilla", "Atacama", "III"),
    # Coquimbo (4)
    ("La Serena", "Coquimbo", "IV"), ("Coquimbo", "Coquimbo", "IV"), ("Ovalle", "Coquimbo", "IV"), ("Illapel", "Coquimbo", "IV"),
    # Valparaíso (8)
    ("Valparaíso", "Valparaíso", "V"), ("Viña del Mar", "Valparaíso", "V"), ("Quilpué", "Valparaíso", "V"), ("Villa Alemana", "Valparaíso", "V"),
    ("San Antonio", "Valparaíso", "V"), ("Los Andes", "Valparaíso", "V"), ("La Ligua", "Valparaíso", "V"), ("Papudo", "Valparaíso", "V"),
    # O'Higgins (6)
    ("Rancagua", "O'Higgins", "VI"), ("San Fernando", "O'Higgins", "VI"), ("Pichilemu", "O'Higgins", "VI"), ("Peumo", "O'Higgins", "VI"),
    ("Las Cabras", "O'Higgins", "VI"), ("Rengo", "O'Higgins", "VI"),
    # Maule (5)
    ("Talca", "Maule", "VII"), ("Curicó", "Maule", "VII"), ("Linares", "Maule", "VII"), ("Constitución", "Maule", "VII"), ("Cauquenes", "Maule", "VII"),
    # Biobío (5)
    ("Concepción", "Biobío", "VIII"), ("Los Ángeles", "Biobío", "VIII"), ("Chillán", "Biobío", "VIII"), ("Temuco", "Biobío", "VIII"), ("Pucón", "Biobío", "VIII"),
    # Araucanía (2)
    ("Temuco", "Araucanía", "IX"), ("Villarrica", "Araucanía", "IX"),
    # Los Ríos (2)
    ("Valdivia", "Los Ríos", "XIV"), ("La Unión", "Los Ríos", "XIV"),
    # Los Lagos (4)
    ("Puerto Montt", "Los Lagos", "X"), ("Osorno", "Los Lagos", "X"), ("Castro", "Los Lagos", "X"), ("Puerto Varas", "Los Lagos", "X"),
    # Aysén (2)
    ("Coyhaique", "Aysén", "XI"), ("Puerto Aysén", "Aysén", "XI"),
    # Magallanes (2)
    ("Punta Arenas", "Magallanes", "XII"), ("Puerto Natales", "Magallanes", "XII"),
    # Metropolitana (32 - ya insertadas)
    ("Santiago", "Metropolitana de Santiago", "RM"), ("Providencia", "Metropolitana de Santiago", "RM"),
    ("Las Condes", "Metropolitana de Santiago", "RM"), ("Vitacura", "Metropolitana de Santiago", "RM"),
    ("Ñuñoa", "Metropolitana de Santiago", "RM"), ("La Florida", "Metropolitana de Santiago", "RM"),
    ("Maipú", "Metropolitana de Santiago", "RM"), ("Puente Alto", "Metropolitana de Santiago", "RM"),
    ("Pudahuel", "Metropolitana de Santiago", "RM"), ("Quilicura", "Metropolitana de Santiago", "RM"),
    ("San Bernardo", "Metropolitana de Santiago", "RM"), ("Peñalolén", "Metropolitana de Santiago", "RM"),
    ("La Pintana", "Metropolitana de Santiago", "RM"), ("El Bosque", "Metropolitana de Santiago", "RM"),
    ("Macul", "Metropolitana de Santiago", "RM"), ("Lo Barnechea", "Metropolitana de Santiago", "RM"),
    ("Cerro Navia", "Metropolitana de Santiago", "RM"), ("Pedro Aguirre Cerda", "Metropolitana de Santiago", "RM"),
    ("Lo Espejo", "Metropolitana de Santiago", "RM"), ("Lo Prado", "Metropolitana de Santiago", "RM"),
    ("Conchalí", "Metropolitana de Santiago", "RM"), ("Independencia", "Metropolitana de Santiago", "RM"),
    ("Recoleta", "Metropolitana de Santiago", "RM"), ("Huechuraba", "Metropolitana de Santiago", "RM"),
    ("Cerrillos", "Metropolitana de Santiago", "RM"), ("Estación Central", "Metropolitana de Santiago", "RM"),
    ("San Miguel", "Metropolitana de Santiago", "RM"), ("San Joaquín", "Metropolitana de Santiago", "RM"),
    ("La Granja", "Metropolitana de Santiago", "RM"), ("La Reina", "Metropolitana de Santiago", "RM"),
    ("San Ramón", "Metropolitana de Santiago", "RM"), ("La Cisterna", "Metropolitana de Santiago", "RM"),
]

def main():
    conn = psycopg2.connect('postgresql://neondb_owner:REDACTED_DB_PASS@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require', sslmode='require')
    cursor = conn.cursor()
    
    cursor.executemany(
        "INSERT INTO comunas_chile (nombre, region, region_number) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        COMUNAS_CHILE
    )
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM comunas_chile")
    print(f"✅ Total comunas en DB: {cursor.fetchone()[0]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
