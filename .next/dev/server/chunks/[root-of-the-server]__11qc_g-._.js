module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[project]/app/api/comunas/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET,
    "POST",
    ()=>POST
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
;
async function GET() {
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
        data: COMUNAS_DEFAULT
    });
}
async function POST(req) {
    try {
        const body = await req.json();
        const { comunas, terminos } = body;
        if (!comunas || comunas.length === 0) {
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                error: "Sin comunas"
            }, {
                status: 400
            });
        }
        // Llamar al worker para procesar la búsqueda
        const workerUrl = process.env.WORKER_URL || "http://localhost:8001";
        const res = await fetch(`${workerUrl}/poll`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                comunas,
                terminos: terminos || [
                    "comercializadora",
                    "distribuidora",
                    "importadora",
                    "mayorista",
                    "proveedor"
                ],
                modo: "enriched"
            })
        });
        if (!res.ok) {
            const errorText = await res.text();
            console.error("Worker error:", errorText);
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                data: [],
                total: 0
            });
        }
        const result = await res.json();
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            data: result.empresas || [],
            total: result.total || 0
        });
    } catch (e) {
        console.error("Error en POST /api/empresas:", e);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            data: [],
            total: 0
        });
    }
}
const COMUNAS_DEFAULT = [
    {
        id: 1,
        nombre: "Santiago",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 2,
        nombre: "Providencia",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 3,
        nombre: "Las Condes",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 4,
        nombre: "Vitacura",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 5,
        nombre: "Ñuñoa",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 6,
        nombre: "La Florida",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 7,
        nombre: "Maipú",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 8,
        nombre: "Puente Alto",
        region: "Metropolitana de Santiago",
        region_number: "RM"
    },
    {
        id: 9,
        nombre: "Iquique",
        region: "Tarapacá",
        region_number: "I"
    },
    {
        id: 10,
        nombre: "Antofagasta",
        region: "Antofagasta",
        region_number: "II"
    },
    {
        id: 11,
        nombre: "La Serena",
        region: "Coquimbo",
        region_number: "IV"
    },
    {
        id: 12,
        nombre: "Valparaíso",
        region: "Valparaíso",
        region_number: "V"
    },
    {
        id: 13,
        nombre: "Viña del Mar",
        region: "Valparaíso",
        region_number: "V"
    },
    {
        id: 14,
        nombre: "Rancagua",
        region: "O'Higgins",
        region_number: "VI"
    },
    {
        id: 15,
        nombre: "Talca",
        region: "Maule",
        region_number: "VII"
    },
    {
        id: 16,
        nombre: "Concepción",
        region: "Biobío",
        region_number: "VIII"
    },
    {
        id: 17,
        nombre: "Temuco",
        region: "Araucanía",
        region_number: "IX"
    },
    {
        id: 18,
        nombre: "Valdivia",
        region: "Los Ríos",
        region_number: "XIV"
    },
    {
        id: 19,
        nombre: "Puerto Montt",
        region: "Los Lagos",
        region_number: "X"
    },
    {
        id: 20,
        nombre: "Coyhaique",
        region: "Aysén",
        region_number: "XI"
    },
    {
        id: 21,
        nombre: "Punta Arenas",
        region: "Magallanes",
        region_number: "XII"
    }
];
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__11qc_g-._.js.map