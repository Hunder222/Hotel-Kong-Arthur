# Go-Live Checkliste — Hotel Kong Arthur Operations & Analytics Platform

> **Formål:** Denne checkliste beskriver de konkrete tekniske, sikkerhedsmæssige, juridiske og driftsmæssige krav, der skal være opfyldt og verificeret, før systemet kan gå fra lokal prototype (`docker compose up`) til live produktionsdrift hos **Hotel Kong Arthur**.

---

## 1. Sikkerhed, Adgangskontrol & Netværk (Kritisk)

- [ ] **Brugerautentificering & RBAC:** Implementér login (f.eks. OAuth2/OIDC eller SSO) og rollebaseret adgangskontrol, så receptionister, ledelse/CFO og administratorer kun har adgang til deres respektive funktioner (pt. er autentificering udeladt jf. `specs/001-hotel-analytics-platform/spec.md`).
- [ ] **Maskin-til-maskin API-sikkerhed:** Indfør API-nøgler eller service-tokens (f.eks. Bearer JWT) til eksterne klienter som hotellets bookingsystem og CFO'ens Tableau Desktop.
- [ ] **HTTPS / TLS-kryptering:** Sæt en reverse proxy / load balancer med gyldigt TLS-certifikat foran `frontend` (`frontend/nginx.conf` lytter pt. kun på HTTP port `80`) og tving redirect fra HTTP til HTTPS.
- [ ] **Luk eksponerede dev-porte:** Fjern direkte eksponering af API (`8000`) og Swagger UI (`8081`) i produktionskonfigurationen (`docker-compose.yml`), eller begræns adgang til internt netværk/VPN + login.
- [ ] **Fjern dev-secrets:** Erstat alle udviklings-defaults (`DB_PASSWORD: hotel_dev` m.fl. i `docker-compose.yml` og `backend/src/hotel_api/config.py`) med stærke secrets indlæst sikkert fra miljøvariabler eller en secret manager.
- [ ] **Lås `CORS_ORIGINS`:** Opdatér `CORS_ORIGINS` fra `http://localhost:8080,http://localhost:8081` til udelukkende at tillade hotellets rigtige produktionsdomæne(r).
- [ ] **HTTP-sikkerhedsheadere & Rate Limiting:** Tilføj security headers (`Strict-Transport-Security`, `X-Content-Type-Options`, `Content-Security-Policy`) og rate limiting i Nginx/reverse proxy mod misbrug og brute-force.

---

## 2. Integrationer & Live Datastrømme

- [ ] **Integration til hotellets PMS / Bookingsystem:** Opsæt og test automatisk synkronisering (webhooks eller planlagt sync) fra hotellets eksisterende bookingsystem til `POST/PUT/DELETE /api/v1/bookings`.
- [ ] **Lobbybar / POS-integration:** Tilføj write-endpoints og/eller integration til barens kassesystem (POS), så `bar_drink_sales` opdateres løbende (pt. er `GET /api/v1/bar/drink-sales` i `backend/src/hotel_api/presentation/api/routers/bar.py` kun read-only og baseret på seed-data).
- [ ] **Indsamling af gæsteanmeldelser:** Kobl hotellets rigtige review-kilde (spørgeskema, Booking.com, TripAdvisor eller lign.) til `POST /api/v1/reviews`, så kundetilfredsheds-KPI'en (`K3`) afspejler aktuelle ophold.
- [ ] **Vedligeholdelse af værelsestyper & priser:** Etablér en arbejdsgang eller admin-endpoints til opdatering af `room_types` og `room_type_rates` (pt. indlæses de kun én gang via `db/init/02_reference_data.sql`), så prisjusteringer og sæsonændringer kan håndteres uden kodeændringer.
- [ ] **Tableau-opkobling i produktion:** Opdatér CFO'ens Tableau Desktop-forbindelse fra `http://localhost:8000/api/v1/*` til produktions-URL med autentificering og bekræft, at `$.items[*]` fortsat indlæser alle rå endpoints korrekt.

---

## 3. Database, Migrationer & Skalerbarhed

