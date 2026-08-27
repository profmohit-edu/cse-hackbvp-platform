# CSE HackBVP Platform

A compact web-based hackathon and project management platform created by Mohit Tiwari, Department of Computer Science and Engineering, Bharati Vidyapeeth's College of Engineering, New Delhi.

## Working functions

- Team and project registration with validation
- Project listing and stage/status tracking
- Submission link and progress-note updates
- Mentor review and actionable feedback
- Evaluator scoring across innovation, technical implementation, impact and presentation
- Dashboard totals, stage distribution and ranked evaluated projects
- Persistent browser storage with JSON backup/restore
- Clearly labelled synthetic demonstration dataset

The static deployment uses browser `localStorage`; it is a genuine single-browser demonstrator, not a multi-user production database. Exported JSON provides a portable audit trail.

## Run and test

```bash
python3 -m http.server 8000
node --test tests/core.test.js
```

Version 1.0.0, completed 27 August 2026. MIT licensed.
