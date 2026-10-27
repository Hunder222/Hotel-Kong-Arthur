# Hotel Kong Arthur

**Analyse af Hoteldata med Tableau, ITA 3. semester – 2 ugers tværfagligt miniprojekt**  
*Reference:* [https://arthurhotels.dk/hotel-kong-arthur/](https://arthurhotels.dk/hotel-kong-arthur/)

---

## Baggrund

Du arbejder som IT-arkitekt for en virksomhed, der leverer innovative løsninger til hotelbranchen. Du har fået til opgave at udvikle et system, der skal hjælpe Hotel Kong Arthur med at optimere deres drift gennem en avanceret dataanalyse-platform.

---

## Systemkrav

* **Formål:** Systemet skal kunne analysere og præsentere data fra hoteldrift for beslutningstagere.
* **Teknologistak:** En Backend med 3-lags arkitektur og en grænseflade i JSON. Kontrakten skal leveres som en OpenAPI-specifikation. Alt skal køre i Docker-containere, og I skal gøre brug af `docker-compose`. Programmeringssprog er frit, og databasen skal være MySQL.
* **Beregninger:** Systemet skal kunne beregne nøgletal som belægningsgrader, indtjening, kundetilfredshed mm.
* **Visualisering:** I skal udarbejde et interaktivt dashboard i Tableau, der viser nøgletallene.

---

## Datagrundlag

* Eksempler på data findes i dette repository: [https://github.com/ITAKEA/hoteldata](https://github.com/ITAKEA/hoteldata). Brug dette data som inspiration til det system, I skal lave.
* CSV-filerne er et udsnit af, hvad vi kunne få fat i fra hotellets nuværende systemer. Data er i CSV/XSLT-format og er dermed statisk og historisk.
* I skal lave et system, der **løbende kan opdatere data**, og som kan **vise data live**, og altså ikke kun historisk som i disse CSV-filer.

---

## Udvikling af systemet

* I forventes at gøre brug af AI til løsning af hele denne opgave.
* I forventes også at tage ejerskab for de udviklede produkter. Med det menes, at I skal kunne forklare og vurdere det, I eller jeres AI har udviklet.

---

## Grupper

I skal arbejde i de grupper, I har lavet i starten af dette semester.

---

## Data om Hotel Kong Arthur

Hotel Kong Arthur har **214 værelser**, og afhængig af værelsets størrelse og kategori kan hotellet huse mellem 1-4 personer pr. værelse. Dette betyder, at hotellet maksimalt kan rumme omkring **428 gæster ad gangen**, hvis alle værelser er optaget og indrettet til den maksimale kapacitet.

### Værelsestyper og priser

Hotel Kong Arthur tilbyder 8 forskellige værelsestyper. Priserne varierer afhængigt af sæsonen:

1. **Standard enkeltværelse:** Ideelt til solo-rejsende.  
   *Pris:* ca. 900–1.200 DKK pr. nat afhængig af lav- eller højsæson.
2. **Grand lit værelse (dobbelt økonomi):** Lidt større enkeltværelse eller kompakt dobbeltværelse.  
   *Pris:* ca. 1.100–1.400 DKK pr. nat.
3. **Standard dobbeltværelse:** Velegnet til par eller forretningsrejsende.  
   *Pris:* ca. 1.200–1.600 DKK pr. nat.
4. **Superior dobbeltværelse:** Rummeligere med mere luksuriøse faciliteter.  
   *Pris:* ca. 1.400–2.000 DKK pr. nat.
5. **Junior suite:** Unikke værelser, nogle med historisk inspiration, andre mere moderne.  
   *Pris:* ca. 1.800–2.500 DKK pr. nat.
6. **Spa executive:** Suiter med fokus på wellness, inkl. spa-adgang. Spa-faciliteter og behandlinger kan være inkluderet.  
   *Pris:* ca. 2.000–2.800 DKK pr. nat.
7. **Suite:** Store, luksuriøse værelser med individuelle designs.  
   *Pris:* ca. 2.500–3.500 DKK pr. nat.
8. **LOFT suite:** Suiter i to niveauer med udsigt over gårdhaverne.  
   *Pris:* ca. 3.000–4.000 DKK pr. nat.

### Sæsonvariationer

* **Lavsæson (typisk vintermånederne):** Værelser findes til lavere priser, f.eks. fra 800–1.200 DKK for standardværelser.
* **Mellemsæson (forår og efterår):** Priserne ligger normalt mellem 1.200–1.800 DKK for standard og superior værelser.
* **Højsæson (sommer og juletid):** Priserne stiger til deres højeste, og de mere luksuriøse værelser kan nå op mod 3.000–4.000 DKK per nat for suiter.

### Cocktailbar

Hotel Kong Arthur har en cocktailmenu, der tilbydes i lobbybaren sammen med vin, øl og kaffe. Cocktails bliver kombineret med snacks, der passer til.  
Receptionisten Helene Christine står også i baren. Hun laver 20 forskellige cocktails og 10 forskellige kaffetyper.

---

## Krav: Forretningsdesign og Analytics

Med udgangspunkt i backendens REST API skal I lave et interaktivt Tableau dashboard, der viser og beregner:

* Hvor kommer gæsterne fra (lande)?
* Hvor meget indtjening er der:
  * Pr. værelsestype (pr. sæson)
  * Pr. land
* Hvilke værelser tjener Kong Arthur flest penge på?
* Hvilke lande tjener Kong Arthur flest penge på?
* Beregn årets indtjening for hotellet.
* Find også selv et interessant nøgletal at vise.

Dashboardet skal også vise og beregne følgende for **cocktailbaren**:
* Hvor meget har Helene Christine solgt totalt for året?
* Vis omsætning pr. drink.
* Vis procentfordeling af cocktails og kaffe for Helene Christine.

---

## Krav: Systemudvikling

I skal udvikle systemet spec-drevet (**Spec-Driven Development**) med GitHub Spec Kit ([https://github.com/github/spec-kit](https://github.com/github/spec-kit)), som I lærte det i AI-forløbet med hestecasen. Det betyder, at I beskriver hvad systemet skal gøre, før I eller jeres kodeagent skriver kode. Specifikationen er det, I styrer AI'en med, og det, I vurderer resultatet op imod.

### Workflowet
$$\text{Constitution} \rightarrow \text{Specify} \rightarrow \text{Clarify} \rightarrow \text{Plan} \rightarrow \text{Tasks} \rightarrow \text{Implement} \rightarrow \text{Converge}$$

* **Constitution:** Aftal principper og begrænsninger for hele projektet. Her hører opgavens faste krav hjemme: 3-lagsarkitektur, REST/JSON, OpenAPI-kontrakt, MySQL, Docker og `docker-compose up`.
* **Specify:** Beskriv funktionerne, brugerne, kravene og succeskriterierne, f.eks. booking-CRUD, live-opdatering af data, nøgletal og cocktailbaren.
* **Clarify:** Find og løs huller, uklarheder og ubesvarede spørgsmål. Hvad betyder "live"? Hvordan defineres en sæson? Hvordan beregnes belægningsgraden?
* **Plan:** Vælg den tekniske løsning. Specifikationen sagde *hvad*, planen siger *hvordan*: sprog, arkitektur, hovedkomponenter og datamodel.
* **Tasks:** Del planen op i små, konkrete opgaver, organiseret efter user stories og med afhængigheder kortlagt.
* **Implement:** Lad kodeagenten skrive koden, én opgave ad gangen. I gennemgår, hvad den laver.
* **Converge:** Tjek koden mod spec, plan og tasks. Mangler der noget, tilføjes nye tasks. Gentag implement $\rightarrow$ converge, indtil systemet matcher specifikationen.

*Brug checklister og analyse undervejs til at tjekke kvalitet og sammenhæng mellem spec, plan og tasks.*

### User Stories

* Skriv user stories i formatet:  
  `"Som <rolle> ønsker jeg <mål>, så <fordel>"`  
  *Eksempler:*
  * *"Som hoteladministrator ønsker jeg at se en rapport over månedlige belægningsgrader, så jeg kan planlægge kampagner."*
  * *"Som receptionist ønsker jeg at kunne oprette, rette og slette bookinger, så systemet altid viser den aktuelle belægning."*
* Brug **INVEST**-principperne til at sikre kvaliteten af jeres user stories.
* Hver user story skal have acceptkriterier (**Confirmation** i "The Three Cs"). Det er dem, I bruger i Converge-trinnet til at afgøre, om en story er færdig.

### Hvad skal afleveres (Systemudvikling)

* Jeres spec-artefakter i GitHub-repositoryet: constitution, spec, plan og tasks (f.eks. i en `specs/`-mappe).
* User stories med acceptkriterier.
* Resultatet af jeres sidste Converge-tjek: Hvad er implementeret, og hvad mangler?

---

## Krav: Softwarearkitektur

* I skal på baggrund af de krav og det data, I har fået stillet til rådighed, udvikle en backend-applikation bygget op efter en **3-lags arkitektur**. Programmeringssprog er valgfrit. Systemets præsentationslag skal levere et REST API som grænseflade. Systemets database skal være MySQL.
* API'ets kontrakt skal leveres som en **OpenAPI-specifikation** og skal kunne tilgås via et **Swagger UI**.
* Hotellets nuværende bookingsystem vil kunne skrive (POST/PUT/DELETE) til jeres API, men på prototype-niveau skal I lave en **frontend, som kan køre via browseren**. I denne frontend skal I kunne oprette, redigere og slette bookinger i applikationens backend.
* Alt i jeres system skal kunne køres ved hjælp af en enkelt `docker-compose up` kommando.

### Hvad skal afleveres (Softwarearkitektur)

* **Kildekode** i et GitHub repository. (I vil blive bedømt på, om alle i gruppen har deltaget i udviklingen af systemet – git commits).
* **Dokumentation:**
  * En `README.md`
  * En `CONTRIBUTE.md`
  * Swagger UI kørende i en Docker-container.
  * Et **arkitekturdiagram** over jeres samlede system i `README.md` filen.

---

## Præsentation

I skal præsentere jeres projekt for Lasse og Claus **fredag d. 6/11 kl 12.30 - 15.45**.

Der er 3 grupper i lokalet samtidigt. Hver gruppes præsentation og efterfølgende feedback tager i alt 20 minutter. Når én gruppe fremlægger, er det en anden gruppes opgave at tage noter og efterfølgende stille spørgsmål og give feedback.

### Tidsskema

| Tid | Grupper |
| :--- | :--- |
| **kl. 12.30–13.30** | Gruppe: 1, 2, 3 |
| **kl. 13.35–14.35** | Gruppe: 4, 5, 6 |
| **kl. 14.40–15.40** | Gruppe: 7, 8, 9 |

Hver gruppe får **10 minutter** til at præsentere, hvad I har lavet de sidste 2 uger, og efterfølgende er der **10 minutters** spørgsmål og feedback (først fra reviewgruppen og derefter fra Lasse og Claus).

*Vi har en stram tidsplan, så vær klar med jeres præsentation inden I kommer ind i lokalet.*