# kmehul.github.io

Portfolio site for Kumar Mehul, served by GitHub Pages from `main`.

## Shipping changes

After every change: commit, push the working branch, then fast-forward `main` to it
(`git push origin HEAD:main`) so the change goes live. The owner has given standing
permission for this; no pull request is needed. If `main` has moved and the push is not
a fast-forward, merge `origin/main` into the branch first, rebuild, then push.

## Editing the site

- All content lives in `tools/build.py`. Never edit `index.html` or `designs/*.html` by
  hand; they are generated. Rebuild with `python3 tools/build.py` and commit the output.
- Copy rules: no em dashes, z-spellings, no filler adjectives.
- Every figure on the site must come from the resume or the
  `kmehul/citibike-jc-mobility-analysis` repo.

## Updating the resume

When given a new resume PDF:

1. Replace `KumarMehul_Resume.pdf` with it.
2. Diff its text against the previous version (`pdftotext -layout` on both) to find what
   changed.
3. Mirror each change in `tools/build.py` (about, experience, projects, skills,
   education), rebuild, then ship as above.
