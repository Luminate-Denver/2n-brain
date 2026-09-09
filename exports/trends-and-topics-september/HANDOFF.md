# September Trends & Topics handoff

Date: September 9, 2026. COMPLETE: CJ manually sent campaign 46. ActiveCampaign verified status 5 (completed), 273 sent, September 9 at 7:42:52 a.m. MT; completed at 7:43:07 a.m. MT. No broadcast action remains.

## Current state

- Completed campaign 46, message 57, list 2; canonical subject: `2^n Family Office Brief: September 2026`.
- Final preview: `trends-and-topics-september-v1.html`. The filename stayed v1 throughout review; email test subjects advanced separately through preview v6.
- Latest test v6 sent successfully to CJ, Matt, and Sydney. Canonical subject restored after each round.
- All six Matt revisions from September 9 at 4:53 a.m. MT applied. Latest event wording: “Suggest or host in-person events and see which members are attending.” CJ explicitly retained the single sentence.
- Contact audit freshly verified 273 active recipients, zero eligible completed non-test family-office members missing. Ten additions verified. Josh Shapiro unsubscribed at CJ's request. Existing opt-outs/bounce preserved; invited/test users excluded.
- Eleven featured firms do not imply eleven new email additions: Brodie and Jefferson River already had active contacts; nine roster members plus Brandon Nel account for ten additions. Brandon is on the email list; CJ did not request adding his firm to the newsletter roster.
- Source repeated Sentinel Global while claiming four Deal Partners. Preview uses three unique firms, without a numerical partner claim.
- The source is an editorial cohort, not a strict August creation-date query; includes early September additions.

## Locked presentation

Full-width roster dotted lines, location tracking 0.5px, 18px list-to-button gaps, no trailing paragraph margin in buttonless cards. Metadata centered with one 80px gold divider between title and volume/date. Talent stat: 1 plus 16px superscript st, label Talent Posting. Event cards all white with gold date text. One shared spotlight CTA. Talent section has explicit spacing and “Refer to the Talent Vault.” No Better Matches card. Signal names the 2^n team and “Ring the Concierge.”

## Workflow and caveats

`build-preview.py` reproduces the final artifact; do not overwrite it with an older template. `update-draft.py` checks campaign status 0 and now intentionally refuses the completed campaign. Do not modify or resend campaign 46. Never rerun historic send/sync scripts: they performed external actions and are not generally idempotent. A new test needs a unique subject, then canonical subject restoration. No production broadcast endpoint is provided.

Browser tooling blocked local-file rendering. CJ reviewed the local artifact and supplied screenshots across phone/tablet widths. HTML structure/compliance checks passed; automated viewport-overflow matrix remains unverified. Footer retains AC address/unsubscribe merge tags. CJ changed the AC default address before test v5; actual delivered address was not independently verified.

Sensitive audit exports, contact sync logs and source copy remain local. They are not required to render or update the draft. Audit findings in review-notes.md are historical; current contact audit is fo-list-audit.md. No app code or 2N records were modified.
