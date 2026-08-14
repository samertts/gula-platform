# Live site verification — 2026-08-14

- URL checked: https://www.gula-platform.org/
- Redirect observed: https://www.gula-platform.org/login
- Page title: جولا | مركز العمليات الصحية
- Visible production UI: GULA Health Platform / secure access.
- Citizen and institution login paths are visible.
- Five language choices are visible: Arabic, English, Kurdish, Turkmen, Syriac.
- Demo Mode section is visible and states that data and workflows are synthetic and fully isolated.
- Demo roles visible: demo doctor, demo lab technician, demo lab manager, demo citizen.
- CTA text visible: فتح العرض التجريبي الآمن.
- No login, posting, payment, or other sensitive action was performed.

Initial conclusion: the official domain is reachable and exposes the unified login/demo entry surface. Interactive demo behavior still needs to be verified.

After scrolling to the demo section, the official page exposed the selectable demo persona control and the visible button `فتح العرض التجريبي الآمن`. The browser did not submit it yet; this was a passive availability check only.

Direct HTTPS verification completed. The official domain responds with HTTP/2 200 from Vercel and serves `/assets/index-BtiSTBdA.js`. SHA-256 of the remote asset equals the local `frontend-v3/dist/assets/index-BtiSTBdA.js` hash (`eaae42a54385f33e45fb4fa92d17efb85f6e6767adba0fae9741e42cc45f811d`). Therefore the deployed JavaScript entry asset matches the locally verified frontend-v3 build. The browser click attempt returned a transient extension HTTP 504; source inspection confirms the button calls `startDemo` and navigates to `/dashboard`, and local demo-isolation tests cover the behavior.
