(() => {
  const data = JSON.parse(document.getElementById('geodiff-data').textContent);
  const tabs = setupTabs();
  const mapView = data.map ? setupMap(data.map) : null;
  setupSelection(tabs, mapView);

  function setupTabs() {
    const buttons = document.querySelectorAll('.tabs button');
    const panels = document.querySelectorAll('.table-panel');
    function select(table) {
      for (const b of buttons) b.setAttribute('aria-selected', b.dataset.table === table ? 'true' : 'false');
      for (const p of panels) p.hidden = p.dataset.table !== table;
    }
    for (const b of buttons) b.addEventListener('click', () => select(b.dataset.table));
    return { select };
  }

  function setupMap(mapData) {
    class LayerControl {
      constructor(layers, layerIds) {
        this.layers = layers;
        this.layerIds = layerIds;
      }

      onAdd(map) {
        const el = document.createElement('div');
        el.className = 'maplibregl-ctrl maplibregl-ctrl-group layer-control';
        for (const l of this.layers) {
          const cb = document.createElement('input');
          cb.type = 'checkbox';
          cb.checked = true;
          cb.addEventListener('change', () => {
            const v = cb.checked ? 'visible' : 'none';
            for (const id of this.layerIds[l.table]) {
              map.setLayoutProperty(id, 'visibility', v);
            }
          });
          const label = document.createElement('label');
          label.append(cb, ' ', l.table);
          el.append(label);
        }
        this.el = el;
        return el;
      }

      onRemove() {
        this.el.remove();
      }
    }

    const STYLE = {
      point: [
        ['circle', 'before', { 'circle-color': '#cf222e', 'circle-radius': 7, 'circle-opacity': 0.5 }],
        ['circle', 'after',  { 'circle-color': '#20dd5b', 'circle-radius': 4 }],
      ],
      line: [
        ['line', 'before', { 'line-color': '#cf222e', 'line-width': 8, 'line-opacity': 0.5 }],
        ['line', 'after',  { 'line-color': '#20dd5b', 'line-width': 4 }],
      ],
      polygon: [
        ['fill', 'before', { 'fill-color': '#cf222e', 'fill-opacity': 0.2 }],
        ['line', 'before', { 'line-color': '#cf222e', 'line-width': 3, 'line-opacity': 0.6 }],
        ['fill', 'after',  { 'fill-color': '#20dd5b', 'fill-opacity': 0.2 }],
        ['line', 'after',  { 'line-color': '#20dd5b', 'line-width': 1.5 }],
      ],
    };

    const HIGHLIGHT = {
      point:   [['circle', { 'circle-radius': 11, 'circle-opacity': 0,
                             'circle-stroke-color': '#0969da', 'circle-stroke-width': 3 }]],
      line:    [['line',   { 'line-color': '#0969da', 'line-width': 2, 'line-gap-width': 10 }]],
      polygon: [['line',   { 'line-color': '#0969da', 'line-width': 3 }]],
    };

    const ORDER = { polygon: 0, line: 1, point: 2 };
    const layerIds = {};
    const hlIds = [];

    const map = new maplibregl.Map({
      container: 'map',
      style: mapData.basemap,
      center: [0, 0],
      zoom: 1,
    });

    function eachCoord(coords, fn) {
      if (typeof coords[0] === 'number') fn(coords);
      else for (const c of coords) eachCoord(c, fn);
    }

    // Build feature index: index[table][String(pk)] = [feature, ...]
    const index = {};
    for (const l of mapData.layers)
      for (const fc of [l.before, l.after])
        for (const f of fc.features)
          ((index[l.table] ??= {})[String(f.properties.pk)] ??= []).push(f);

    let ready = false;

    map.on('load', () => {
      const layers = [...mapData.layers].sort((a, b) => ORDER[a.kind] - ORDER[b.kind]);
      for (const l of layers) {
        map.addSource(`${l.table}:before`, { type: 'geojson', data: l.before });
        map.addSource(`${l.table}:after`,  { type: 'geojson', data: l.after });
        layerIds[l.table] = [];
        STYLE[l.kind].forEach(([type, side, paint], i) => {
          const id = `${l.table}:${side}:${type}:${i}`;
          map.addLayer({ id, type, source: `${l.table}:${side}`, paint });
          layerIds[l.table].push(id);
        });
      }

      // Add highlight layers on top of all regular layers
      for (const l of layers) {
        for (const side of ['before', 'after']) {
          HIGHLIGHT[l.kind].forEach(([type, paint], i) => {
            const id = `${l.table}:${side}:highlight:${i}`;
            map.addLayer({ id, type, source: `${l.table}:${side}`, paint,
                           layout: { visibility: 'none' } });
            hlIds.push({ id, table: l.table });
          });
        }
      }

      map.addControl(new LayerControl(mapData.layers, layerIds), 'top-right');

      const bounds = new maplibregl.LngLatBounds();
      for (const l of mapData.layers)
        for (const fc of [l.before, l.after])
          for (const f of fc.features)
            eachCoord(f.geometry.coordinates, c => bounds.extend(c));
      if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 40 });

      ready = true;
    });

    function highlight(table, pk) {
      if (!ready) return;
      for (const { id, table: t } of hlIds) {
        if (t === table) {
          map.setFilter(id, ['==', ['to-string', ['get', 'pk']], pk]);
          map.setLayoutProperty(id, 'visibility', 'visible');
        } else {
          map.setLayoutProperty(id, 'visibility', 'none');
        }
      }
      const feats = index[table]?.[pk] ?? [];
      const b = new maplibregl.LngLatBounds();
      for (const f of feats) eachCoord(f.geometry.coordinates, c => b.extend(c));
      if (!b.isEmpty()) map.fitBounds(b, { padding: 80, maxZoom: 18 });
    }

    function clear() {
      if (!ready) return;
      for (const { id } of hlIds) map.setLayoutProperty(id, 'visibility', 'none');
    }

    return { highlight, clear };
  }

  function setupSelection(tabs, mapView) {
    for (const tr of document.querySelectorAll('tr[data-pk]')) {
      tr.addEventListener('click', () => {
        const { table, pk } = tr.dataset;
        for (const r of document.querySelectorAll('tr.selected')) r.classList.remove('selected');
        const rows = document.querySelectorAll(
          `tr[data-table="${CSS.escape(table)}"][data-pk="${CSS.escape(pk)}"]`);
        for (const r of rows) r.classList.add('selected');
        tabs.select(table);
        mapView?.highlight(table, pk);
      });
    }
  }
})();
