/**
 * Branchen-Rollenvorlagen fuer den Rollen-Verwaltung-Bildschirm.
 *
 * Rein client-seitige Starthilfe - erzeugt beim Uebernehmen ganz normale
 * Rollen ueber den bestehenden POST /roles-Endpoint (api.js: createRole).
 * Keine eigene Backend-Logik noetig: das Custom-Rollen-System (siehe
 * role_suggestion.py) bleibt die einzige Quelle der Wahrheit, Vorlagen sind
 * nur vorausgefuellte Name+Beschreibung-Paare, die management uebernehmen,
 * anpassen oder ignorieren kann.
 */

export const ROLE_TEMPLATES = [
  {
    industry: "Steuerberatung / Kanzlei",
    roles: [
      {
        name: "Mandanten-Buchhaltung",
        description: "Rechnungen, Belege, Kontoauszuege, laufende Mandantenbuchhaltung",
      },
      {
        name: "Lohnbuchhaltung",
        description: "Gehaltsabrechnungen, Sozialversicherung, Lohnsteuer",
      },
      {
        name: "Empfang",
        description: "Terminkoordination, allgemeine Mandantenanfragen, Postein- und -ausgang",
      },
    ],
  },
  {
    industry: "Marketing- / Design-Agentur",
    roles: [
      {
        name: "Kundenbetreuung",
        description: "Kundenkommunikation, Briefings, Projektabstimmung, Account-Management",
      },
      {
        name: "Kreation",
        description: "Design, Konzeption, Content-Erstellung, Kreativbriefings",
      },
      {
        name: "Buchhaltung",
        description: "Rechnungen, Angebote, Honorarabrechnung",
      },
    ],
  },
  {
    industry: "Beratung / Consulting",
    roles: [
      {
        name: "Projektleitung",
        description: "Projektplanung, Statusberichte, Kundensteuerung",
      },
      {
        name: "Research",
        description: "Recherche, Analysen, Marktstudien, interne Auswertungen",
      },
      {
        name: "Vertrieb",
        description: "Akquise, Angebote, Vertragsverhandlungen",
      },
    ],
  },
  {
    industry: "Immobilienmarketing",
    roles: [
      {
        name: "Expose-Erstellung",
        description: "Objektbeschreibungen, Texte, Exposes",
      },
      {
        name: "Medien",
        description: "Fotografie, Grundrisse, Videos, Bildbearbeitung",
      },
      {
        name: "Terminkoordination",
        description: "Besichtigungstermine, Kundenkommunikation, Kalenderpflege",
      },
    ],
  },
];
