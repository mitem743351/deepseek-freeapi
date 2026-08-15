# Phase 2 capture matrix

Each ID has an independent worksheet in `network/scenarios/`. Status is **PENDING** until sanitized normal-browser evidence exists.

| Group | IDs | Goal | Status |
|---|---|---|---|
| Session | A01 initial page load; A02 authenticated page load; A03 reload; A04 sign out | Establish browser boot/session boundary without recording credentials. | PENDING |
| Conversation | B01 create; B02 first message; B03 second message; B04 reload; B05 switch; B06 rename; B07 delete; B08 search | Identify conversation lifecycle and persistence behavior. | PENDING |
| Generation | C01 ordinary; C02 long; C03 stop; C04 regenerate; C05 natural retry; C06 edit | Determine stream lifecycle and mutation/cancellation behavior. | PENDING |
| Reasoning/model | D01 reasoning; D02 model; D03 generation settings; D04 response settings | Identify only visible feature-specific state/network behavior. | PENDING |
| Files | E01 TXT; E02 MD; E03 JSON; E04 CSV; E05 PDF; E06 DOCX; E07 XLSX; E08 image | Determine supported attachment pipeline using synthetic data only. | PENDING |
| Search | F01 trigger; F02 results; F03 sources; F04 follow-up | Determine visible search/source workflow only. | PENDING |
| Sharing/export | G01 share; G02 export; G03 copy | Determine visible artifact/export behavior without publishing private data. | PENDING |
