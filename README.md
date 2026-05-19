# Vibe Jury Export

Extract juror ratings from VI.BE platform into CSV for spreadsheet analysis.

## Quick Start

```bash
cd ~/utils/busker-sheet
python3 extract_submissions.py
```

## Workflow

1. **Export HAR file from VI.BE**
   - Open the submissions page in browser
   - Open DevTools (F12) → Network tab
   - Refresh the page (let it fully load all submissions)
   - Scroll down to the bottom of the page so all submissions are loaded (important!)
   - Right-click in Network panel → "Save all as HAR"
   - Save to this directory

2. **Run extraction**

   ```bash
   python3 extract_submissions.py
   # Or specify a HAR file:
   python3 extract_submissions.py "vi.be_Archive [26-05-18 16-36-24].har"
   ```

3. **Open in LibreOffice Calc**

   ```bash
   libreoffice busker_submissions_latest.csv
   ```

## Output

| File                                     | Description                           |
| ---------------------------------------- | ------------------------------------- |
| `busker_submissions_latest.csv`          | Always current (overwritten each run) |
| `busker_submissions_YYYYMMDD_HHMMSS.csv` | Timestamped backup                    |

## CSV Columns

| Column           | Description                                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------------------------- |
| Artist           | Band/artist name                                                                                                |
| VI.BE Page       | Link to artist profile                                                                                          |
| Avg Rating       | Average of all juror ratings                                                                                    |
| Rated By         | Progress (e.g., `3/4` = 3 of 4 jurors rated)                                                                    |
| [Juror] (Rating) | Individual 1-5 star rating per juror                                                                            |
| Broad Genre      | Auto-classified: hip-hop, electronic, metal, punk, rock, pop, singer-songwriter, jazz/soul, world, experimental |
| Shortlisted      | Yes/No                                                                                                          |
| [Juror] (Notes)  | Comments from each juror                                                                                        |
| Email            | Contact email                                                                                                   |
| Phone            | Contact phone (normalized, no spaces)                                                                           |
| Location         | City                                                                                                            |
| Genres           | Original genre tags                                                                                             |
| Custom Genre     | Artist's custom genre description                                                                               |

## Customizing Genre Classification

Edit `BROAD_GENRE_MAPPING` in `extract_submissions.py` to adjust keyword mappings.

Edit `GENRE_PRIORITY` to change which genre wins when multiple match (first in list = highest priority).

## Requirements

- Python 3.6+
- No external dependencies
