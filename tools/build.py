"""Build kmehul.github.io from one content model and four interchangeable designs.

    python3 tools/build.py                 rebuild with the current live design
    python3 tools/build.py --live linear   switch the live design (and remember it)

Writes index.html (the live site) plus designs/<name>.html previews of every
design and designs/index.html to compare them. Each design is a stylesheet in
css/ on top of css/base.css; content and behaviour are shared.

Every figure comes from the resume or the citibike-jc-mobility-analysis repo
(its README and the outputs of notebooks/03_visualizations.ipynb).
Copy rules: no em dashes, z-spellings, no filler adjectives.
"""
import argparse
import html
import re
from pathlib import Path

LIVE = "stripe"

ROOT = Path(__file__).resolve().parent.parent

ARR = ('<svg class="arr" width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">'
       '<path class="arr-line" d="M0 5h7"/><path class="arr-tip" d="M1 1l4 4-4 4"/></svg>')

DESIGNS = {
    "stripe": {"label": "Stripe", "note": "Light, silk gradient, two-tone headlines",
               "fonts": "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600&display=swap",
               "accent": "%23533afd"},
    "linear": {"label": "Linear", "note": "Dark, precise, soft indigo glow",
               "fonts": "https://fonts.googleapis.com/css2?family=Inter:wght@300..700&display=swap",
               "accent": "%235e6ad2"},
    "editorial": {"label": "Editorial", "note": "Data journalism: warm paper, serif, ruled columns",
                  "fonts": ("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..700;"
                            "1,6..72,300..600&family=Libre+Franklin:wght@400;500;600;700&display=swap"),
                  "accent": "%230f5e66", "no_count": True},
    "vercel": {"label": "Vercel", "note": "Monochrome Swiss grid, Geist type",
               "fonts": "https://fonts.googleapis.com/css2?family=Geist:wght@300..700&family=Geist+Mono:wght@400;500&display=swap",
               "accent": "%23171717"},
}

SECTIONS = [("about", "About"), ("experience", "Experience"), ("projects", "Projects"),
            ("skills", "Skills"), ("education", "Education"), ("contact", "Contact")]

LINKS = {
    "linkedin": "https://linkedin.com/in/kmehul992",
    "github": "https://github.com/kmehul",
    "email": "mailto:kumar-mehul_1@outlook.com",
    "dashboard": "https://public.tableau.com/shared/WW7ZSRM8C?:display_count=n&amp;:origin=viz_share_link",
    "citibike": "https://github.com/kmehul/citibike-jc-mobility-analysis",
    "imdb": "https://github.com/kmehul/IMDB-Movie-Data-Analysis",
    "food": "https://github.com/kmehul/California-Food-Inspection-Analysis",
}

# --- CitiBike chart data: notebooks/03_visualizations.ipynb outputs ----------------------
# rides_by_hour_rider (cell 59): rides started in each hour, May 2026, cleaned trips
MEMBER = [625, 315, 212, 129, 214, 763, 2183, 4165, 5577, 3274, 3221, 3177,
          3352, 3481, 3505, 4426, 5150, 7263, 6603, 4764, 3380, 2447, 1742, 1106]
CASUAL = [528, 322, 255, 193, 112, 209, 429, 714, 953, 773, 859, 1000,
          1164, 1280, 1367, 1643, 1810, 2163, 2143, 1700, 1340, 1066, 890, 702]
assert len(MEMBER) == len(CASUAL) == 24
assert sum(MEMBER) + sum(CASUAL) == 94689, "hourly counts must reconcile with the verified trip total"

# station_imbalance_combined (cell 112): average daily flow (departures minus arrivals) on days
# with more than 25 rides, stations with at least 6 such days; volume-weighted imbalance %
STATIONS = [
    ("Oakland Ave", 6.961538, 26, 17.822651),
    ("McGinley Square", 4.655172, 29, 10.834629),
    ("Glenwood Ave", 2.800000, 10, 16.981132),
    ("River St & 1 St", 2.419355, 31, 6.527735),
    ("South Waterfront Walkway - Sinatra Dr & 1 St", 2.172414, 29, 4.405874),
    ("Newport PATH", -1.161290, 31, 2.718007),
    ("Hoboken Terminal - Hudson St & Hudson Pl", -1.225806, 31, 3.366422),
    ("Washington St & Morgan St", -1.818182, 11, 5.176471),
    ("City Hall", -3.700000, 30, 6.068408),
    ("River St & Newark St", -6.161290, 31, 5.215144),
]
assert max(s[3] for s in STATIONS) > 17.8 and round(max(s[3] for s in STATIONS), 1) == 17.8


def hour_label(h):
    return "12am" if h == 0 else f"{h}am" if h < 12 else "12pm" if h == 12 else f"{h - 12}pm"


