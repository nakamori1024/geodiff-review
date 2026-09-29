(() => {
  const data = JSON.parse(document.getElementById('geodiff-data').textContent);
  const tabs = setupTabs();
  const mapView = data.map ? setupMap(data.map) : null;
  const selection = setupSelection(tabs, mapView);
  if (mapView) mapView.bindSelection(selection);

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
      point: {
        before: [['circle', { 'circle-color': '#ff6666', 'circle-radius': 10, 'circle-opacity': 0.8 }]],
        after:  [['circle', { 'circle-color': '#66ff66', 'circle-radius': 7 }]],
      },
      line: {
        before: [['line', { 'line-color': '#ff6666', 'line-width': 10, 'line-opacity': 0.8 }]],
        after:  [['line', { 'line-color': '#66ff66', 'line-width': 6 }]],
      },
      polygon: {
        before: [
          ['fill', { 'fill-color': '#ff6666', 'fill-opacity': 0.35 }],
          ['line', { 'line-color': '#ff6666', 'line-width': 4, 'line-opacity': 0.9 }],
        ],
        after: [
          ['fill', { 'fill-color': '#66ff66', 'fill-opacity': 0.35 }],
          ['line', { 'line-color': '#66ff66', 'line-width': 2.5 }],
        ],
      },
    };

    const ORDER = { polygon: 0, line: 1, point: 2 };
    const layerIds = {};
    const hlIds = [];
    const regularIds = [];

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
          regularIds.push(id);
        });
      }

      // Add highlight layers on top of all regular layers
      for (const l of layers) {
        for (const side of ['before', 'after']) {
          HIGHLIGHT[l.kind][side].forEach(([type, paint], i) => {
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

    function highlight(table, pk, { zoom = true } = {}) {
      if (!ready) return;
      for (const { id, table: t } of hlIds) {
        if (t === table) {
          map.setFilter(id, ['==', ['to-string', ['get', 'pk']], pk]);
          map.setLayoutProperty(id, 'visibility', 'visible');
        } else {
          map.setLayoutProperty(id, 'visibility', 'none');
        }
      }
      if (zoom) {
        const feats = index[table]?.[pk] ?? [];
        const b = new maplibregl.LngLatBounds();
        for (const f of feats) eachCoord(f.geometry.coordinates, c => b.extend(c));
        if (!b.isEmpty()) map.fitBounds(b, { padding: 80, maxZoom: 18 });
      }
    }

    function clear() {
      if (!ready) return;
      for (const { id } of hlIds) map.setLayoutProperty(id, 'visibility', 'none');
    }

    function bindSelection(selection) {
      map.on('click', (e) => {
        if (!ready) return;
        const features = map.queryRenderedFeatures(e.point, { layers: regularIds });
        if (features.length === 0) {
          selection.clear();
          return;
        }
        const f = features[0];
        const table = f.properties.table;
        const pk = String(f.properties.pk);
        selection.select(table, pk, { zoom: false, scroll: true });
      });
    }

    return { highlight, clear, bindSelection };
  }

  function setupSelection(tabs, mapView) {
    function select(table, pk, { zoom = true, scroll = false } = {}) {
      for (const r of document.querySelectorAll('tr.selected')) r.classList.remove('selected');
      const rows = document.querySelectorAll(
        `tr[data-table="${CSS.escape(table)}"][data-pk="${CSS.escape(pk)}"]`);
      for (const r of rows) r.classList.add('selected');
      tabs.select(table);
      mapView?.highlight(table, pk, { zoom });
      if (scroll && rows.length) rows[0].scrollIntoView({ block: 'center' });
    }

    function clear() {
      for (const r of document.querySelectorAll('tr.selected')) r.classList.remove('selected');
      mapView?.clear();
    }

    for (const tr of document.querySelectorAll('tr[data-pk]')) {
      tr.addEventListener('click', () => select(tr.dataset.table, tr.dataset.pk));
    }

    return { select, clear };
  }
})();
