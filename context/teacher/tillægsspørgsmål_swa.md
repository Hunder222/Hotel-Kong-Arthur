# Tillægsspørgsmål til Hotel Kong Arthur opgaven (SWA)

Her er 10 spørgsmål, som I løbende kan tænke over, mens I laver opgaven.

Til fremlæggelsen kan I bruge disse som afsæt for, hvad I vil fortælle os. I kan eventuelt også blive spurgt om dette af Claus.

De er ordnet, så de går fra at afdække helheden, ned i de enkelte dele og så tilbage til sammenhængen.

---

### 1. Arkitekturdiagrammet
Gennemgå jeres arkitekturdiagram fra `README.md`. Hvilke komponenter består systemet af, og hvordan kommunikerer de med hinanden?

### 2. Følg et request
En bruger opretter en booking i jeres frontend. Hvad sker der trin for trin, fra klikket i browseren til data ligger i MySQL og svaret er tilbage hos brugeren?

### 3. 3-lags arkitektur
Hvilket ansvar har hvert af de tre lag i jeres backend, og hvor i koden går grænserne mellem dem? Vis et eksempel på noget, I bevidst har placeret i ét lag frem for et andet.

### 4. Forretningslogikkens placering
Hvor beregnes nøgletal som belægningsgrad og indtjening: i databasen, i backendens logiklag eller i Tableau? Hvorfor har I valgt den placering, og hvad ville konsekvensen være af at flytte beregningen?

### 5. Udskiftelighed
Hvis MySQL skulle udskiftes med en anden database, eller frontenden med hotellets eget bookingsystem, hvilke dele af jeres system skulle så ændres, og hvilke ville være uberørte? Hvad siger det om jeres lagdeling?

### 6. REST-design
Hvordan har I designet jeres ressourcer og endpoints? Forklar jeres valg af URL-struktur, HTTP-metoder og statuskoder ud fra et konkret endpoint, og vis hvordan domænemodellen afspejles i API'et.

### 7. API-kontrakten
Hvilken rolle spiller OpenAPI-specifikationen i jeres system? Hvem er "kunderne" til kontrakten (frontend, Tableau, hotellets bookingsystem), og hvordan sikrer I, at specifikationen og den faktiske implementering stemmer overens?

### 8. Docker og docker-compose
Hvilke containere består jeres system af, og hvad sker der, når man kører `docker-compose up`? Hvordan finder containerne hinanden, hvordan håndterer I opstartsrækkefølge (fx at databasen skal være klar før backenden), og hvad sker der med data, når containerne lukkes ned?

### 9. Fra statisk til live data
Opgaven kræver, at systemet løbende kan opdatere data frem for kun at vise historiske CSV-filer. Hvordan understøtter jeres arkitektur det, og hvordan får Tableau adgang til de aktuelle data via jeres REST API?

### 10. Ejerskab og vurdering
I har brugt AI til at udvikle systemet. Udpeg en arkitekturbeslutning, som AI'en foreslog, og som I enten ændrede eller valgte at beholde. Hvad var begrundelsen, og hvad er den største svaghed i jeres nuværende arkitektur, hvis systemet skulle i produktion?