def signed(v):
    return ("+" if v > 0 else "−") + f"{abs(v):.2f}"


def stat(value, label, count=None, decimals=0, prefix="", suffix=""):
    """A stat block. `count` animates the number up once it scrolls into view."""
    num = f'<span data-count="{count}" data-decimals="{decimals}">{value}</span>' if count is not None else value
    return (f'<div class="stat"><dt class="stat-value">{prefix}{num}{suffix}</dt>'
            f'<dd class="stat-label">{label}</dd></div>')


def section_head(eyebrow, t1, t2=""):
    t2_html = f' <span class="t2">{t2}</span>' if t2 else ""
    return (f'<header class="section-head reveal"><p class="eyebrow">{eyebrow}</p>'
            f'<h2 class="section-title"><span class="t1">{t1}</span>{t2_html}</h2></header>')


def stack(items):
    return " &middot; ".join(f"<span>{i}</span>" for i in items)


# ---------------------------------------------------------------------------- charts

def hourly_chart():
    """Line chart, rides by hour. Plot is an SVG stretched to its box (strokes stay 2px);
    text, dots and the hover layer are HTML positioned in % so type never scales."""
    ymax = 8000
    y = lambda v: 100 - v / ymax * 100
    path = lambda vals: "M" + "L".join(f"{h * 10} {y(v):.3f}" for h, v in enumerate(vals))
    grid = "".join(f'<line x1="0" y1="{y(t):.3f}" x2="230" y2="{y(t):.3f}"/>' for t in range(0, ymax + 1, 2000))
    yticks = "".join(f'<span style="top:{y(t):.3f}%">{t:,}</span>' for t in range(0, ymax + 1, 2000))
    xticks = "".join(f'<span class="{"" if h % 6 == 0 else "minor"}" style="left:{h / 23 * 100:.3f}%">{hour_label(h)}</span>'
                     for h in range(0, 24, 3))
    peaks = "".join(
        f'<span class="lc-peak {s}" style="left:{h / 23 * 100:.3f}%;top:{y(v):.3f}%"><i></i><b>{v:,}</b></span>'
        for s, h, v in (("member", 8, MEMBER[8]), ("member", 17, MEMBER[17]), ("casual", 17, CASUAL[17])))
    rows = "".join(f'<tr><th scope="row">{hour_label(h)}</th><td>{m:,}</td><td>{c:,}</td></tr>'
                   for h, (m, c) in enumerate(zip(MEMBER, CASUAL)))
    return f'''<figure class="fig chart lc" data-member="{",".join(map(str, MEMBER))}" data-casual="{",".join(map(str, CASUAL))}" data-ymax="{ymax}">
          <div class="chart-head">
            <p class="chart-title">Rides by hour of day</p>
            <ul class="chart-legend"><li><i class="key member"></i>Members</li><li><i class="key casual"></i>Casual riders</li></ul>
          </div>
          <div class="lc-body">
            <div class="lc-y" aria-hidden="true"><div class="lc-in">{yticks}</div></div>
            <div class="lc-plot" tabindex="0" role="group" aria-label="Rides by hour of day for members and casual riders. Use the left and right arrow keys to read each hour.">
              <div class="lc-in">
                <svg class="lc-svg" viewBox="0 0 230 100" preserveAspectRatio="none" aria-hidden="true"><g class="lc-grid">{grid}</g><path class="lc-line casual" d="{path(CASUAL)}"/><path class="lc-line member" d="{path(MEMBER)}"/></svg>
                <div aria-hidden="true">{peaks}</div>
                <span class="lc-cross" aria-hidden="true"></span><span class="lc-hdot member" aria-hidden="true"></span><span class="lc-hdot casual" aria-hidden="true"></span>
                <div class="chart-tip lc-tip" role="status" aria-live="polite"></div>
              </div>
            </div>
          </div>
          <div class="lc-x" aria-hidden="true">{xticks}</div>
          <figcaption>Members peak twice, at 8am ({MEMBER[8]:,} rides) and 5pm ({MEMBER[17]:,}); casual riders build to a single peak at 5pm ({CASUAL[17]:,}). <span class="src">Source: Citi Bike System Data, May 2026.</span></figcaption>
          <details class="chart-data"><summary>View data</summary><table><thead><tr><th scope="col">Hour</th><th scope="col">Members</th><th scope="col">Casual riders</th></tr></thead><tbody>{rows}</tbody></table></details>
        </figure>'''


