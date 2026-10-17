# kmehul.github.io

Portfolio site for Kumar Mehul, served by GitHub Pages from `main`.

## Shipping changes

After every change: commit, push the working branch, then fast-forward `main` to it
(`git push origin HEAD:main`) so the change goes live. The owner has given standing
permission for this; no pull request is needed. If that push is rejected because `main`
has moved, run `git fetch origin main`, merge `origin/main` into the branch, rebuild with
`python3 tools/build.py` (regenerate the HTML rather than hand-resolving conflicts in
it), commit, then push again.

## Editing the site

- Page content lives in `tools/build.py`. Never edit `index.html` or `designs/*.html` by
  hand; they are generated. Rebuild with `python3 tools/build.py` and commit the output.
- Outside `build.py`: `js/site.js` holds the contact email fallback and the FormSubmit
  endpoint (also in `build.py`), and `og-image.png` is a static link-preview image with
  the name and title baked in.
- Copy rules: no em dashes, z-spellings, no filler adjectives.
- Figures come from the resume or the `kmehul/citibike-jc-mobility-analysis` repo.
  Exception: the California Food Inspection card is kept on purpose though the resume
  no longer lists it. Do not remove it unless the owner asks.

## Updating the resume

When given a new resume PDF:

1. Diff its text against the current one: `git show HEAD:KumarMehul_Resume.pdf` to a
   temp file, `pdftotext -layout` on both, then `diff -w` (layout output has
   whitespace-only noise).
2. Replace `KumarMehul_Resume.pdf` with it, keeping that exact filename (the site links
   to it).
3. Grep `tools/build.py` for every changed fact or figure, since they repeat across the
   hero, stats band, about, experience, projects, skills, education and meta tags.
   A new email needs `js/site.js` and a new FormSubmit endpoint too; a new name or title
   needs `og-image.png` redone. The build asserts 94,689 trips and the 17.8% peak
   against the chart data, so changing those needs new data from the CitiBike notebooks.
4. Rebuild, then ship as above.
