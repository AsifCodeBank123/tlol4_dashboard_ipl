# TLOL4 Sports League Dashboard

A clean Streamlit multipage dashboard for an office multi-sport tournament using IPL-inspired team branding.

## Teams

- Rachita Royals
- Gayatri Titans
- Komal Knight Riders
- Royal Challengers Bijal

## Google Sheet Format

You can use the new Team headers or keep the older House headers. The app supports both.

### Participants

Preferred columns:

```text
Participant | Team | Sport | Points | Matches | Wins | Bonus
```

Backward-compatible old column:

```text
Participant | House | Sport | Points | Matches | Wins | Bonus
```

### Fixtures

Preferred columns:

```text
Sport | Date | Time | Participant 1 | Team 1 | Participant 2 | Team 2 | Match | Venue | Status
```

Backward-compatible old columns are also supported:

```text
Sport | Date | Time | Participant 1 | House 1 | Participant 2 | House 2 | Match | Venue | Status
```

## Features

- Home page with team standings, top participants, top teams, upcoming fixtures, and current winners
- Fixtures page with sport tabs and rules/card details for every sport
- Leaderboard with participant points merged across all sports
- Config-driven teams, colors, sheet ID, status colors, and sport rules
- Light and dark mode CSS support

## Run

```bash
pip install -r requirements.txt
streamlit run main.py
```

Place your Google service account file in the project root as:

```text
service_account.json
```


## Team pages

The sidebar team names are clickable. Each team has a standalone profile page showing:

- Team slogan and captain
- Total points
- Members count
- Sports represented
- Wins
- Sport contribution
- Top performers
- Team fixtures
- Roster and point breakdown

If a team has no matching rows in the Google Sheet, fallback member names from `config.json` are shown so the page remains usable during setup.