def flow_chart():
    """Diverging bars: average daily bike flow per station, zero in the middle."""
    half = 10  # bikes a day at each end of the axis, leaving room for labels at the bar tips
    rows, table = [], []
    for name, v, days, imb in STATIONS:
        side = "drain" if v > 0 else "surplus"
        n = html.escape(name)
        # bind the last two words so a wrapped name never strands "St" or "1 St" on its own line
        head, _, tail = n.rpartition(" ")
        n_label = f"{head}&nbsp;{tail}" if head else n
        rows.append(
            f'<li class="dv-row {side}" tabindex="0"><span class="dv-name">{n_label}</span>'
            f'<span class="dv-track"><span class="dv-bar {side}" style="--w:{abs(v) / half * 50:.2f}%"><span class="dv-val">{signed(v)}</span></span></span>'
            f'<span class="chart-tip dv-tip" aria-hidden="true"><strong>{signed(v)} bikes a day</strong><span class="tip-name">{n}</span>'
            f'<span>{imb:.1f}% imbalance &middot; {days} qualifying days</span></span></li>')
        table.append(f'<tr><th scope="row">{n}</th><td>{signed(v)}</td><td>{imb:.1f}%</td><td>{days}</td></tr>')
    ticks = "".join(f'<span style="left:{50 + t / half * 50:.2f}%">{"0" if t == 0 else signed(t).rstrip("0").rstrip(".")}</span>'
                    for t in (-10, -5, 0, 5, 10))
    return f'''<figure class="fig chart dv">
          <div class="chart-head">
            <p class="chart-title">Average daily bike flow by station</p>
            <ul class="chart-legend"><li><i class="key drain"></i>Draining (more departures)</li><li><i class="key surplus"></i>Surplus (more arrivals)</li></ul>
          </div>
          <ol class="dv-rows">{"".join(rows)}</ol>
          <div class="dv-axis" aria-hidden="true"><span></span><span class="dv-ticks">{ticks}</span></div>
          <figcaption>Departures minus arrivals, averaged over days with more than 25 rides at stations with at least 6 such days. <span class="src">Source: Citi Bike System Data, May 2026.</span></figcaption>
          <details class="chart-data"><summary>View data</summary><table><thead><tr><th scope="col">Station</th><th scope="col">Bikes a day</th><th scope="col">Imbalance</th><th scope="col">Qualifying days</th></tr></thead><tbody>{"".join(table)}</tbody></table></details>
        </figure>'''


# ---------------------------------------------------------------------------- hero

def ribbon_svg():
    """Stripe-style silk ribbon: a band of even width swept along one centre curve,
    coloured across its width, with faint streaks running along it."""
    spine = [(690, -90), (720, 190), (870, 430), (1180, 640)]
    w0, w1 = 250, 380
    samples = 56

    def point(t):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = spine
        u = 1 - t
        return (u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
                u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3)

    def normal(t):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = spine
        u = 1 - t
        dx = 3 * u * u * (x1 - x0) + 6 * u * t * (x2 - x1) + 3 * t * t * (x3 - x2)
        dy = 3 * u * u * (y1 - y0) + 6 * u * t * (y2 - y1) + 3 * t * t * (y3 - y2)
        n = (dx * dx + dy * dy) ** 0.5
        return (-dy / n, dx / n)

    def offset(t, f):
        (px, py), (nx, ny), w = point(t), normal(t), w0 + (w1 - w0) * t
        return (px + nx * w * f, py + ny * w * f)

    ts = [i / samples for i in range(samples + 1)]
    pts = lambda f: [offset(t, f) for t in ts]
    poly = lambda p: "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in p)
    band = poly(pts(0.5) + pts(-0.5)[::-1]) + "Z"
    streaks = "".join(f'<path d="{poly(pts(0.5 - i / 16))}" stroke-opacity="{0.05 + 0.11 * (1 - abs(0.5 - i / 16) * 2):.2f}"/>'
                      for i in range(1, 16))
    (ax, ay), (bx, by) = offset(0.5, 0.5), offset(0.5, -0.5)
    (sx, sy), (ex, ey) = point(0), point(1)
    return f'''<svg class="ribbon" viewBox="0 0 1040 880" preserveAspectRatio="xMaxYMin slice" aria-hidden="true">
  <defs>
    <linearGradient id="rb" gradientUnits="userSpaceOnUse" x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}">
      <stop offset="0" stop-color="#a9b8ff"/><stop offset=".18" stop-color="#8b7bff"/>
      <stop offset=".4" stop-color="#d36bff"/><stop offset=".6" stop-color="#ff5fae"/>
      <stop offset=".8" stop-color="#ff8a3d"/><stop offset="1" stop-color="#ffc233"/>
    </linearGradient>
    <linearGradient id="rb-sheen" gradientUnits="userSpaceOnUse" x1="{sx:.0f}" y1="{sy:.0f}" x2="{ex:.0f}" y2="{ey:.0f}">
      <stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".75" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <filter id="rb-soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="1.6"/></filter>
  </defs>
  <path d="{band}" fill="url(#rb)" filter="url(#rb-soft)"/>
  <path d="{band}" fill="url(#rb-sheen)"/>
  <g fill="none" stroke="#fff" stroke-width="1.2">{streaks}</g>
</svg>'''


