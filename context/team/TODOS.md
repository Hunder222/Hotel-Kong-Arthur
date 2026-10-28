# Receptionist FRONTEND
- Vis pris oversigt, pr night, total, før create booking
- Ved siden af Total Price skal der også være et felt til at kunne sætte en fast pr night pris, (kun 1 felt kan være udfyldt)
- Fremhæv “Edit mode”, lav helt om på UI så der skiller sig langt fra normal booking opret booking udseende.

# REST API
- Afklar kpis/bar/summary og kpis/hotel/summary, skal kunne se total, men også en for år, /summary (total), /summary/2026(2026)
- Afklar /api/v1/kpis/hotel/by-room-type, hvorfor står der “2026”, vi skal se en total, tilføj en /api/v1/kpis/hotel/by-room-type/2026 for at få års oversigt.
    - Samme med /api/v1/kpis/hotel/by-season,
    - Samme med /api/v1/kpis/hotel/by-room-type-and-season
    - Samme med /api/v1/kpis/hotel/by-country
