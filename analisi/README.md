# Analisi log — effetto pala danneggiata

Cartella dedicata alle analisi off-line dei log di volo PX4 per studiare
l'effetto del danneggiamento delle pale sul comportamento dell'esacottero F550.

## Documenti

- **[`panoramica.md`](panoramica.md)** — vista d'insieme: metodologia,
  confronto trasversale fra tutti i livelli di danno (0 / 5 % / 10 %),
  progressione su M1, metriche raccomandate per la relazione.
- [`pala-5pct.md`](pala-5pct.md) — dettaglio Set A (baseline) vs Set B
  (pala 5 % su M1…M6).
- [`pala-10pct.md`](pala-10pct.md) — dettaglio Set A vs Set C (pala 10 %;
  oggi solo C.1, verrà esteso con C.2–C.6).

## Contenuto

```
analisi/
├── README.md            ← questo file
├── panoramica.md        ← entry point, metodologia + confronto trasversale
├── pala-5pct.md         ← Set A vs Set B
├── pala-10pct.md        ← Set A vs Set C (parziale)
├── scripts/
│   ├── analizza_log.py  ← estrae metriche da .ulg → risultati.json
│   └── sintesi.py       ← tabelle comparative → tabelle.txt
└── dati/
    ├── risultati.json   ← statistiche per-volo (intervallo armato)
    └── tabelle.txt      ← tabelle leggibili
```

## Come rigenerare

```bash
python3 analisi/scripts/analizza_log.py > analisi/dati/risultati.json
python3 analisi/scripts/sintesi.py     > analisi/dati/tabelle.txt
```

Richiede `pyulog` e `numpy`. I percorsi sono relativi alla repo, gli script
trovano automaticamente i log in `log/2026-05-27/`.
