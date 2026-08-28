"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, Download, MapPin, Menu, Search, ShieldCheck, Star, X } from "lucide-react";

type Comuna = { id: number; nombre: string; region: string; region_number: string };
type PricingPlan = {
  id: string;
  name: string;
  priceFormatted: string;
  empresas: number;
  features: string[];
  popular?: boolean;
  mercadoPagoUrl: string;
};

const regionsChile = [
  { name: "Arica y Parinacota", comunas: ["Arica", "Camarones", "General Lagos", "Putre"] },
  { name: "Tarapacá", comunas: ["Alto Hospicio", "Camiña", "Colchane", "Huara", "Iquique", "Pica", "Pozo Almonte"] },
  { name: "Antofagasta", comunas: ["Antofagasta", "Calama", "María Elena", "Mejillones", "San Pedro de Atacama", "Tocopilla"] },
  { name: "Valparaíso", comunas: ["Valparaíso", "Viña del Mar", "Quilpué", "Villa Alemana", "San Antonio", "Quillota"] },
  { name: "Metropolitana", comunas: ["Santiago", "Providencia", "Las Condes", "Ñuñoa", "Maipú", "Puente Alto", "La Florida"] },
  { name: "Biobío", comunas: ["Concepción", "Talcahuano", "Los Ángeles", "Coronel", "San Pedro de la Paz"] },
  { name: "Araucanía", comunas: ["Temuco", "Villarrica", "Padre Las Casas", "Angol"] },
  { name: "Los Lagos", comunas: ["Puerto Montt", "Puerto Varas", "Osorno", "Castro"] },
];

const industries = [
  "Construcción y Ferreterías",
  "Clínicas y Centros Médicos",
  "Retail y Minimarkets",
  "Restaurantes y Cafeterías",
  "Empresas IT y Software",
  "Inmobiliarias",
  "Distribuidoras",
  "Transporte y Logística",
  "Educación y Capacitación",
  "Servicios Financieros",
];

const pricingPlans: PricingPlan[] = [
  { id: "basico", name: "Básico", priceFormatted: "$4.990", empresas: 500, features: ["Descarga en CSV", "Filtros por región", "Soporte por email"], mercadoPagoUrl: "https://mpago.la/1ngFLgK" },
  { id: "starter", name: "Starter", priceFormatted: "$14.990", empresas: 1000, features: ["Descarga en CSV", "Filtros básicos", "Soporte por email"], mercadoPagoUrl: "https://mpago.la/1rpeu28" },
  { id: "business", name: "Business", priceFormatted: "$39.990", empresas: 3000, features: ["Todo de Starter", "Limpieza de duplicados", "Emails y redes sociales", "Soporte prioritario"], popular: true, mercadoPagoUrl: "https://mpago.la/2iqtw4s" },
  { id: "master", name: "Master", priceFormatted: "$64.990", empresas: 5000, features: ["Todo de Business", "CSV y Excel", "Actualización recurrente", "Soporte VIP"], mercadoPagoUrl: "https://mpago.la/19bCNhS" },
];

const faqs = [
  { q: "¿Es legal comprar estas bases de datos?", a: "Sí. La información es pública y se trabaja como OSINT, con foco en empresas y contactos publicados voluntariamente." },
  { q: "¿En qué formato se entrega?", a: "En CSV. Los planes más avanzados también pueden incluir Excel." },
  { q: "¿Cómo recibo el archivo?", a: "Después del pago se entrega el enlace o se dispara el flujo de descarga según el backend activo." },
  { q: "¿Puedo elegir comunas y rubros?", a: "Sí, el explorador permite filtrar por región, comuna e industria." },
];

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");
const apiUrl = (path: string) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path);