def hero(design, p):
    actions = (f'<div class="hero-actions reveal">'
               f'<a class="btn btn-primary" href="{p}KumarMehul_Resume.pdf" download>Download resume {ARR}</a>'
               f'<a class="btn btn-secondary" href="#contact">Get in touch {ARR}</a></div>')
    links = (f'<ul class="hero-links reveal">'
             f'<li><a href="{LINKS["linkedin"]}" target="_blank" rel="noopener">LinkedIn {ARR}</a></li>'
             f'<li><a href="{LINKS["github"]}" target="_blank" rel="noopener">GitHub {ARR}</a></li>'
             f'<li><a href="{LINKS["email"]}">Email {ARR}</a></li></ul>')

    if design == "stripe":
        return f'''<section class="hero">
  <div class="hero-art">{ribbon_svg()}</div>
  <div class="wrap hero-inner">
    <p class="hero-counter reveal">Trips analyzed in my latest project: <span data-count="94689" data-decimals="0">94,689</span></p>
    <h1 class="hero-title reveal"><span class="t1">Kumar Mehul, Data Analyst.</span> <span class="t2">SQL, Python, Tableau. From raw data to decisions that stick.</span></h1>
    {actions}
    {links}
  </div>
</section>'''

    if design == "linear":
        return f'''<section class="hero">
  <div class="hero-art" aria-hidden="true"></div>
  <div class="wrap hero-inner">
    <a class="hero-pill reveal" href="#projects"><span class="pill-tag">Latest</span>Jersey City last-mile mobility case study {ARR}</a>
    <h1 class="hero-title reveal">Kumar Mehul</h1>
    <p class="hero-sub reveal"><span class="t1">Data Analyst.</span> <span class="t2">SQL, Python, Tableau. From raw data to decisions that stick.</span></p>
    {actions}
    {links}
  </div>
</section>'''

    if design == "vercel":
        return f'''<section class="hero">
  <div class="wrap">
    <div class="hero-frame">
      <i class="plus tl"></i><i class="plus tr"></i><i class="plus bl"></i><i class="plus br"></i>
      <p class="hero-kicker reveal">Data Analyst &middot; India &middot; Open to relocation</p>
      <h1 class="hero-title reveal">Kumar Mehul</h1>
      <p class="hero-sub reveal">SQL, Python, Tableau. From raw data to decisions that stick.</p>
      {actions}
      {links}
    </div>
  </div>
</section>'''

    index = "".join(f'<li><a href="#{sid}"><span class="ix-n">{n:02d}</span>{label}</a></li>'
                    for n, (sid, label) in enumerate(SECTIONS, 1))
    return f'''<section class="hero">
  <div class="wrap">
    <p class="hero-kicker reveal">Portfolio &middot; Data Analysis</p>
    <h1 class="hero-title reveal">Kumar Mehul</h1>
    <p class="hero-dek reveal">Data analyst. SQL, Python, Tableau. From raw data to decisions that stick.</p>
    <p class="hero-byline reveal">India &middot; Open to relocation</p>
    {actions}
    {links}
    <nav class="hero-index reveal" aria-label="In this portfolio"><p class="ix-label">In this portfolio</p><ol>{index}</ol></nav>
  </div>
</section>'''


def stats_band():
    return f'''<section class="stats-band">
  <div class="wrap">
    <dl class="stats reveal">
      {stat("94,689", "CitiBike trips cleaned and analyzed", 94689)}
      {stat("8,000", "foundation records audited", 8000, prefix="~")}
      {stat("8.9", "records in a dimensional warehouse", 8.9, 1, prefix="~", suffix="M")}
      {stat("17", "heterogeneous sources integrated", 17)}
    </dl>
  </div>
</section>'''


# ---------------------------------------------------------------------------- body

ABOUT = '''<section class="section about" id="about">
  <div class="wrap">
    <p class="eyebrow reveal">About</p>
    <p class="statement reveal"><span class="t1">I am a Data Analyst with an MS in Information Systems from Northeastern University, Boston, and hands-on professional experience in data operations and reporting.</span> <span class="t2">My work covers the full analysis cycle - from sourcing and cleaning raw data to building the reporting layer that teams use to make decisions. I work primarily in SQL, Python, and Tableau, with additional experience in Power BI, Alteryx, and Talend across ETL and dimensional modeling workflows.</span></p>
  </div>
</section>'''

