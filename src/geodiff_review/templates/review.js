(() => {
  const data = JSON.parse(document.getElementById('geodiff-data').textContent);
  if (!data.map) return;

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

  const ORDER = { polygon: 0, line: 1, point: 2 };
  const layerIds = {};

  const map = new maplibregl.Map({
    container: 'map',
    style: data.map.basemap,
    center: [0, 0],
    zoom: 1,
  });

  function eachCoord(coords, fn) {
    if (typeof coords[0] === 'number') fn(coords);
    else for (const c of coords) eachCoord(c, fn);
  }

  map.on('load', () => {
    const layers = [...data.map.layers].sort((a, b) => ORDER[a.kind] - ORDER[b.kind]);
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

    map.addControl(new LayerControl(data.map.layers, layerIds), 'top-right');

    const bounds = new maplibregl.LngLatBounds();
    for (const l of data.map.layers)
      for (const fc of [l.before, l.after])
        for (const f of fc.features)
          eachCoord(f.geometry.coordinates, c => bounds.extend(c));
    if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 40 });
  });
})();