function Header() {
  const [open, setOpen] = useState(false);
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <a href="#" className="flex items-center gap-2 font-bold">
          <MapPin className="h-5 w-5 text-cyan-300" />
          <span>Mapadata<span className="text-cyan-300">.cl</span></span>
        </a>
        <nav className="hidden items-center gap-8 md:flex text-sm text-slate-300">
          <a href="#explorador">Explorador</a>
          <a href="#soluciones">Soluciones</a>
          <a href="#precios">Precios</a>
          <a href="#faq">FAQ</a>
        </nav>
        <div className="hidden items-center gap-3 md:flex">
          <a href="#precios" className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-950">Comprar ahora</a>
        </div>
        <button className="md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Abrir menú">
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open ? (
        <div className="border-t border-white/10 bg-slate-950 px-4 py-4 md:hidden text-sm text-slate-300">
          <div className="flex flex-col gap-3">
            <a href="#explorador" onClick={() => setOpen(false)}>Explorador</a>
            <a href="#soluciones" onClick={() => setOpen(false)}>Soluciones</a>
            <a href="#precios" onClick={() => setOpen(false)}>Precios</a>
            <a href="#faq" onClick={() => setOpen(false)}>FAQ</a>
          </div>
        </div>
      ) : null}
    </header>
  );
}

function Hero() {
  const [selectedRegion, setSelectedRegion] = useState("");
  const [selectedComuna, setSelectedComuna] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const estimated = useMemo(() => {
    let base = 45000;
    if (selectedRegion) base = Math.floor(base * 0.15);
    if (selectedComuna) base = Math.floor(base * 0.3);
    if (selectedIndustry) base = Math.floor(base * 0.2);
    return Math.max(120, base);
  }, [selectedRegion, selectedComuna, selectedIndustry]);

  return (
    <section className="relative overflow-hidden pt-28 pb-20">
      <div className="absolute inset-0 opacity-40">
        <div className="absolute left-8 top-20 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute right-10 top-44 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
      </div>
      <div className="relative mx-auto max-w-7xl px-4">
        <div className="text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-1.5 text-sm text-cyan-200">
            <span className="h-2 w-2 rounded-full bg-cyan-300" />
            Base de datos de Chile actualizada hoy
          </div>
          <h1 className="mx-auto max-w-4xl text-4xl font-extrabold leading-tight md:text-6xl">
            Convierte Google Maps en tu <span className="text-cyan-300">Motor de Ventas B2B</span>
          </h1>
          <p className="mx-auto mt-6 max-w-3xl text-lg text-slate-300">
            Descarga listas de empresas verificadas por industria y región. Este frontend ya está preparado para tu backend real y para publicarse en Cloudflare Pages.
          </p>
          <p className="mt-4 text-cyan-300 font-semibold">Más de 45,000 empresas actualizadas</p>
        </div>

        <div id="explorador" className="mx-auto mt-10 max-w-5xl rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
          <ExplorerCard />
        </div>

        <div className="mx-auto mt-6 max-w-5xl rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-center text-sm text-slate-300">
          Explora datos con filtros por región, comuna e industria. Resultado estimado: <span className="font-semibold text-white">{estimated.toLocaleString("es-CL")}</span>
        </div>
      </div>
    </section>
  );

  function ExplorerCard() {
    const [region, setRegion] = useState("");
    const [comuna, setComuna] = useState("");
    const [industry, setIndustry] = useState("");
    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState<Comuna[]>([]);
    const [regions, setRegions] = useState<string[]>([]);
    const [job, setJob] = useState<any>(null);
    const [clientId, setClientId] = useState("1");

    useEffect(() => {
      fetch(apiUrl("/api/comunas"))
        .then((r) => r.json())
        .then((data: Comuna[]) => {
          setItems(data);
          setRegions([...new Set(data.map((c) => c.region))] as string[]);
        })
        .catch(() => void 0);
    }, []);

    const comunasDisponibles = region ? items.filter((c) => c.region === region).map((c) => c.nombre) : [];

    const onSearch = async () => {
      setLoading(true);
      setJob(null);
      try {
        const res = await fetch(apiUrl("/api/jobs"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ comunas: comuna ? [comuna] : [], terminos: industry ? [industry] : undefined, cliente_id: Number(clientId) || 1, modo: "enriched" }),
        });
        const data = await res.json();
        setJob(data);
      } finally {
        setLoading(false);
      }
    };

    return (
      <>
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Región">
            <select value={region} onChange={(e) => { setRegion(e.target.value); setComuna(""); }} className="input">
              <option value="">Todo Chile</option>
              {regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </Field>
          <Field label="Comuna">
            <select value={comuna} onChange={(e) => setComuna(e.target.value)} disabled={!region} className="input">
              <option value="">Todas las comunas</option>
              {comunasDisponibles.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Industria / Rubro">
            <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="input">
              <option value="">Todos los rubros</option>
              {industries.map((i) => <option key={i} value={i}>{i}</option>)}
            </select>
          </Field>
        </div>
        <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center">
          <button onClick={onSearch} className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-6 py-3 font-semibold text-slate-950 hover:bg-slate-200 transition">
            <Search className="h-4 w-4" />
            {loading ? "Creando job..." : "Buscar leads"}
          </button>
          <div className="text-sm text-slate-300">
            <span className="mr-2 font-semibold text-cyan-300">{estimated.toLocaleString("es-CL")}</span> empresas encontradas
          </div>
        </div>
        {job ? <div className="mt-4 rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-4 text-sm text-cyan-100">Job #{job.id} creado con estado <strong>{job.status}</strong></div> : null}
      </>
    );
  }
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="space-y-2 text-left text-sm">
      <span className="block uppercase tracking-[0.2em] text-slate-400">{label}</span>
      {children}
    </label>
  );
}