EXPERIENCE = f'''<section class="section experience" id="experience">
  <div class="wrap">
    {section_head("Experience", "Grants intelligence, end to end.", "Eight months building, auditing, and enriching a dataset of 8,000 foundations for a grants team.")}
    <article class="xp card reveal">
      <div class="xp-head">
        <div>
          <h3 class="xp-role">Data Analyst</h3>
          <p class="xp-org">Rebecca Everlene Trust Company &middot; Chicago, USA (Remote)</p>
        </div>
        <p class="xp-dates">Oct 2024 - May 2025</p>
      </div>
      <p class="xp-summary">Built a grants intelligence dataset from IRS 990 filings and foundation websites, then audited, gap-analyzed, and enriched it into submission-ready grant packages for the team.</p>
      <dl class="stats stats-3">
        {stat("8,000", "records audited for structural integrity", 8000, prefix="~")}
        {stat("6,300", "foundations segmented across a 12-month grant pipeline", 6300, prefix="~")}
        {stat("80", "of assigned foundations with packages ready before deadlines", 80, prefix="~", suffix="%")}
      </dl>
      <ul class="xp-list">
        <li>Extracted and structured IRS 990 and foundation website data for about 2,000 of the team's 8,000 organization records.</li>
        <li>Audited the full dataset for structural integrity and formatting consistency, resolving field-level inconsistencies across every record.</li>
        <li>Ran a structured gap analysis with a resolution log across multiple review cycles, focusing follow-up on recoverable gaps.</li>
        <li>Built a deadline-driven classification framework that replaced an unstructured process with a team-wide workflow.</li>
      </ul>
    </article>
  </div>
</section>'''


def case(p):
    return f'''<article class="case card reveal" id="citibike">
      <header class="case-head">
        <p class="eyebrow">Featured case study</p>
        <h3 class="case-title">Jersey City Last-Mile Mobility Analysis</h3>
        <p class="case-lede">Which CitiBike stations run out of bikes, when, and for whom? An analysis of 94,689 trips across Jersey City and Hoboken, from raw data to a rebalancing plan.</p>
        <p class="case-meta"><span class="case-dates">Jun 2026 - Jul 2026</span><span class="case-stack">{stack(["PostgreSQL", "Python (pandas, matplotlib, seaborn)", "Tableau"])}</span></p>
      </header>

      <figure class="fig fig-hero">
        <a href="{LINKS["dashboard"]}" target="_blank" rel="noopener"><img src="{p}assets/cb-dashboard.jpg" width="1600" height="1066" loading="lazy" decoding="async" alt="Tableau map of all 108 CitiBike stations in Jersey City and Hoboken, colored by daily net bike flow from surplus (blue) to deficit (orange) and sized by magnitude."></a>
        <figcaption>All 108 stations by average daily bike flow. Color shows direction (drain or surplus), size shows magnitude, and the 27 lower-volume stations use a separate marker. <a href="{LINKS["dashboard"]}" target="_blank" rel="noopener">Open the live dashboard {ARR}</a></figcaption>
      </figure>

      <dl class="stats stats-4">
        {stat("94,689", "verified trips", 94689)}
        {stat("108", "stations mapped", 108)}
        {stat("10", "priority stations", 10)}
        {stat("17.8", "peak daily imbalance", 17.8, 1, suffix="%")}
      </dl>

      <div class="case-cols">
        <section class="case-block">
          <h4>The question</h4>
          <p>How do CitiBike usage patterns in the Jersey City area reveal opportunities to better serve commuter and recreational demand?</p>
        </section>
        <section class="case-block">
          <h4>The approach</h4>
          <p>Cleaned 95,350 raw trips in pandas, removing 355 null records and 306 cross-system rides to leave 94,689. Built reusable PostgreSQL views for each station's daily bike flow and imbalance, kept low-volume noise out of the rankings with a reliability filter (more than 25 daily rides on at least 6 of 31 days), and published a Tableau map of every station.</p>
        </section>
      </div>

      <section class="finding">
        <div class="finding-text">
          <p class="finding-n">Finding 01</p>
          <h4>Members commute. Casual riders don't.</h4>
          <p>Members take short trips at high volume nearly all day, with peaks in the morning and evening. Casual riders ride longer and build to a single evening peak, with no morning spike at all.</p>
          <div class="duo" role="img" aria-label="Average ride length: members 8 minutes, casual riders 15 minutes.">
            <div class="duo-row"><span class="duo-label">Member</span><span class="duo-bar"><i class="member" style="--w:53.3%"></i></span><span class="duo-val">8 min</span></div>
            <div class="duo-row"><span class="duo-label">Casual</span><span class="duo-bar"><i class="casual" style="--w:100%"></i></span><span class="duo-val">15 min</span></div>
            <p class="duo-note">Average ride length</p>
          </div>
        </div>
        {hourly_chart()}
      </section>

      <section class="finding finding-wide">
        <div class="finding-text">
          <p class="finding-n">Finding 02</p>
          <h4>Bike drain concentrates in one corridor.</h4>
          <p>Oakland Ave, McGinley Square, and Glenwood Ave lose the most bikes every day, and the draining stations cluster in a single Jersey City corridor. Surplus stations such as River St &amp; Newark St and City Hall split evenly across both cities.</p>
        </div>
        {flow_chart()}
      </section>

      <section class="case-block reco">
        <h4>The recommendation</h4>
        <p>Split rebalancing by city, not by operation type. Every draining and surplus station sorts cleanly into Jersey City or Hoboken, so one route per city covers the whole problem without cross-city travel. Shared transit hubs like Grove St PATH should be sized for peak-hour capacity, not all-day demand.</p>
      </section>

      <aside class="callout">
        <p class="callout-label">How the numbers were checked</p>
        <p>I used Claude as an independent code reviewer to reproduce the results. It surfaced a NULL-handling bug and a sign error affecting 44 of 81 stations, both fixed before publishing.</p>
      </aside>

      <p class="case-links">
        <a class="btn btn-primary" href="{LINKS["dashboard"]}" target="_blank" rel="noopener">Open live dashboard {ARR}</a>
        <a class="btn btn-secondary" href="{LINKS["citibike"]}" target="_blank" rel="noopener">View repository {ARR}</a>
      </p>
    </article>'''


