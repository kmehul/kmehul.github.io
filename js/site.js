(function () {
  var root = document.documentElement;
  root.classList.add('js');

  // ---- Contact form: send via FormSubmit AJAX, fall back to an inline mailto link
  var form = document.getElementById('contact-form');
  if (form) {
    var status = document.getElementById('form-status');
    var button = form.querySelector('[type="submit"]');
    var buttonLabel = button.textContent;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = document.getElementById('cf-name').value;
      var email = document.getElementById('cf-email').value;
      var message = document.getElementById('cf-message').value;

      button.disabled = true;
      button.textContent = 'Sending…';
      status.textContent = '';
      status.className = 'form-status';

      fetch('https://formsubmit.co/ajax/4828c43603eda8bb09f2faaca6532157', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({
          name: name,
          email: email,
          message: message,
          _replyto: email,
          _subject: 'Portfolio contact from ' + name,
          _template: 'table'
        })
      }).then(function (res) {
        return res.json();
      }).then(function (data) {
        if (data.success === 'true' || data.success === true) {
          form.reset();
          status.textContent = 'Message sent. Thank you!';
          status.classList.add('success');
        } else {
          throw new Error(data.message || 'Send failed');
        }
      }).catch(function () {
        var subject = encodeURIComponent('Portfolio contact from ' + name);
        var body = encodeURIComponent('Name: ' + name + '\nEmail: ' + email + '\n\n' + message);
        var href = 'mailto:kumar-mehul_1@outlook.com?subject=' + subject + '&body=' + body;
        status.innerHTML = 'Could not send right now - <a href="' + href + '">email me directly</a> instead.';
        status.classList.add('error');
      }).finally(function () {
        button.disabled = false;
        button.textContent = buttonLabel;
      });
    });
  }

  // ---- Mobile nav: persistent bar with a hamburger that opens a full menu
  var nav = document.getElementById('nav');
  var toggle = document.getElementById('nav-toggle');

  function setMenu(open) {
    nav.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.classList.toggle('menu-open', open);
  }

  toggle.addEventListener('click', function () {
    setMenu(!nav.classList.contains('open'));
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setMenu(false);
  });

  // Designs that change the bar once the page moves (border, tint)
  function markScrolled() {
    nav.classList.toggle('scrolled', window.scrollY > 8);
  }
  markScrolled();
  window.addEventListener('scroll', markScrolled, { passive: true });

  // ---- Scroll reveal. Symmetric: any exit re-arms the element, so reveals
  // replay on every pass through the viewport, scrolling down or up
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        entry.target.classList.toggle('in-view', entry.isIntersecting);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    for (var j = 0; j < revealEls.length; j++) io.observe(revealEls[j]);
  } else {
    for (var k = 0; k < revealEls.length; k++) revealEls[k].classList.add('in-view');
  }

  // ---- Line chart hover layer: a crosshair snaps to the nearest hour and one
  // tooltip lists both series. Keyboard: focus the plot, then arrow keys.
  function hourLabel(h) {
    return h === 0 ? '12am' : h < 12 ? h + 'am' : h === 12 ? '12pm' : (h - 12) + 'pm';
  }
  var lineCharts = document.querySelectorAll('.lc');
  for (var lci = 0; lci < lineCharts.length; lci++) (function (fig) {
    var series = [
      { key: 'member', name: 'Members', vals: fig.getAttribute('data-member').split(',').map(Number) },
      { key: 'casual', name: 'Casual riders', vals: fig.getAttribute('data-casual').split(',').map(Number) }
    ];
    var ymax = Number(fig.getAttribute('data-ymax'));
    var last = series[0].vals.length - 1;
    var plot = fig.querySelector('.lc-plot');
    var area = plot.querySelector('.lc-in');
    var cross = fig.querySelector('.lc-cross');
    var tip = fig.querySelector('.lc-tip');
    var dots = {
      member: fig.querySelector('.lc-hdot.member'),
      casual: fig.querySelector('.lc-hdot.casual')
    };
    var current = -1;

    function show(h) {
      current = h;
      var pct = h / last * 100;
      cross.style.left = pct + '%';
      tip.textContent = '';
      var head = document.createElement('p');
      head.className = 'tip-head';
      head.textContent = hourLabel(h);
      tip.appendChild(head);
      series.forEach(function (s) {
        var dot = dots[s.key];
        dot.style.left = pct + '%';
        dot.style.top = (100 - s.vals[h] / ymax * 100) + '%';
        var row = document.createElement('p');
        row.className = 'tip-row';
        var key = document.createElement('i');
        key.className = 'tip-key ' + s.key;
        var val = document.createElement('strong');
        val.textContent = s.vals[h].toLocaleString('en-US');
        var name = document.createElement('span');
        name.textContent = s.name;
        row.appendChild(key);
        row.appendChild(val);
        row.appendChild(name);
        tip.appendChild(row);
      });
      fig.classList.add('is-active');
      // keep the tooltip inside the chart: right of the crosshair, else left of it
      var w = area.clientWidth, x = w * pct / 100, tw = tip.offsetWidth;
      var left = x + 14 + tw <= w ? x + 14 : x - 14 - tw;
      tip.style.left = Math.max(0, Math.min(w - tw, left)) + 'px';
    }
    function hide() {
      fig.classList.remove('is-active');
    }
    function hourAt(e) {
      var r = area.getBoundingClientRect();
      return Math.max(0, Math.min(last, Math.round((e.clientX - r.left) / r.width * last)));
    }

    plot.addEventListener('pointermove', function (e) { show(hourAt(e)); });
    plot.addEventListener('pointerdown', function (e) { show(hourAt(e)); });
    plot.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') hide(); });
    plot.addEventListener('focus', function () { show(current < 0 ? 17 : current); });
    plot.addEventListener('blur', hide);
    plot.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        var step = e.key === 'ArrowRight' ? 1 : -1;
        show(Math.max(0, Math.min(last, (current < 0 ? 17 : current) + step)));
      } else if (e.key === 'Escape') {
        plot.blur();
      }
    });
    document.addEventListener('pointerdown', function (e) {
      if (!plot.contains(e.target)) hide();
    });
  })(lineCharts[lci]);

  // ---- Numbers count up once, the first time they scroll into view.
  // Without JS (or with reduced motion) the final value is already in the markup
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (root.getAttribute('data-count') !== 'off' && !reduceMotion && 'IntersectionObserver' in window) {
    var fmt = function (v, d) {
      return v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
    };
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        cio.unobserve(el);
        var end = parseFloat(el.getAttribute('data-count'));
        var d = parseInt(el.getAttribute('data-decimals') || '0', 10);
        var t0 = null;
        function step(t) {
          if (!t0) t0 = t;
          var p = Math.min((t - t0) / 1400, 1);
          el.textContent = fmt(end * (1 - Math.pow(1 - p, 3)), d);
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    var counters = document.querySelectorAll('span[data-count]');
    for (var c = 0; c < counters.length; c++) cio.observe(counters[c]);
  }

  // Reveal everything above a document position instantly, no animation.
  // Used for anchor jumps and hash loads so content is never invisible on arrival
  function completeRevealsAbove(docY) {
    root.classList.add('no-anim');
    for (var m = 0; m < revealEls.length; m++) {
      var el = revealEls[m];
      if (el.getBoundingClientRect().top + window.scrollY <= docY) el.classList.add('in-view');
    }
    void root.offsetHeight;
    root.classList.remove('no-anim');
  }

  // In-page links scroll without writing a hash into the URL, so a later
  // reload always starts at the top instead of the last-visited section
  var anchors = document.querySelectorAll('a[href^="#"]');
  for (var i = 0; i < anchors.length; i++) {
    anchors[i].addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      setMenu(false);
      completeRevealsAbove(target.getBoundingClientRect().top + window.scrollY + window.innerHeight);
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  // Reloads start at the top like a fresh visit; hash URLs land with
  // everything through the target already revealed
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  function settleHashReveal() {
    if (!location.hash) return;
    var hashTarget = document.querySelector(location.hash);
    if (!hashTarget) return;
    completeRevealsAbove(hashTarget.getBoundingClientRect().top + window.scrollY + window.innerHeight);
    // manual scrollRestoration also suppresses the browser's own fragment jump
    hashTarget.scrollIntoView({ behavior: 'instant', block: 'start' });
  }
  settleHashReveal();
  window.addEventListener('load', settleHashReveal);
})();
