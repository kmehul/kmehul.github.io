# kmehul.github.io

Portfolio of Kumar Mehul, Data Analyst: **https://kmehul.github.io**

## How it is built

Plain HTML, CSS and JavaScript. The only tool is Python 3, used to generate the pages.

| Path | What it is |
|---|---|
| `tools/build.py` | All site content, the CitiBike chart data, and the page generator |
| `css/base.css` | Shared layout, mobile menu, scroll reveals and the chart system |
| `css/<design>.css` | One file per design language |
| `js/site.js` | Navigation, reveals, chart tooltips and the contact form |
| `index.html` | The live page (generated; edit `tools/build.py`, not this file) |
| `designs/` | Previews of every design (generated, hidden from search engines) |

The two charts in the CitiBike case study are drawn in the browser from the data in
`tools/build.py`, copied from the outputs of that project's notebooks. The build checks
that the hourly counts still add up to the 94,689 verified trips.

## Designs

The live site uses **Stripe**. Three alternatives are kept ready to switch to:

| Design | Character | Preview |
|---|---|---|
| Stripe (live) | Light, silk gradient, two-tone headlines | [/designs/stripe.html](https://kmehul.github.io/designs/stripe.html) |
| Linear | Dark, precise, soft indigo glow | [/designs/linear.html](https://kmehul.github.io/designs/linear.html) |
| Editorial | Data journalism: warm paper, serif, ruled columns | [/designs/editorial.html](https://kmehul.github.io/designs/editorial.html) |
| Vercel | Monochrome Swiss grid, Geist type | [/designs/vercel.html](https://kmehul.github.io/designs/vercel.html) |

To switch the live design, run one command, then commit and push:

```
python3 tools/build.py --live linear
```

After editing content in `tools/build.py`, rebuild with `python3 tools/build.py`.

## License

MIT, see [LICENSE](LICENSE).