def mini(p, key, dates, title, items, desc, chips, img, w, h, alt, caption):
    chip_html = "".join(f"<li>{c}</li>" for c in chips)
    return f'''<article class="mini card reveal">
        <figure class="fig mini-fig"><img src="{p}assets/{img}" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}"><figcaption>{caption}</figcaption></figure>
        <div class="mini-body">
          <p class="mini-meta">{dates}</p>
          <h3 class="mini-title">{title}</h3>
          <p class="mini-stack">{stack(items)}</p>
          <p class="mini-desc">{desc}</p>
          <ul class="chips">{chip_html}</ul>
          <a class="text-link" href="{LINKS[key]}" target="_blank" rel="noopener">View repository {ARR}</a>
        </div>
      </article>'''


def projects(p):
    imdb = mini(p, "imdb", "Dec 2023 - Apr 2024", "IMDB Movie Data Analysis",
                ["Alteryx", "Talend", "Tableau", "Azure SQL", "E/R Studio"],
                "Built Talend jobs to load about 1 million source records from 17 heterogeneous sources into a 12-table dimensional model on Azure SQL, expanding many-to-many relationships into a warehouse of about 8.9 million records. Designed the model in E/R Studio, profiled and validated all source data in Alteryx, and built Tableau dashboards covering genre-level rating and revenue patterns, multi-year output and rating trends, seasonal release performance, and multi-region release footprint.",
                ["~1M source records", "17 sources", "~8.9M-record warehouse", "12 tables"],
                "imdb-model.png", 1219, 762,
                "E/R Studio logical model of the IMDB warehouse with dimension, fact and bridge tables.",
                "The 12-table dimensional model in E/R Studio: 6 dimensions, 2 fact tables, and 4 bridge tables.")
    food = mini(p, "food", "Oct 2023 - Nov 2023", "California Food Inspection Analysis",
                ["Alteryx", "Talend", "Tableau", "Azure SQL", "MySQL", "E/R Studio"],
                "Built a compliance analytics system for Sonoma County food facility inspections. Designed a 5-table star schema, profiled and cleansed source data in Alteryx, loaded into Azure SQL via Talend, and built Tableau dashboards covering inspection trends, pass/fail analysis, violation category breakdowns, and geographic risk distribution.",
                ["5-table star schema", "Sonoma County", "Tableau dashboards"],
                "food-model.png", 956, 697,
                "E/R Studio star schema with business, date and violation dimensions around inspection fact tables.",
                "The 5-table star schema: 3 dimensions and 2 fact tables around inspections and violations.")
    return f'''<section class="section projects" id="projects">
  <div class="wrap">
    {section_head("Projects", "From raw data to decisions.", "Three end-to-end analyses across mobility, entertainment, and food safety data.")}
    {case(p)}
    <div class="mini-grid">
      {imdb}
      {food}
    </div>
  </div>
</section>'''


def skill(title, tools, subs):
    pills = "".join(f"<li>{t}</li>" for t in tools)
    sub = " &middot; ".join(f"<span>{s}</span>" for s in subs)
    return (f'<div class="skill reveal"><h3 class="skill-title">{title}</h3>'
            f'<ul class="pills">{pills}</ul><p class="skill-subs">{sub}</p></div>')


