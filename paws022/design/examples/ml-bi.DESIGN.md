# Example: ML / BI dashboard app (e.g. IS 108 crypto prediction)

> Copy ideas into your project `design/DESIGN.md`. Not used automatically.

## Status

- **Design phase:** in progress
- **Primary tool:** Google Stitch (Cursor MCP)

## Design system (short)

| Token | Value |
|-------|--------|
| Primary color | `#2563eb` (academic blue) |
| Typography | System UI / sans-serif |
| Spacing | Comfortable padding, card-based layout |
| Breakpoints | Desktop-first demo; readable on laptop |

## Screens

| ID | Name | Route | Notes | Asset |
|----|------|-------|-------|-------|
| S1 | Data upload | `/upload` | CSV upload, row preview, Import | `exports/s1-upload.html` |
| S2 | Preprocess & features | `/preprocess` | Indicator options, run preprocess | `exports/s2-preprocess.html` |
| S3 | Train & compare | `/models` | KNN, SVM, ANN cards, train buttons, metrics table | `exports/s3-models.html` |
| S4 | Signal & results | `/results` | Buy/Sell (1/0), last prediction, optional chart | `exports/s4-results.html` |

## Interaction notes

- S1 → S2: after successful import
- S3: show accuracy/precision/recall placeholders until API returns real metrics
- S4: highlight predicted class with clear UP/DOWN labels

## Implementation gate

**ready for implementation** when S1–S4 exist in `design/exports/` or user approves wireframes.

## Changelog

| Date | Change |
|------|--------|
| | Example template for POS |
