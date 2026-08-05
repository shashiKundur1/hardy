(function () {
  var script = document.currentScript;
  var endpoint = script.dataset.endpoint;
  var batchSize = Number(script.dataset.batchSize);
  var flushMs = Number(script.dataset.flushMs);
  var debounceMs = Number(script.dataset.debounceMs);
  var path = location.pathname;

  var queue = [];
  var timer = null;
  var searchTimer = null;
  var dwellSent = false;
  var openedAt = Date.now();

  function send(useBeacon) {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    if (queue.length === 0) {
      return;
    }
    var body = JSON.stringify({ events: queue });
    queue = [];
    if (useBeacon && navigator.sendBeacon) {
      navigator.sendBeacon(endpoint, new Blob([body], { type: "application/json" }));
      return;
    }
    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body,
      keepalive: true,
credentials: "same-origin"
    }).catch(function () {});
  }

  function push(event) {
    event.path = path;
    queue.push(event);
    if (queue.length >= batchSize) {
      send(false);
      return;
    }
    if (timer === null) {
      timer = setTimeout(function () {
        send(false);
      }, flushMs);
    }
  }

  function track(type, detail) {
    var event = detail || {};
    event.type = type;
    push(event);
  }

  function leave() {
    if (!dwellSent) {
      dwellSent = true;
      queue.push({
        type: "dwell",
        path: path,
        dwell_ms: Date.now() - openedAt,
        product_id: Number(document.body.dataset.productId) || null,
        category: document.body.dataset.category || null
      });
    }
    send(true);
  }

  track("page_view", {
    product_id: Number(document.body.dataset.productId) || null,
    category: document.body.dataset.category || null
  });

  if (document.body.dataset.productId) {
    track("product_view", {
      product_id: Number(document.body.dataset.productId),
      category: document.body.dataset.category || null
    });
  }

  document.addEventListener("click", function (moment) {
    var target = moment.target.closest("[data-track]");
    if (!target) {
      return;
    }
    track("click", {
      product_id: Number(target.dataset.productId) || null,
      category: target.dataset.category || null,
      query: target.dataset.track
    });
  });

  document.addEventListener("input", function (moment) {
    var field = moment.target;
    if (field.type !== "search") {
      return;
    }
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      var value = field.value.trim();
      if (value) {
        track("search", { query: value });
      }
    }, debounceMs);
  });

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") {
      leave();
    }
  });

  window.addEventListener("pagehide", leave);
})();
