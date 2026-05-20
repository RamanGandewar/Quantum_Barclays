---
name: New migration state proposal
about: Propose adding a state to the SMSM
---

**Proposed state name**

**Position in state order** (between which existing states)

**Classical security level** [ ] Full [ ] Partial [ ] Reduced [ ] None

**Quantum security level** [ ] None [ ] Partial [ ] Strong [ ] Maximum

**Evidence required to enter this state**

**Rollback condition**

**Files that would need to change**
- [ ] `backend/verifier-api/app/state_machine.py`
- [ ] `frontend/dashboard/src/constants/states.ts`
- [ ] `frontend/dashboard/src/components/StateMachineView.tsx`
- [ ] `docs/research-notes.md`
- [ ] `docs/prd-traceability.md`
- [ ] `README.md` migration states table
