# Firebase Usage

> PROGRAM-02 read-only analysis.

## Result: ZERO Firebase dependencies

| Check | Result |
|---|---|
| package.json dependencies | no firebase / firebase-admin / @capacitor/firebase |
| src/ import scan | 0 references to firebase/firestore/initializeApp |
| Alternative stack | self-hosted backend (Python/FastAPI) + axios + react-query |

## Classification

- **Required:** none
- **Optional:** none
- **Obsolete:** none
- **Replaceable:** none
- **Already replaced:** push notifications (FCM) are sent by the backend `shared/notifications` service (server-side FCM), not by the frontend — the frontend has no direct Firebase dependency.

## Conclusion
Frontend is Firebase-free and fully aligned with the 'Self-Hosted First' constitution.