- [ ] **Skema-migrationsværktøj (Alembic):** Indfør et migrationsværktøj (f.eks. Alembic), da `db/init/01_schema.sql` kun afvikles på en tom Docker-volume og ikke kan håndtere løbende skemaændringer i produktion.
- [ ] **Automatisk backup & testet restore:** Opsæt daglige, krypterede backups af PostgreSQL-databasen (eller brug en managed PostgreSQL-service) med point-in-time recovery, og gennemfør en dokumenteret restore-test.
- [ ] **Connection pooling:** Erstat én-ny-forbindelse-pr.-request i `backend/src/hotel_api/data/connection.py` med connection pooling (`psycopg_pool` eller PgBouncer) for at undgå forbindelsesflaskehalse ved spidsbelastning.
- [ ] **Flere API-workers / høj tilgængelighed:** Skalér `uvicorn` i `backend/Dockerfile` til flere workers (eller flere container-replicas bag load balancer), så API'et kan håndtere samtidig trafik uden nedetid ved genstart.
- [ ] **Beskyt mod demo-seed i produktion:** Sikr at `seed` og `seed-realistic` profilerne i `docker-compose.yml` er deaktiveret eller blokeret i produktionsmiljøet, så rigtige hoteldata ikke overskrives ved en fejl.

---

## 4. GDPR & Persondata (PII)

- [ ] **Databehandleraftale & fortegnelse:** Få udarbejdet databehandleraftale og dokumentér behandlingen af gæstedata (navn, nationalitet, opholdsdatoer i tabellen `bookings` i `db/init/01_schema.sql`).
- [ ] **Slette- og anonymiseringspolitik:** Implementér automatisk sletning eller anonymisering af `first_name` og `family_name` efter udløb af opbevaringsfristen, så historiske omsætnings- og belægnings-KPI'er kan bevares GDPR-lovligt.
- [ ] **Audit-logging:** Log hvem der tilgår, opretter, ændrer eller sletter gæsteoplysninger og bookinger, samt hvornår det sker.
- [ ] **Kryptering at-rest:** Sørg for at produktionsdatabasen og backups ligger på krypteret disk/storage.

---

## 5. Forretningslogik & Datavalidering

- [ ] **Afklaring af kapacitets- / overbooking-tjek:** Beslut med hotellet, om `BookingService` (`backend/src/hotel_api/business/services/booking_service.py`) skal validere antal aktive bookinger mod `room_count` pr. dato, hvis receptionen opretter bookinger direkte i systemet (pt. tjekkes kun inputformat, datoer og prisbånd).
- [ ] **Godkendelse af KPI-definitioner:** Verificér med hotellets ledelse/CFO, at sæsoninddeling (`low`, `mid`, `high`), belægningsberegning (`room-nights` ud af 214 værelser) og prisintervaller stemmer 100% overens med hotellets regnskabsprincipper.
- [ ] **Initial produktionsdata:** Indlæs rigtige stamdata (værelsestyper, priser, aktive bookinger og evt. historiske data til sammenligning) før åbning.

---

## 6. Drift, CI/CD & Overvågning

- [ ] **Produktionshosting & DNS:** Klargør produktionsmiljø (cloud, PaaS eller on-prem server), domæne og DNS-opsætning.
- [ ] **CI/CD-pipeline med automatiske tests:** Opsæt pipeline (f.eks. GitHub Actions), der automatisk kører alle 4 testsuiter (`pytest` — `unit`, `architecture`, `contract` og `integration`) og blokerer deploy ved fejl.
- [ ] **Central logging & alarmering:** Opsæt struktureret logging, central logopsamling og alarmer ved 5xx-fejl, høje svartider eller manglende databaseforbindelse.
- [ ] **Uptime-overvågning:** Kobl ekstern health-monitoring på `GET /api/v1/health` med notifikation til driftsansvarlig ved nedetid.

---

## 7. Cutover & Go-Live Dag

- [ ] **Frys & backup:** Tag fuld backup af eksisterende data før endelig cutover.
- [ ] **Smoke test i produktion:** Bekræft efter deploy at:
  - `GET /api/v1/health` svarer `200 OK`
  - En test-booking kan oprettes, vises, opdateres og slettes via frontend (`F1`), og testdata ryddes op igen
  - Alle `Hotel Analytics`-visninger (`F2`) og Tableau-udtræk opdateres korrekt
- [ ] **Rollback-plan klar:** Dokumentér præcis hvordan systemet rulles tilbage til forrige version/backup, hvis kritiske fejl opstår under opstarten.
- [ ] **Brugerintroduktion & support:** Gennemfør kort oplæring af receptionister og CFO, og udpeg kontaktperson for support i de første driftsuger.