SKILLS = f'''<section class="section skills" id="skills">
  <div class="wrap">
    {section_head("Skills", "The toolkit.", "What I use, and what I use it for.")}
    <div class="skills-grid">
      {skill("Analytics &amp; Visualization", ["Tableau", "Power BI"], ["Business intelligence", "Dashboards", "KPIs", "Drill-downs", "Ad-hoc analysis", "Data storytelling"])}
      {skill("Languages &amp; Querying", ["SQL", "Python", "pandas", "matplotlib", "seaborn"], ["Data manipulation", "Data cleaning", "Querying", "Exploratory data analysis"])}
      {skill("Data Preparation", ["Alteryx", "Talend"], ["ETL", "Data profiling", "Data transformation", "Data integration", "Data quality"])}
      {skill("Databases", ["PostgreSQL", "SQL Server", "Azure SQL", "MySQL", "E/R Studio"], ["Relational databases", "Dimensional modeling", "Data warehousing", "Data modeling"])}
    </div>
  </div>
</section>'''

EDUCATION = f'''<section class="section education" id="education">
  <div class="wrap">
    {section_head("Education", "Education.")}
    <ol class="edu">
      <li class="edu-item reveal"><div><h3 class="edu-degree">Master of Science in Information Systems</h3><p class="edu-school">Northeastern University, Boston, USA</p></div><p class="edu-dates">Sep 2022 - May 2024</p></li>
      <li class="edu-item reveal"><div><h3 class="edu-degree">Bachelor of Technology in Information Technology</h3><p class="edu-school">SRM Institute of Science and Technology, Chennai, India</p></div><p class="edu-dates">Jul 2016 - May 2020</p></li>
    </ol>
  </div>
</section>'''

CONTACT = '''<section class="section contact" id="contact">
  <div class="wrap">
    <header class="section-head contact-head reveal">
      <p class="eyebrow">Contact</p>
      <h2 class="section-title"><span class="t1">Get in Touch</span></h2>
      <p class="contact-sub"><span>Hiring an analyst, or sitting on data that needs answers?</span> <span>Tell me about it.<br class="br-mobile"> I read every message.</span></p>
    </header>
    <form class="contact-form card reveal" id="contact-form" action="https://formsubmit.co/4828c43603eda8bb09f2faaca6532157" method="POST">
      <input type="hidden" name="_subject" value="New message from kmehul.github.io">
      <input type="hidden" name="_captcha" value="false">
      <input type="hidden" name="_next" value="https://kmehul.github.io/#contact">
      <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">
      <label class="field"><span class="field-label">Name</span><input type="text" id="cf-name" name="name" autocomplete="name" required></label>
      <label class="field"><span class="field-label">Email</span><input type="email" id="cf-email" name="email" autocomplete="email" required></label>
      <label class="field"><span class="field-label">Message</span><textarea id="cf-message" name="message" required></textarea></label>
      <div class="form-foot">
        <button class="btn btn-primary" type="submit">Send message</button>
        <p class="form-status" id="form-status" role="status"></p>
      </div>
    </form>
  </div>
</section>'''


def footer(p):
    return f'''<footer class="footer">
  <div class="wrap footer-inner">
    <p>&copy; 2026 Kumar Mehul &middot; India &middot; Open to relocation</p>
    <ul class="footer-links">
      <li><a href="{LINKS["linkedin"]}" target="_blank" rel="noopener">LinkedIn</a></li>
      <li><a href="{LINKS["github"]}" target="_blank" rel="noopener">GitHub</a></li>
      <li><a href="{LINKS["email"]}">Email</a></li>
      <li><a href="{p}KumarMehul_Resume.pdf" download>Resume</a></li>
    </ul>
  </div>
</footer>'''


def nav(p):
    links = "".join(f'<a href="#{sid}">{label}</a>' for sid, label in SECTIONS)
    return f'''<header class="nav" id="nav">
  <div class="wrap nav-inner">
    <a class="brand" href="#top">Kumar Mehul</a>
    <nav class="nav-menu" id="nav-menu" aria-label="Sections">{links}</nav>
    <div class="nav-actions">
      <a class="btn btn-primary btn-sm nav-cta" href="{p}KumarMehul_Resume.pdf" download>Resume {ARR}</a>
      <button class="nav-toggle" id="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="nav-menu"><span></span><span></span></button>
    </div>
  </div>
</header>'''


PREVIEW_BADGE = '''<a class="preview-badge" href="index.html" style="position:fixed;left:16px;bottom:16px;z-index:200;display:inline-flex;align-items:center;gap:8px;padding:8px 14px;border-radius:999px;background:rgba(17,17,17,.88);color:#fff;font:500 13px/1 -apple-system,system-ui,sans-serif;text-decoration:none;box-shadow:0 6px 20px rgba(0,0,0,.18)">Design preview: {label} &middot; All options</a>'''


