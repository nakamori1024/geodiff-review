(() => {
  const data = JSON.parse(document.getElementById('geodiff-data').textContent);
  if (!data.map) return;
  const { basemap, before, after } = data.map;

  const map = new maplibregl.Map({
    container: 'map',
    style: basemap,
    center: [0, 0],
    zoom: 1,
  });

  map.on('load', () => {
    map.addSource('before', { type: 'geojson', data: before });
    map.addSource('after',  { type: 'geojson', data: after  });

    map.addLayer({
      id: 'before-line', type: 'line', source: 'before',
      paint: { 'line-color': '#cf222e', 'line-width': 8, 'line-opacity': 0.5 }
    });
    map.addLayer({
      id: 'after-line', type: 'line', source: 'after',
      paint: { 'line-color': '#20dd5b', 'line-width': 4 }
    });

    const bounds = new maplibregl.LngLatBounds();
    for (const fc of [before, after])
      for (const f of fc.features)
        for (const part of f.geometry.coordinates)
          for (const c of part) bounds.extend(c);
    if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 40 });
  });
})();
