# CV Intelligence Daily

Podcast quotidiano (lunedì–venerdì) su Iveco Group, Tata Motors e FPT Industrial, generato in automatico e ascoltabile su Spotify alle 7.

## Come funziona

1. **Verso l'una di notte**, un'attività programmata di Claude cerca le notizie, scrive lo script seguendo `ISTRUZIONI_EPISODIO.md` e lo salva in `scripts/AAAA-MM-GG.md`.
2. **GitHub Actions** (`.github/workflows/build-episode.yml`) parte da solo: manda il testo a ElevenLabs, crea l'MP3 e lo pubblica come *release* del repository.
3. Lo stesso workflow aggiorna `docs/feed.xml`, servito da GitHub Pages.
4. **Spotify** legge il feed più volte al giorno e mostra il nuovo episodio.

## Configurazione (una volta sola)

### 1. ElevenLabs
- Crea la voce con *Voice Design* e salvala in *My Voices*. Copia il suo **Voice ID** (menu della voce → *Copy voice ID*).
- In *Profilo → API Keys* crea una chiave API.

### 2. Secret del repository
GitHub → repository → *Settings → Secrets and variables → Actions → New repository secret*:
- Nome: `ELEVENLABS_API_KEY`
- Valore: la chiave API di ElevenLabs

### 3. `podcast.json`
Sostituisci i valori `DA_COMPILARE`:
- `owner_name`, `owner_email`: il tuo nome e l'email che riceverà il codice di verifica di Spotify (compare nel feed pubblico).
- `site_url`: `https://<username>.github.io/cv-intelligence-daily`
- `elevenlabs.voice_id`: il Voice ID.

### 4. GitHub Pages
*Settings → Pages → Build and deployment*: Source **Deploy from a branch**, Branch **main**, cartella **/docs**. Dopo un minuto il feed è su `https://<username>.github.io/cv-intelligence-daily/feed.xml`.

### 5. Prova
*Actions → Genera episodio → Run workflow* con **Prova senza ElevenLabs** spuntato: verifica che tutto giri senza consumare caratteri. Poi rilancialo senza spunta: genera il primo episodio vero.

### 6. Spotify
Su [creators.spotify.com](https://creators.spotify.com) → *Get started* → *Find an existing show* / *Add your podcast via RSS*, incolla l'indirizzo del feed e inserisci il codice che arriva all'email di `owner_email`. Poi segui il podcast dalla tua app.

## Operazioni utili

- **Rigenerare un episodio**: elimina la sua release (e il tag `ep-AAAA-MM-GG`), togli la voce da `episodes.json`, poi rilancia il workflow.
- **Cambiare voce**: modifica `voice_id` o `voice_settings` in `podcast.json`.
- **Lezioni tecniche**: il piano è in `lezioni_tecniche.md`; aggiungi argomenti in fondo quando vuoi.
- **Se qualcosa fallisce**: GitHub ti manda un'email; i dettagli sono nella scheda *Actions*.

## Costi

Ogni episodio è circa 17.000–19.000 caratteri, cioè circa 400.000 caratteri al mese. Con il modello `eleven_multilingual_v2` serve il piano ElevenLabs Pro. GitHub, GitHub Pages e Spotify for Creators sono gratuiti.
