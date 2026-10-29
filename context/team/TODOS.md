# Receptionist FRONTEND
- Vis pris oversigt, pr night, total, før create booking
- Ved siden af Total Price skal der også være et felt til at kunne sætte en fast pr night pris, (kun 1 felt kan være udfyldt)
- Fremhæv “Edit mode”, lav helt om på UI så der skiller sig langt fra normal booking opret booking udseende.

# REST API (Corrected 2026-10-29)
- Fjern alle præ-aggregerede `/api/v1/kpis/*` endpoints og alle query-parametre (`?year=`, `?season=`, `?room_type=`, `?country=`, `?category=`).
- Eksponér rå data via basale `GET` endpoints uden query-parametre (`/api/v1/bookings`, `/api/v1/room-types`, `/api/v1/reviews`, `/api/v1/bar/drink-sales`), så teamet forbinder Tableau direkte til de rå tabeller og bygger dashboards og KPI'er manuelt i Tableau.