function ExplorerPreview() {
  const rows = [
    ["Constructora Eje Sur SpA", "Construcción", "+56 9 8765 4321", "ejesur.cl", "4.8"],
    ["Ingeniería y Proyectos Andes", "Ferretería Industrial", "+56 2 2345 6789", "proyectosandes.cl", "4.5"],
    ["Maquinarias Biobío Ltda.", "Arriendo Equipos", "+56 41 222 3344", "No disponible", "4.2"],
  ];
  return (
    <section className="py-20" id="soluciones">
      <div className="mx-auto max-w-7xl px-4">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold md:text-4xl">Explorador de datos en vivo</h2>
          <p className="mt-3 text-slate-300">Previsualiza la calidad de la información antes de descargar tu CSV.</p>
        </div>
        <div className="mx-auto mt-10 max-w-5xl overflow-hidden rounded-3xl border border-white/10 bg-white/5">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <div className="flex items-center gap-2 text-cyan-300"><Star className="h-4 w-4" /> Mostrando resultados de prueba</div>
            <button className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-sm">
              <Download className="h-4 w-4" /> Descargar CSV
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-white/5 text-slate-400">
                <tr>
                  <th className="px-4 py-3">Nombre</th>
                  <th className="px-4 py-3">Categoría</th>
                  <th className="px-4 py-3">Teléfono</th>
                  <th className="px-4 py-3">Sitio web</th>
                  <th className="px-4 py-3">Rating</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row[0]} className="border-t border-white/5">
                    {row.map((cell) => <td key={cell} className="px-4 py-3 text-slate-200">{cell}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}

function Solutions() {
  const items = ["Construcción", "Salud", "Retail", "Restaurantes", "IT", "Inmobiliarias"];
  return (
    <section className="py-12">
      <div className="mx-auto max-w-7xl px-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
          {items.map((item) => (
            <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center text-sm text-slate-200">{item}</div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Guarantee() {
  return (
    <section className="py-16">
      <div className="mx-auto max-w-3xl px-4">
        <div className="rounded-3xl border border-cyan-300/20 bg-cyan-300/10 p-8 text-center">
          <ShieldCheck className="mx-auto mb-4 h-12 w-12 text-cyan-300" />
          <h3 className="text-2xl font-bold">Garantía de Rebote</h3>
          <p className="mt-3 text-slate-200">Si más del 5% de los correos rebotan, repongo el doble de datos sin costo adicional.</p>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  const [selected, setSelected] = useState<PricingPlan | null>(null);
  return (
    <section className="py-20" id="precios">
      <div className="mx-auto max-w-7xl px-4">
        <div className="text-center">
          <h2 className="text-3xl font-bold md:text-4xl">Paga solo por la data que necesitas</h2>
          <p className="mt-3 text-slate-300">1 empresa = toda su información pública disponible.</p>
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-4">
          {pricingPlans.map((plan) => (
            <article key={plan.id} className={`rounded-3xl border p-6 ${plan.popular ? "border-cyan-300/50 bg-cyan-300/10" : "border-white/10 bg-white/5"}`}>
              {plan.popular ? <div className="mb-4 inline-flex rounded-full bg-cyan-300 px-3 py-1 text-xs font-semibold text-slate-950">Más popular</div> : null}
              <h3 className="text-xl font-bold">{plan.name}</h3>
              <div className="mt-3 text-3xl font-extrabold">{plan.priceFormatted} <span className="text-sm font-normal text-slate-400">CLP</span></div>
              <p className="mt-2 text-cyan-300">{plan.empresas.toLocaleString("es-CL")} empresas</p>
              <ul className="mt-5 space-y-2 text-sm text-slate-300">
                {plan.features.map((f) => <li key={f} className="flex gap-2"><Check className="mt-0.5 h-4 w-4 text-cyan-300" />{f}</li>)}
              </ul>
              <button onClick={() => setSelected(plan)} className={`mt-6 w-full rounded-xl px-4 py-3 font-semibold ${plan.popular ? "bg-white text-slate-950" : "bg-white/10 text-white"}`}>
                Comprar pack
              </button>
            </article>
          ))}
        </div>
      </div>
      {selected ? <Checkout plan={selected} onClose={() => setSelected(null)} /> : null}
    </section>
  );
}

function Checkout({ plan, onClose }: { plan: PricingPlan; onClose: () => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [rut, setRut] = useState("");
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur">
      <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-slate-950 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold">Resumen de compra</h3>
          <button onClick={onClose}><X className="h-5 w-5" /></button>
        </div>
        <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex justify-between"><span>Plan {plan.name}</span><span>{plan.priceFormatted}</span></div>
          <p className="mt-1 text-sm text-slate-400">{plan.empresas.toLocaleString("es-CL")} empresas</p>
        </div>
        <div className="mt-4 grid gap-3">
          <input className="input" placeholder="Nombre completo" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="input" placeholder="RUT" value={rut} onChange={(e) => setRut(e.target.value)} />
          <input className="input" placeholder="correo@empresa.cl" value={email} onChange={(e) => setEmail(e.target.value)} />
          <a href={plan.mercadoPagoUrl} target="_blank" rel="noreferrer" className="rounded-xl bg-white px-4 py-3 text-center font-semibold text-slate-950">Pagar con MercadoPago</a>
        </div>
      </div>
    </div>
  );
}

function FAQ() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section id="faq" className="py-20">
      <div className="mx-auto max-w-3xl px-4">
        <div className="text-center">
          <h2 className="text-3xl font-bold md:text-4xl">Preguntas frecuentes</h2>
          <p className="mt-3 text-slate-300">Todo lo que necesitas saber sobre el servicio.</p>
        </div>
        <div className="mt-10 space-y-3">
          {faqs.map((faq, i) => (
            <button key={faq.q} onClick={() => setOpen(open === i ? null : i)} className="w-full rounded-2xl border border-white/10 bg-white/5 p-5 text-left">
              <div className="flex items-center justify-between gap-4">
                <span className="font-medium">{faq.q}</span>
                <ChevronDown className={`h-5 w-5 transition-transform ${open === i ? "rotate-180" : ""}`} />
              </div>
              {open === i ? <p className="mt-3 text-sm text-slate-300">{faq.a}</p> : null}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/10 py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 md:flex-row">
        <div className="flex items-center gap-2 font-bold">
          <MapPin className="h-5 w-5 text-cyan-300" />
          Mapadata<span className="text-cyan-300">.cl</span>
        </div>
        <p className="text-xs text-slate-400">Frontend replicado desde el original de Lovable, listo para tu backend.</p>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.14),_transparent_30%),linear-gradient(180deg,#0f172a_0%,#070b14_40%,#05070d_100%)] text-white">
      <Header />
      <Hero />
      <ExplorerPreview />
      <Solutions />
      <Guarantee />
      <Pricing />
      <FAQ />
      <Footer />
    </main>
  );
}
