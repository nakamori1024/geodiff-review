# Test Data

Derived from "Sapporo Authorized Road Network Map" (札幌市認定路線網図) published by Sapporo City.

- Source: https://ckan.pf-sapporo.jp/dataset/sapporo_authorized_road
- License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)

## Processing

- Extracted Chuo Ward (ward code 10) from Nov 2023 and Sep 2025 snapshots
- Renamed columns to English. Some columns had different Japanese names
  between the 2023 and 2025 editions, so they were unified under a single name.

  | 2023 edition | 2025 edition | Renamed to |
  |---|---|---|
  | 道路区分 | 路線区分 | `road_class` |
  | 区コード | 区コード | `ward_code` |
  | 路線番号 | 路線番号 | `route_no` |
  | 路線名 | 路線名 | `route_name` |
  | 幅員最小 | 幅員最小 | `width_min` |
  | 幅員最大 | 幅員最大 | `width_max` |
  | 共用区分 | 供用区分 | `service_status` |

- Assigned integer primary key `id` from `route_no`
- Reprojected from EPSG:2454 to EPSG:4326
- **Removed 1 feature (`route_no` = 09203, Nakajimabashi Hodosen) from the 2025 edition**
  for testing the deletion case. No such deletion exists in the original data for this period.

## Contents

| | |
|---|---|
| 2023 edition | 826 features |
| 2025 edition | 829 features |

Diff (`changes_count` = 39)

| Type | Count | Origin |
|---|---|---|
| Insert | 4 | Real data |
| Delete | 1 | **Artificial modification** |
| Attribute-only change | 1 | Real data (id=511 `width_max` 18.45 → 18.02) |
| Geometry-only change | 33 | Real data |
| Unchanged | 791 | |