def page(key, preview=False):
    d = DESIGNS[key]
    p = "../" if preview else ""
    count = ' data-count="off"' if d.get("no_count") else ""
    favicon = (f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' "
               f"height='100' rx='22' fill='{d['accent']}'/%3E%3Ctext x='50' y='66' font-size='44' "
               f"font-family='-apple-system,sans-serif' font-weight='600' fill='white' text-anchor='middle'%3EKM%3C/text%3E%3C/svg%3E")
    robots = ('\n  <meta name="robots" content="noindex, nofollow">\n  <link rel="canonical" href="https://kmehul.github.io/">'
              if preview else "")
    guides = '<div class="guides" aria-hidden="true"><i></i><i></i><i></i></div>\n' if key == "stripe" else ""
    badge = PREVIEW_BADGE.format(label=d["label"]) + "\n" if preview else ""
    return f'''<!DOCTYPE html>
<!-- Generated by tools/build.py ({key} design). Edit the script, not this file. -->
<html lang="en" data-design="{key}"{count}>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kumar Mehul - Data Analyst</title>
  <meta name="description" content="Kumar Mehul - Data Analyst. SQL, Python, Tableau. From raw data to decisions that stick.">{robots}
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://kmehul.github.io/">
  <meta property="og:title" content="Kumar Mehul - Data Analyst">
  <meta property="og:description" content="SQL, Python, Tableau. From raw data to decisions that stick.">
  <meta property="og:image" content="https://kmehul.github.io/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Kumar Mehul - Data Analyst">
  <meta name="twitter:description" content="SQL, Python, Tableau. From raw data to decisions that stick.">
  <meta name="twitter:image" content="https://kmehul.github.io/og-image.png">
  <link rel="icon" href="{favicon}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{d['fonts']}">
  <link rel="stylesheet" href="{p}css/base.css">
  <link rel="stylesheet" href="{p}css/{key}.css">
</head>
<body>
{guides}{nav(p)}
<main id="top">
{hero(key, p)}
{stats_band()}
{ABOUT}
{EXPERIENCE}
{projects(p)}
{SKILLS}
{EDUCATION}
{CONTACT}
</main>
{footer(p)}
{badge}<script src="{p}js/site.js"></script>
</body>
</html>
'''


def chooser(live):
    cards = "".join(
        f'<a class="opt{" live" if k == live else ""}" href="{k}.html"><span class="n">{d["label"]}'
        f'{" <em>Live</em>" if k == live else ""}</span><span class="note">{d["note"]}</span></a>'
        for k, d in DESIGNS.items())
    return f'''<!DOCTYPE html>
<!-- Generated by tools/build.py. -->
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow"><title>Design options - Kumar Mehul</title><style>
body{{margin:0;font:16px/1.5 -apple-system,system-ui,sans-serif;background:#f5f5f7;color:#1d1d1f;padding:56px 20px}}
h1{{font-size:28px;margin:0 0 6px;text-align:center}}p.sub{{text-align:center;color:#6e6e73;margin:0 0 28px}}
.grid{{max-width:760px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
.opt{{display:block;background:#fff;border-radius:14px;padding:20px;text-decoration:none;color:inherit;border:1px solid #e5e5ea}}
.opt:hover{{border-color:#0071e3}}.opt.live{{border-color:#1d1d1f}}.n{{display:block;font-size:19px;font-weight:600}}
.n em{{font-style:normal;font-size:11px;font-weight:600;background:#1d1d1f;color:#fff;border-radius:999px;padding:2px 8px;vertical-align:3px;margin-left:6px}}
.note{{display:block;color:#6e6e73;font-size:14px;margin-top:4px}}a.back{{display:block;text-align:center;margin-top:28px;color:#0071e3;text-decoration:none}}</style></head>
<body><h1>Design options</h1><p class="sub">Same content, four design languages. The live site uses the one marked Live.</p>
<div class="grid">{cards}</div><a class="back" href="../">Back to the live site</a></body></html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", choices=DESIGNS, help="switch the live design and remember the choice")
    args = ap.parse_args()
    live = LIVE
    if args.live and args.live != LIVE:
        live = args.live
        me = Path(__file__)
        me.write_text(re.sub(r'^LIVE = "\w+"$', f'LIVE = "{live}"', me.read_text(), count=1, flags=re.M))
    (ROOT / "index.html").write_text(page(live))
    (ROOT / "designs").mkdir(exist_ok=True)
    for key in DESIGNS:
        (ROOT / "designs" / f"{key}.html").write_text(page(key, preview=True))
    (ROOT / "designs" / "index.html").write_text(chooser(live))
    print(f"live design: {live}  |  built index.html, designs/index.html, designs/{{{','.join(DESIGNS)}}}.html")


if __name__ == "__main__":
    main()
