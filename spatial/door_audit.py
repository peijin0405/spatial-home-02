"""Validate source-evidence door bindings before geometry generation.

Pure Python: no vision/Blender dependency. Legacy openings without evidence
remain review-required drafts. Contradictory evidence always blocks generation.
"""
import hashlib
import json
import math
from pathlib import Path

class DoorBindingError(ValueError):
    def __init__(self, report):
        self.report = report
        super().__init__('Door audit blocked: ' + '; '.join(
            f"{e['opening_id']}: {e['code']}" for e in report['errors']))

def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError('Expected a 2D point')
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in value):
        raise ValueError('Expected finite coordinates')
    return value

def _matrix(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(len(r) != 3 for r in value):
        raise ValueError('Expected a 2x3 affine calibration')
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for row in value for v in row):
        raise ValueError('Non-finite calibration')
    if abs(value[0][0]*value[1][1]-value[0][1]*value[1][0]) < 1e-12:
        raise ValueError('Singular calibration')
    return value

def evidence_segment(evidence, calibration):
    matrix = _matrix(calibration)
    def world(key):
        x, y = _point(evidence[key])
        return [row[0]*x + row[1]*y + row[2] for row in matrix]
    # Deliberately never use the open leaf direction to select a wall.
    return world('hinge_px'), world('closed_tip_px')

def wall_fit(start, end, wall, distance_tolerance=.15, angle_tolerance=8):
    a, b = _point(wall['a']), _point(wall['b'])
    length = math.dist(a, b)
    width = math.dist(start, end)
    if length < 1e-8 or width < 1e-8:
        raise ValueError('Degenerate wall or opening')
    axis = [(b[i]-a[i])/length for i in range(2)]
    direction = [(end[i]-start[i])/width for i in range(2)]
    angle = math.degrees(math.acos(min(1., abs(sum(axis[i]*direction[i] for i in range(2))))))
    offsets = [sum((p[i]-a[i])*axis[i] for i in range(2)) for p in (start, end)]
    distances = [abs((p[0]-a[0])*axis[1]-(p[1]-a[1])*axis[0]) for p in (start, end)]
    return {'matches': angle <= angle_tolerance and max(distances) <= distance_tolerance
            and min(offsets) >= -1e-4 and max(offsets) <= length+1e-4,
            'angle_degrees': angle, 'distance_m': max(distances),
            'offset': min(offsets), 'width': abs(offsets[1]-offsets[0]),
            'within_wall': min(offsets) >= -1e-4 and max(offsets) <= length+1e-4}

def audit_door_bindings(model):
    report = {'schema_version': 1, 'model_revision': model.get('revision'),
              'errors': [], 'warnings': [], 'bindings': []}
    def issue(level, ident, code, **details):
        report[level].append(dict(opening_id=ident, code=code, **details))
    walls = {w['id']: w for w in model['walls']}
    openings = {h['id']: h for h in model['openings']}
    matrix = model.get('calibration', {}).get('pixel_to_world')
    for h in model['openings']:
        if h.get('type') != 'door':
            continue
        ident = h['id']
        if h['wall_id'] not in walls:
            issue('errors', ident, 'missing_bound_wall')
            continue
        evidence = h.get('source_evidence')
        if not evidence:
            issue('warnings', ident, 'missing_source_evidence')
            continue
        try:
            if evidence.get('source_image') != model.get('source'):
                issue('errors', ident, 'source_image_mismatch')
            start, end = evidence_segment(evidence, matrix)
            _point(evidence['leaf_tip_px'])
            radius = math.dist(evidence['hinge_px'], evidence['closed_tip_px'])
            leaf_radius = math.dist(evidence['hinge_px'], evidence['leaf_tip_px'])
            if radius < 1 or abs(radius-leaf_radius) > max(3, radius*.15):
                issue('errors', ident, 'inconsistent_symbol_radius')
            if evidence.get('review_status') != 'confirmed':
                issue('errors', ident, 'unconfirmed_source_evidence')
            fits = {wid: wall_fit(start, end, w) for wid, w in walls.items()}
            matches = [wid for wid, fit in fits.items() if fit['matches']]
            bound = fits[h['wall_id']]
            if bound['angle_degrees'] > 8:
                issue('errors', ident, 'direction_mismatch', angle_degrees=bound['angle_degrees'])
            if not bound['matches']:
                issue('errors', ident, 'endpoints_outside_bound_wall')
            if not matches:
                issue('errors', ident, 'unmatched_wall')
            elif len(matches) > 1:
                issue('errors', ident, 'ambiguous_wall', wall_ids=matches)
            if abs(h['offset']-bound['offset']) > .10:
                issue('errors', ident, 'offset_mismatch')
            if abs(h['width']-bound['width']) > .10:
                issue('errors', ident, 'width_mismatch')
            report['bindings'].append(dict(opening_id=ident, wall_id=h['wall_id'],
                candidate_wall_ids=matches, evidence_world=[start, end], **bound))
        except (KeyError, ValueError, TypeError, IndexError, OverflowError) as error:
            issue('errors', ident, 'invalid_evidence_or_geometry', reason=str(error))
    # Detection proposals must be reconciled explicitly; missing detections never delete doors.
    for candidate in model.get('door_candidates', []):
        ident = candidate.get('id', 'unknown_candidate')
        decision = candidate.get('review', {})
        if decision.get('status') == 'rejected' and decision.get('reason'):
            continue
        if decision.get('status') != 'accepted':
            issue('errors', ident, 'unresolved_detection')
            continue
        opening = openings.get(decision.get('opening_id'))
        if not opening or opening.get('type') != 'door':
            issue('errors', ident, 'detected_door_not_modeled')
            continue
        evidence = opening.get('source_evidence', {})
        try:
            if any(math.dist(_point(candidate[k]), _point(evidence[k])) > 3
                   for k in ('hinge_px', 'closed_tip_px', 'leaf_tip_px')):
                issue('errors', ident, 'detection_model_conflict')
        except (ValueError, TypeError, KeyError):
            issue('errors', ident, 'missing_detection_evidence')
    report['status'] = 'blocked' if report['errors'] else ('requires_review' if report['warnings'] else 'validated')
    structural = {k: model.get(k) for k in ('source','calibration','walls','openings','door_candidates')}
    report['structure_sha256'] = hashlib.sha256(json.dumps(structural, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return report

def enforce_door_bindings(model):
    report = audit_door_bindings(model)
    if report['errors']:
        raise DoorBindingError(report)
    return report

def write_audit_report(model, directory):
    report = audit_door_bindings(model)
    Path(directory, 'door-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    if report['errors']:
        raise DoorBindingError(report)
    return report
